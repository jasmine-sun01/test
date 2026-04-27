"""报废相关 Schema"""
from datetime import datetime
from pydantic import BaseModel


class ScrapCreate(BaseModel):
    item_id: int
    reason: str


class ScrapApprove(BaseModel):
    approve_note: str | None = None


class ScrapOut(BaseModel):
    id: int
    item_id: int
    item_name: str | None = None
    item_code: str | None = None
    applicant_id: int
    applicant_name: str | None = None
    approver_id: int | None = None
    approver_name: str | None = None
    reason: str
    status: str
    apply_time: datetime
    approve_time: datetime | None = None
    approve_note: str | None = None

    model_config = {"from_attributes": True}
