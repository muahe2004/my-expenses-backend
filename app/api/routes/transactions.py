from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.statistics import StatisticsResponse
from app.models.transactions import TransactionCreate, TransactionResponse, TransactionType, TransactionUpdate
from app.models.users import User
from app.services import transactions as service
from app.services import statistics as statistics_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), transaction_type: TransactionType | None = None, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_transactions(db, user.id, skip, limit, transaction_type, start_date, end_date)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.create_transaction(db, data, user.id)


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return statistics_service.get_statistics(db, user.id, start_date, end_date)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_transaction(db, transaction_id, user.id)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: UUID, data: TransactionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update_transaction(db, transaction_id, data, user.id)

