"""仪表盘 & 报表业务逻辑"""
import csv
import io
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.item import Item
from models.borrow import BorrowRecord
from models.user import User


def get_stats(db: Session) -> dict:
    """统计概览"""
    total = db.query(Item).count()
    available = db.query(Item).filter_by(status="available").count()
    borrowed = db.query(Item).filter_by(status="borrowed").count()
    scrapped = db.query(Item).filter_by(status="scrapped").count()

    overdue = (
        db.query(BorrowRecord)
        .filter(
            BorrowRecord.status.in_(["active", "overdue"]),
            BorrowRecord.due_date < date.today(),
        )
        .count()
    )

    return {
        "total_items": total,
        "available_count": available,
        "borrowed_count": borrowed,
        "overdue_count": overdue,
        "scrapped_count": scrapped,
    }


def get_top_borrowed(db: Session, limit: int = 10) -> list:
    """借用频次 Top N"""
    results = (
        db.query(
            BorrowRecord.item_id,
            Item.name,
            Item.code,
            func.count(BorrowRecord.id).label("borrow_count"),
        )
        .join(Item, BorrowRecord.item_id == Item.id)
        .group_by(BorrowRecord.item_id)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "item_id": r.item_id,
            "name": r.name,
            "code": r.code,
            "borrow_count": r.borrow_count,
        }
        for r in results
    ]


def export_borrow_report(db: Session, start_date: date | None = None, end_date: date | None = None) -> str:
    """导出借用报表 CSV，返回 CSV 字符串"""
    q = db.query(BorrowRecord).join(Item, BorrowRecord.item_id == Item.id).join(User, BorrowRecord.user_id == User.id)

    if start_date:
        q = q.filter(BorrowRecord.borrow_date >= start_date)
    if end_date:
        q = q.filter(BorrowRecord.borrow_date <= end_date)

    records = q.order_by(BorrowRecord.borrow_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["借用ID", "物品编号", "物品名称", "借用人", "借出日期", "应还日期", "实际归还", "状态", "用途"])

    for r in records:
        item = db.query(Item).filter_by(id=r.item_id).first()
        user = db.query(User).filter_by(id=r.user_id).first()
        writer.writerow([
            r.id,
            item.code if item else "",
            item.name if item else "",
            user.real_name if user else "",
            r.borrow_date.strftime("%Y-%m-%d") if r.borrow_date else "",
            str(r.due_date) if r.due_date else "",
            r.return_date.strftime("%Y-%m-%d") if r.return_date else "未归还",
            r.status,
            r.purpose or "",
        ])

    return output.getvalue()
