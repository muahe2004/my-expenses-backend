import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.acb_transaction import router as acb_transaction_router
from app.api.routes.google_oauth import router as google_oauth_router
from app.api.routes.transactions import router as transactions_router
from app.database import engine

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(acb_transaction_router)
app.include_router(google_oauth_router)
app.include_router(transactions_router)


@app.get("/")
def root():
    return {"message": "Hello FastAPI"}


@app.get("/health/db")
def database_health():
    """Verify that the API can reach PostgreSQL."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}
