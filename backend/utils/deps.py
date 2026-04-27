"""FastAPI 依赖注入"""
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from utils.auth import get_session
from models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """从 Cookie 中读取 session_id，获取当前登录用户"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="未登录")

    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session 已过期，请重新登录")

    user = db.query(User).filter_by(id=session_data["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")
    return current_user
