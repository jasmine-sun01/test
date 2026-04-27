"""借用相关 Schema"""
from datetime import datetime, date
from pydantic import BaseModel


class BorrowCreate(BaseModel):
    item_id: int
    due_date: date
    purpose: str | None = None


class BorrowReturn(BaseModel):
    return_note: str | None = None


class BorrowOut(BaseModel):
    id: int
    item_id: int
    item_name: str | None = None
    item_code: str | None = None
    user_id: int
    user_name: str | None = None
    borrow_date: datetime
    due_date: date
    return_date: datetime | None = None
    status: str
    purpose: str | None = None
    return_note: str | None = None

    model_config = {"from_attributes": True}
