from decimal import Decimal
from enum import Enum
from uuid import uuid4
from uuid import UUID
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Column, Date, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.database import Base
# Import related models so SQLAlchemy can resolve all foreign-key targets when
# the transaction mapper is flushed in a process that imports this module first.
from app.models.categories import Category  # noqa: F401
from app.models.users import User  # noqa: F401


class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class Transaction(Base):
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    transaction_id = Column(String(100), nullable=False, unique=True, index=True)
    account_number = Column(String(50), nullable=True)
    transaction_type = Column(SQLAlchemyEnum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    balance = Column(Numeric(15, 2), nullable=True)
    description = Column(String(500), nullable=True)
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    category = relationship("Category", lazy="joined")


class TransactionBase(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=100)
    category_id: UUID | None = None
    account_number: str | None = Field(default=None, max_length=50)
    transaction_type: TransactionType
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    balance: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: UUID | None = None
    description: str | None = Field(default=None, max_length=500)


class TransactionCategoryResponse(BaseModel):
    category_id: UUID | None = None
    category_name: str | None = None

    @classmethod
    def from_category(cls, category):
        if category is None:
            return cls()
        return cls(category_id=category.id, category_name=category.name)


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: str
    category: TransactionCategoryResponse
    account_number: str | None = None
    transaction_type: TransactionType
    amount: Decimal
    balance: Decimal | None = None
    description: str | None = None
    transaction_date: date
    id: UUID
    user_id: UUID

    @model_validator(mode="before")
    @classmethod
    def serialize_category(cls, obj):
        if not isinstance(obj, dict):
            obj = {
                "transaction_id": obj.transaction_id,
                "category": TransactionCategoryResponse.from_category(obj.category),
                "account_number": obj.account_number,
                "transaction_type": obj.transaction_type,
                "amount": obj.amount,
                "balance": obj.balance,
                "description": obj.description,
                "transaction_date": obj.transaction_date,
                "id": obj.id,
                "user_id": obj.user_id,
            }
        return obj
