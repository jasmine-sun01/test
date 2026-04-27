"""借用记录表"""
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class BorrowRecord(Base):
    __tablename__ = "borrow_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    borrow_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active / returned / overdue
    purpose: Mapped[str | None] = mapped_column(String(200))
    return_note: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
