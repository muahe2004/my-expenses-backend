from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
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


class UserResponse(BaseModel):
    id: UUID
    full_name: str | None
    email: str
    google_id: str | None
    phone_number: str | None
    address: str | None
    bank_name: str | None
    balance: Decimal | None
    currency: str | None
    status: UserStatus | None
    created_at: datetime | None
    updated_at: datetime | None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=150)
    phone_number: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    bank_name: str | None = Field(default=None, max_length=100)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
