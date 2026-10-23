from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.categories import Category
from app.models.statistics import CategoryStatistics, StatisticsData, StatisticsResponse
from app.models.transactions import Transaction, TransactionResponse, TransactionType


def get_statistics(db: Session, user_id: UUID, start_date: date, end_date: date) -> StatisticsResponse:
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    categories = db.query(Category).order_by(Category.name.asc(), Category.id.asc()).all()
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .all()
    )

    grouped: dict[UUID | None, list[TransactionResponse]] = {category.id: [] for category in categories}
    grouped[None] = []
    total_expense = Decimal("0.00")
    total_income = Decimal("0.00")
    for transaction in transactions:
        if transaction.transaction_type == TransactionType.DEBIT:
            total_expense += transaction.amount
        elif transaction.transaction_type == TransactionType.CREDIT:
            total_income += transaction.amount
        if transaction.category_id in grouped:
            response = TransactionResponse.model_validate(transaction)
            if transaction.category_id is None:
                response.category.category_name = "Unknown"
            grouped[transaction.category_id].append(response)

    category_statistics = [
        CategoryStatistics(
            category_id=category.id,
            name=category.name,
            type=category.type,
            status=category.status,
            count=len(grouped[category.id]) or None,
            transactions=grouped[category.id] or None,
        )
        for category in categories
    ]
    if grouped[None]:
        category_statistics.append(
            CategoryStatistics(
                category_id=None,
                name="Unknown",
                type=None,
                status=None,
                count=len(grouped[None]),
                transactions=grouped[None],
            )
        )
    return StatisticsResponse(
        data=StatisticsData(
            start_date=start_date,
            end_date=end_date,
            total_expense=total_expense,
            total_income=total_income,
            categories=category_statistics,
        )
    )
