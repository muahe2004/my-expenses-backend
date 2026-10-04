from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.acb_transaction import router as acb_transaction_router
from app.api.routes.google_oauth import router as google_oauth_router
from app.database import engine

app = FastAPI()
app.include_router(acb_transaction_router)
app.include_router(google_oauth_router)


@app.get("/")
def root():
    return {"message": "Hello FastAPI"}


@app.get("/health/db")
def database_health():
    """Verify that the API can reach PostgreSQL."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}
