"""用户相关 Schema"""
from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str
    role: str = "student"  # admin / staff / student
    phone: str | None = None


class UserUpdate(BaseModel):
    real_name: str | None = None
    role: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    role: str
    phone: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
