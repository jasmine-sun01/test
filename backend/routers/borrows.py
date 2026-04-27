"""借用路由: /api/borrows"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import ApiResponse, PaginatedData
from schemas.borrow import BorrowCreate, BorrowReturn, BorrowOut
from services import borrow_service
from utils.deps import get_current_user, require_admin
from models.user import User
from models.item import Item

router = APIRouter(prefix="/api/borrows", tags=["借用管理"])


def _borrow_to_out(record, db: Session) -> dict:
    """BorrowRecord ORM → 输出 dict"""
    d = BorrowOut.model_validate(record).model_dump()
    item = db.query(Item).filter_by(id=record.item_id).first()
    user = db.query(User).filter_by(id=record.user_id).first()
    d["item_name"] = item.name if item else ""
    d["item_code"] = item.code if item else ""
    d["user_name"] = user.real_name if user else ""
    return d


@router.post("")
def create_borrow(data: BorrowCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        record = borrow_service.borrow_item(db, data, current_user)
        return ApiResponse(data=_borrow_to_out(record, db))
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.put("/{borrow_id}/return")
def return_borrow(
    borrow_id: int,
    data: BorrowReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        record = borrow_service.return_item(db, borrow_id, current_user, data.return_note)
        return ApiResponse(data=_borrow_to_out(record, db))
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.get("")
def list_borrows(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records, total = borrow_service.list_borrows(db, status, page, page_size)
    return ApiResponse(data=PaginatedData(
        items=[_borrow_to_out(r, db) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())


@router.get("/my")
def my_borrows(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records, total = borrow_service.my_borrows(db, current_user.id, status, page, page_size)
    return ApiResponse(data=PaginatedData(
        items=[_borrow_to_out(r, db) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())


@router.get("/overdue")
def overdue_list(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    records = borrow_service.list_overdue(db)
    return ApiResponse(data=[_borrow_to_out(r, db) for r in records])
