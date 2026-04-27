"""通用响应模型"""
from typing import Any
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应格式"""
    code: int = 0
    data: Any = None
    msg: str = "ok"


class PaginatedData(BaseModel):
    """分页数据"""
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20
