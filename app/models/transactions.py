from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.database import Base


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
