from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.database import Base


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name = Column(String(150), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    phone_number = Column(String(30), nullable=True)
    address = Column(String(255), nullable=True)
    bank_name = Column(String(100), nullable=True)
    balance = Column(Numeric(15, 2), nullable=True, default=Decimal("0.00"))
    currency = Column(String(3), nullable=True, default="VND")
    status = Column(SQLAlchemyEnum(UserStatus), nullable=True, default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now())
