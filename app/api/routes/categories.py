from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categories import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryStatus,
    CategoryUpdate,
)
from app.models.users import User
from app.services import categories as service
from app.services.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_status: CategoryStatus | None = Query(default=None, alias="status"),
    name: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total, items = service.list_categories(db, skip, limit, category_status, name)
    return {"total": total, "items": items}


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.create_category(db, data)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.get_category(db, category_id)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
