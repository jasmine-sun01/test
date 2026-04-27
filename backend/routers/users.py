"""用户管理路由: /api/users"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import ApiResponse, PaginatedData
from schemas.user import UserCreate, UserUpdate, UserOut
from services import user_service
from utils.deps import require_admin
from models.user import User

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users, total = user_service.list_users(db, page, page_size)
    return ApiResponse(data=PaginatedData(
        items=[UserOut.model_validate(u).model_dump() for u in users],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())


@router.post("")
def create_user(data: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        user = user_service.create_user(db, data)
        return ApiResponse(data=UserOut.model_validate(user).model_dump())
    except ValueError as e:
        return ApiResponse(code=40002, msg=str(e))


@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        user = user_service.update_user(db, user_id, data)
        return ApiResponse(data=UserOut.model_validate(user).model_dump())
    except ValueError as e:
        return ApiResponse(code=40001, msg=str(e))


@router.put("/{user_id}/disable")
def disable_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        user = user_service.disable_user(db, user_id)
        return ApiResponse(data=UserOut.model_validate(user).model_dump())
    except ValueError as e:
        return ApiResponse(code=40001, msg=str(e))
