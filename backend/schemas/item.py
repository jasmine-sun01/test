"""物品相关 Schema"""
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    category_id: int | None = None
    model: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    location: str | None = None
    remark: str | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    model: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    location: str | None = None
    remark: str | None = None


class ItemOut(BaseModel):
    id: int
    code: str
    name: str
    category_id: int | None = None
    category_name: str | None = None
    model: str | None = None
    status: str
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    location: str | None = None
    qrcode_path: str | None = None
    remark: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class QrcodePdfRequest(BaseModel):
    item_ids: list[int]
