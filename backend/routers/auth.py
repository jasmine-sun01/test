"""认证路由: /api/auth"""
from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

from database import get_db
from schemas.user import LoginRequest, UserOut
from schemas.common import ApiResponse
from services.user_service import authenticate
from utils.auth import create_session, destroy_session
from utils.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, data.username, data.password)
    if not user:
        return ApiResponse(code=40101, msg="用户名或密码错误")

    session_id = create_session(user.id, user.username, user.role, user.real_name)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24小时
    )
    return ApiResponse(data=UserOut.model_validate(user).model_dump())


@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        destroy_session(session_id)
    response.delete_cookie("session_id")
    return ApiResponse(msg="已退出登录")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data=UserOut.model_validate(current_user).model_dump())
