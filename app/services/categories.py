from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.categories import Category, CategoryCreate, CategoryStatus, CategoryUpdate
from app.models.transactions import Transaction


def _get(db: Session, category_id: UUID) -> Category:
    item = db.query(Category).filter(Category.id == category_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return item


def list_categories(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: CategoryStatus | None = None,
    name: str | None = None,
) -> tuple[int, list[Category]]:
    query = db.query(Category)
    if status is not None:
        query = query.filter(Category.status == status)
    if name is not None:
        query = query.filter(Category.name.ilike(f"%{name.strip()}%"))
    total = query.count()
    items = query.order_by(Category.name.asc(), Category.created_at.asc()).offset(skip).limit(limit).all()
    return total, items


def create_category(db: Session, data: CategoryCreate) -> Category:
    item = Category(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_category(db: Session, category_id: UUID) -> Category:
    return _get(db, category_id)


def update_category(db: Session, category_id: UUID, data: CategoryUpdate) -> Category:
    item = _get(db, category_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_category(db: Session, category_id: UUID) -> None:
    item = _get(db, category_id)
    if db.query(Transaction.id).filter(Transaction.category_id == category_id).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Category cannot be deleted while transactions reference it",
        )
    db.delete(item)
    db.commit()
