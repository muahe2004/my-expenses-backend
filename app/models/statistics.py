from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.categories import CategoryStatus, CategoryType
from app.models.transactions import TransactionResponse


class CategoryStatistics(BaseModel):
    category_id: UUID | None
    name: str
    type: CategoryType | None
    status: CategoryStatus | None
    count: int | None
    transactions: list[TransactionResponse] | None


class StatisticsData(BaseModel):
    start_date: date
    end_date: date
    total_expense: Decimal
    total_income: Decimal
    categories: list[CategoryStatistics]


class StatisticsResponse(BaseModel):
    data: StatisticsData
