import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.services.auth import get_current_user
from app.services import acb_transaction as service
from app.models.acb_transaction import ACBEmailQuery

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/emails")
def list_emails(
    max_results: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not service.ACB_QUERY:
        logger.error("ACB_QUERY is not configured")
        raise RuntimeError("ACB_QUERY environment variable is required")

    query = ACBEmailQuery(
        query=service.ACB_QUERY,
        max_results=max_results,
        start_date=start_date,
        end_date=end_date,
    )
    return service.list_acb_transactions(query, db, str(user.id))


# raw data to debug
@router.get("/emails/raw")
def list_raw_emails(
    max_results: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not service.ACB_QUERY:
        logger.error("ACB_QUERY is not configured")
        raise RuntimeError("ACB_QUERY environment variable is required")

    query = ACBEmailQuery(
        query=service.ACB_QUERY,
        max_results=max_results,
        start_date=start_date,
        end_date=end_date,
    )
    return service.list_raw_emails(query, db, str(user.id))
