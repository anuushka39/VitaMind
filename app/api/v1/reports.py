"""Weekly nutrition report endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.report import WeeklyReportOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly/{user_id}", response_model=WeeklyReportOut)
def weekly_report(user_id: int, db: Session = Depends(get_db)):
    service = ReportService(db)
    return service.weekly_report(user_id)
