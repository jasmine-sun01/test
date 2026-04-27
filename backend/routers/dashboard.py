"""仪表盘 & 报表路由: /api/dashboard"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import ApiResponse
from services import dashboard_service
from utils.deps import get_current_user, require_admin
from models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = dashboard_service.get_stats(db)
    return ApiResponse(data=data)


@router.get("/top-borrowed")
def top_borrowed(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = dashboard_service.get_top_borrowed(db, limit)
    return ApiResponse(data=data)


@router.get("/reports/export")
def export_report(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    csv_content = dashboard_service.export_borrow_report(db, start_date, end_date)
    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=borrow_report.csv"},
    )
