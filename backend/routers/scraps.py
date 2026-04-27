"""报废路由: /api/scraps"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import ApiResponse, PaginatedData
from schemas.scrap import ScrapCreate, ScrapApprove, ScrapOut
from services import scrap_service
from utils.deps import get_current_user, require_admin
from models.user import User
from models.item import Item

router = APIRouter(prefix="/api/scraps", tags=["报废管理"])


def _scrap_to_out(record, db: Session) -> dict:
    """ScrapRecord ORM → 输出 dict"""
    d = ScrapOut.model_validate(record).model_dump()
    item = db.query(Item).filter_by(id=record.item_id).first()
    applicant = db.query(User).filter_by(id=record.applicant_id).first()
    d["item_name"] = item.name if item else ""
    d["item_code"] = item.code if item else ""
    d["applicant_name"] = applicant.real_name if applicant else ""
    if record.approver_id:
        approver = db.query(User).filter_by(id=record.approver_id).first()
        d["approver_name"] = approver.real_name if approver else ""
    return d


@router.post("")
def create_scrap(data: ScrapCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        record = scrap_service.apply_scrap(db, data.item_id, data.reason, current_user)
        return ApiResponse(data=_scrap_to_out(record, db))
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.put("/{scrap_id}/approve")
def approve_scrap(
    scrap_id: int,
    data: ScrapApprove,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        record = scrap_service.approve_scrap(db, scrap_id, admin, data.approve_note)
        return ApiResponse(data=_scrap_to_out(record, db))
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.put("/{scrap_id}/reject")
def reject_scrap(
    scrap_id: int,
    data: ScrapApprove,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        record = scrap_service.reject_scrap(db, scrap_id, admin, data.approve_note)
        return ApiResponse(data=_scrap_to_out(record, db))
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.get("")
def list_scraps(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records, total = scrap_service.list_scraps(db, status, page, page_size)
    return ApiResponse(data=PaginatedData(
        items=[_scrap_to_out(r, db) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())
