import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from oauthlib.oauth2 import OAuth2Error
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.google_credentials import GoogleCredential
from app.models.users import User
from app.services.auth import create_access_token
from app.services import google_oauth

router = APIRouter()
_oauth_states: dict[str, str | None] = {}
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/auth/google")
def google_login():
    flow = google_oauth.create_flow()
    url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    _oauth_states[state] = flow.code_verifier
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(400, f"Google authorization failed: {error}")
    if not code or not state or state not in _oauth_states:
        raise HTTPException(400, "Invalid Google OAuth callback")
    verifier = _oauth_states.pop(state)
    flow = google_oauth.create_flow(state)
    try:
        flow.fetch_token(code=code, code_verifier=verifier)
    except OAuth2Error as exc:
        raise HTTPException(400, f"Google token exchange failed: {exc}") from exc

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
    return RedirectResponse(f"{FRONTEND_URL}?token={access_token}")


@router.get("/auth/google/status")
def google_status():
    return {"connected": google_oauth.is_connected()}
