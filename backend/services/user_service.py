"""用户业务逻辑"""
from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate, UserUpdate
from utils.auth import hash_password, verify_password


def authenticate(db: Session, username: str, password: str) -> User | None:
    """验证用户名密码，成功返回 User，失败返回 None"""
    user = db.query(User).filter_by(username=username).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, data: UserCreate) -> User:
    """创建用户"""
    existing = db.query(User).filter_by(username=data.username).first()
    if existing:
        raise ValueError(f"用户名 '{data.username}' 已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        role=data.role,
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    """更新用户信息"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ValueError("用户不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, page: int = 1, page_size: int = 20):
    """分页查询用户列表"""
    total = db.query(User).count()
    users = (
        db.query(User)
        .order_by(User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return users, total


def disable_user(db: Session, user_id: int) -> User:
    """禁用用户"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
