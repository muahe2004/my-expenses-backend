from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.database import Base


class CategoryStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(Base):
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    status = Column(SQLAlchemyEnum(CategoryStatus), nullable=False, default=CategoryStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
