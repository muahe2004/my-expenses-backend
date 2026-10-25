import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from oauthlib.oauth2 import OAuth2Error
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.google_credentials import GoogleCredential
from app.models.users import User, UserResponse, UserUpdate
from app.services.auth import create_access_token
from app.services.auth import get_current_user
from app.services import google_oauth
from app.services import users as users_service

router = APIRouter()
_oauth_states: dict[str, str | None] = {}
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/users/me", response_model=UserResponse)
def get_current_user_details(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return users_service.to_response(users_service.get_current_user(db, user.id))


@router.patch("/users/me", response_model=UserResponse)
def update_current_user(
    data: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return users_service.update_current_user(db, user.id, data)


@router.get("/auth/google")
def google_login():
    flow = google_oauth.create_flow()
    url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    _oauth_states[state] = flow.code_verifier
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    scope: str | None = None,
):
    if error:
        raise HTTPException(400, f"Google authorization failed: {error}")
    if not code or not state or state not in _oauth_states:
        raise HTTPException(400, "Invalid Google OAuth callback")
    verifier = _oauth_states.pop(state)
    gmail_scope = "https://www.googleapis.com/auth/gmail.readonly"
    if scope is not None and gmail_scope not in scope.split():
        raise HTTPException(400, "Gmail read access was not granted. Start Google login again and approve Gmail access.")
    flow = google_oauth.create_flow(state)
    try:
        flow.fetch_token(code=code, code_verifier=verifier)
    except OAuth2Error as exc:
        raise HTTPException(400, f"Google token exchange failed: {exc}") from exc
    except Warning as exc:
        raise HTTPException(400, "Google granted different permissions than requested. Start Google login again and approve Gmail access.") from exc

    try:
        google_profile = id_token.verify_oauth2_token(
            flow.credentials.id_token,
            Request(),
            google_oauth.CLIENT_ID,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, "Invalid Google identity token") from exc

    email = google_profile.get("email")
    google_id = google_profile.get("sub")
    if not email or not google_id:
        raise HTTPException(400, "Google account did not provide email or user id")

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if user is None:
            user = db.query(User).filter(User.email == email).first()

        if user is None:
            user = User(
                email=email,
                google_id=google_id,
                full_name=google_profile.get("name"),
            )
            db.add(user)
            db.flush()
        else:
            user.google_id = google_id
            user.full_name = google_profile.get("name") or user.full_name

        credentials = db.query(GoogleCredential).filter(GoogleCredential.user_id == user.id).first()
        if credentials is None:
            credentials = GoogleCredential(user_id=user.id)
            db.add(credentials)

        credentials.access_token = flow.credentials.token
        credentials.refresh_token = flow.credentials.refresh_token or credentials.refresh_token
        credentials.expires_at = flow.credentials.expiry
        db.commit()
        user_id = user.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    access_token = create_access_token(user_id)
    response = RedirectResponse(FRONTEND_URL)
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        max_age=60 * 60 * 24,
        path="/",
    )
    return response


@router.get("/auth/google/status")
def google_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    credential = db.query(GoogleCredential).filter(GoogleCredential.user_id == user.id).first()
    return {"connected": credential is not None}


@router.post("/auth/logout")
def logout():
    response = {"message": "Logged out successfully"}
    from fastapi.responses import JSONResponse

    result = JSONResponse(response)
    result.delete_cookie(key="auth_token", path="/")
    return result
