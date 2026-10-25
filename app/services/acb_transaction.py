import base64
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import HTTPException
from googleapiclient.discovery import build

from app.constants.acb_patterns import (
    ACCOUNT,
    BALANCE,
    DESCRIPTION,
    LATEST_TRANSACTION,
    TRANSACTION_DATE,
)
from app.models.acb_transaction import (
    ACBEmailData,
    ACBEmailQuery,
    ACBRawEmailResponse,
    ACBTransaction,
    ACBTransactionResponse,
)
from app.models.transactions import Transaction, TransactionType
from app.models.users import User
from app.models.gmail import (
    GmailMessageGetParams,
    GmailMessageListParams,
    GmailMessageListResponse,
)
from app.services.google_oauth import get_credentials


load_dotenv()

MIN_MAX_RESULTS = 1
MAX_MAX_RESULTS = 100
ACB_QUERY = os.getenv("ACB_QUERY")


def _extract(pattern: re.Pattern[str], text: str, group: str = "value") -> str | None:
    match = pattern.search(text)
    return match.group(group).strip() if match else None


def _list_raw_messages(query: ACBEmailQuery, db, user_id: str) -> list[dict[str, Any]]:
    max_results = query.max_results
    if max_results is not None and not MIN_MAX_RESULTS <= max_results <= MAX_MAX_RESULTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"max_results must be between {MIN_MAX_RESULTS} "
                f"and {MAX_MAX_RESULTS}"
            ),
        )

    service = build("gmail", "v1", credentials=get_credentials(db, user_id))
    messages = []
    page_token = None

    if query.start_date and query.end_date and query.start_date > query.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    filters = [query.query]
    if query.start_date:
        filters.append(f"after:{query.start_date:%Y/%m/%d}")
    if query.end_date:
        exclusive_end = query.end_date + timedelta(days=1)
        filters.append(f"before:{exclusive_end:%Y/%m/%d}")
    gmail_query = " ".join(filters)

    while True:
        page_size = min(max_results - len(messages), 500) if max_results else 500
        list_params = GmailMessageListParams(
            user_id=query.user_id,
            max_results=page_size,
            query=gmail_query,
            page_token=page_token,
        )
        raw_response = service.users().messages().list(
            **list_params.as_params()
        ).execute()
        response = GmailMessageListResponse.model_validate(raw_response)
        for item in response.messages:
            message_params = GmailMessageGetParams(message_id=item.message_id)
            message = service.users().messages().get(
                **message_params.as_params()
            ).execute()
            messages.append(message)
            if max_results and len(messages) >= max_results:
                return messages

        page_token = response.next_page_token
        if not page_token:
            break

    return messages


def list_acb_transactions(query: ACBEmailQuery, db, user_id: str) -> ACBTransactionResponse:
    transactions = []
    for message in _list_raw_messages(query, db, user_id):
        data = message.get("payload", {}).get("body", {}).get("data")
        if not data:
            continue
        padding = "=" * (-len(data) % 4)
        html = base64.urlsafe_b64decode(data + padding).decode(
            "utf-8", errors="replace"
        )
        text = " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
        transaction_match = LATEST_TRANSACTION.search(text)
        if not transaction_match:
            continue

        email_data = ACBEmailData(
            account_number=_extract(ACCOUNT, text),
            transaction_type=transaction_match.group("type").capitalize(),
            transaction_amount=transaction_match.group("amount"),
            updated_balance=_extract(BALANCE, text),
            content=_extract(DESCRIPTION, text),
            transaction_date=_extract(TRANSACTION_DATE, text),
        )
        transactions.append(
            ACBTransaction(
                transaction_id=message.get("id"),
                account_number=email_data.account_number,
                transaction_type=email_data.transaction_type,
                amount=email_data.transaction_amount,
                balance=email_data.updated_balance,
                description=email_data.content,
                transaction_date=email_data.transaction_date,
            ).model_dump(exclude_none=True)
        )
    return ACBTransactionResponse(count=len(transactions), transactions=transactions)


def list_raw_emails(query: ACBEmailQuery, db, user_id: str) -> ACBRawEmailResponse:
    messages = _list_raw_messages(query, db, user_id)
    return ACBRawEmailResponse(count=len(messages), messages=messages)


def _parse_amount(value: str) -> Decimal:
    """Convert Gmail's formatted VND amount (for example 1,234.50) to Decimal."""
    try:
        return Decimal(value.replace(",", "").replace(" ", "")).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail=f"Invalid transaction amount: {value}") from exc


def _parse_transaction_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid transaction date: {value}") from exc


def sync_acb_transactions(query: ACBEmailQuery, db, user_id: str) -> dict[str, int]:
    """Sync ACB emails and refresh the user's balance from the latest transaction."""
    parsed = list_acb_transactions(query, db, user_id)
    created = 0
    skipped = 0
    latest_balance: Decimal | None = None
    latest_balance_date = None

    for item in parsed.transactions:
        if not item.transaction_id:
            continue

        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == item.transaction_id,
                Transaction.user_id == user_id,
            )
            .first()
        )
        transaction_date = _parse_transaction_date(item.transaction_date)
        item_balance = _parse_amount(item.balance) if item.balance else None
        if item_balance is not None and (
            latest_balance_date is None
            or (transaction_date is not None and transaction_date > latest_balance_date)
        ):
            latest_balance = item_balance
            latest_balance_date = transaction_date

        if transaction is not None:
            skipped += 1
            continue

        transaction = Transaction(
            transaction_id=item.transaction_id,
            user_id=user_id,
        )
        db.add(transaction)
        created += 1

        transaction.account_number = item.account_number
        transaction.transaction_type = TransactionType(item.transaction_type.upper())
        transaction.amount = _parse_amount(item.amount)
        transaction.balance = item_balance
        transaction.description = item.description
        transaction.transaction_date = transaction_date

    if latest_balance is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if user is not None:
            user.balance = latest_balance

    db.commit()
    return {"fetched": parsed.count, "created": created, "updated": 0, "skipped": skipped}
