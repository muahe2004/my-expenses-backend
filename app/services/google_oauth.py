import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session

from app.models.google_credentials import GoogleCredential

load_dotenv()

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
TOKEN_PATH = Path("token.json")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def create_flow(state: str | None = None) -> Flow:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(500, "Google OAuth is not configured")
    config: dict[str, Any] = {"web": {
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": GOOGLE_AUTH_URI,
        "token_uri": GOOGLE_TOKEN_URI,
    }}
    flow = Flow.from_client_config(config, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI
    return flow


def get_credentials(db: Session, user_id: str) -> Credentials:
    stored = db.query(GoogleCredential).filter(GoogleCredential.user_id == user_id).first()
    if stored is None:
        raise HTTPException(401, "Google account is not connected")
    credentials = Credentials(
        token=stored.access_token,
        refresh_token=stored.refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        stored.access_token = credentials.token
        stored.expires_at = credentials.expiry
        db.commit()
    if not credentials.valid:
        raise HTTPException(401, "Google authorization expired; connect again")
    return credentials


def save_credentials(credentials: Credentials) -> None:
    TOKEN_PATH.write_text(credentials.to_json())


def is_connected() -> bool:
    return TOKEN_PATH.exists()
