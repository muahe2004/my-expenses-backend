from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
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


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    status: CategoryStatus = CategoryStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name must not be blank")
        return value


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    status: CategoryStatus | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Category name must not be blank")
        return value


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: CategoryStatus


class CategoryListResponse(BaseModel):
    total: int
    items: list[CategoryResponse]
