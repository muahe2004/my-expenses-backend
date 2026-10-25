from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.users import User, UserResponse, UserUpdate


def get_user(db: Session, user_id: UUID) -> User | None:
    """Fetch a user by its database ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(db: Session, user_id: UUID) -> User:
    """Return the authenticated user's profile from the database."""
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        google_id=user.google_id,
        phone_number=user.phone_number,
        address=user.address,
        bank_name=user.bank_name,
        balance=user.balance,
        currency=user.currency,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def update_current_user(db: Session, user_id: UUID, data: UserUpdate) -> UserResponse:
    user = get_current_user(db, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return to_response(user)
