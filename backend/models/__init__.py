"""ORM 模型 — 导入所有表，确保 Base.metadata 注册完整"""
from models.user import User
from models.category import Category
from models.item import Item
from models.borrow import BorrowRecord
from models.scrap import ScrapRecord

__all__ = ["User", "Category", "Item", "BorrowRecord", "ScrapRecord"]
