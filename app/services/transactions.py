from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.categories import Category
from app.models.transactions import Transaction, TransactionCreate, TransactionUpdate


def _get(db: Session, transaction_id: UUID, user_id: UUID) -> Transaction:
    item = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return item


def _check_category(db: Session, category_id: UUID | None) -> None:
    if category_id is not None and db.query(Category).filter(Category.id == category_id).first() is None:
        raise HTTPException(status_code=400, detail="Category not found")


def list_transactions(db: Session, user_id: UUID, skip: int = 0, limit: int = 20,
                      transaction_type=None, start_date: date | None = None, end_date: date | None = None):
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if transaction_type is not None:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)
    return query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()).offset(skip).limit(limit).all()


def create_transaction(db: Session, data: TransactionCreate, user_id: UUID):
    _check_category(db, data.category_id)
    item = Transaction(user_id=user_id, **data.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Transaction ID already exists") from exc
    db.refresh(item)
    return item


def get_transaction(db: Session, transaction_id: UUID, user_id: UUID):
    return _get(db, transaction_id, user_id)


def update_transaction(db: Session, transaction_id: UUID, data: TransactionUpdate, user_id: UUID):
    item = _get(db, transaction_id, user_id)
    values = data.model_dump(exclude_unset=True)
    _check_category(db, values.get("category_id")) if "category_id" in values else None
    for field, value in values.items():
        setattr(item, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Transaction ID already exists") from exc
    db.refresh(item)
    return item
