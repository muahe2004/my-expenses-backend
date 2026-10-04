from datetime import date
from typing import Any

from pydantic import BaseModel


class ACBTransaction(BaseModel):
    transaction_id: str | None = None
    account_number: str | None = None
    transaction_type: str
    amount: str
    balance: str | None = None
    description: str | None = None
    transaction_date: str | None = None


class ACBEmailData(BaseModel):
    """Values extracted directly from an ACB notification email."""

    account_number: str | None = None
    transaction_type: str
    transaction_amount: str
    updated_balance: str | None = None
    content: str | None = None
    transaction_date: str | None = None


class ACBEmailQuery(BaseModel):
    user_id: str = "me"
    max_results: int | None = None
    query: str
    start_date: date | None = None
    end_date: date | None = None


class ACBTransactionResponse(BaseModel):
    count: int
    transactions: list[ACBTransaction]
    next_page_token: str | None = None


class ACBRawEmailResponse(BaseModel):
    count: int
    messages: list[dict[str, Any]]
    next_page_token: str | None = None
