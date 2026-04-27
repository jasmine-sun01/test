"""报废记录表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ScrapRecord(Base):
    __tablename__ = "scrap_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), nullable=False, index=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending / approved / rejected
    apply_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    approve_time: Mapped[datetime | None] = mapped_column(DateTime)
    approve_note: Mapped[str | None] = mapped_column(String(200))
