"""借用业务逻辑"""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from models.borrow import BorrowRecord
from models.item import Item
from models.user import User
from schemas.borrow import BorrowCreate


def borrow_item(db: Session, data: BorrowCreate, user: User) -> BorrowRecord:
    """发起借用"""
    item = db.query(Item).filter_by(id=data.item_id).first()
    if not item:
        raise ValueError("物品不存在")
    if item.status != "available":
        raise ValueError(f"物品当前状态为「{item.status}」，不可借用")

    # 检查 due_date
    if data.due_date < date.today():
        raise ValueError("归还日期不能早于今天")
    if data.due_date > date.today() + timedelta(days=90):
        raise ValueError("借期最长 90 天")

    # 检查用户未归还数量
    active_count = (
        db.query(BorrowRecord)
        .filter_by(user_id=user.id, status="active")
        .count()
    )
    if active_count >= 10:
        raise ValueError("您当前未归还物品已达上限（10件）")

    # 事务：插入借用记录 + 更新物品状态
    record = BorrowRecord(
        item_id=data.item_id,
        user_id=user.id,
        due_date=data.due_date,
        purpose=data.purpose,
        status="active",
    )
    item.status = "borrowed"

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def return_item(db: Session, borrow_id: int, user: User, return_note: str | None = None) -> BorrowRecord:
    """归还物品"""
    record = db.query(BorrowRecord).filter_by(id=borrow_id).first()
    if not record:
        raise ValueError("借用记录不存在")
    if record.status == "returned":
        raise ValueError("该借用记录已归还")

    # 权限：本人或管理员
    if record.user_id != user.id and user.role != "admin":
        raise ValueError("只能归还自己的借用记录")

    record.status = "returned"
    record.return_date = datetime.now()
    record.return_note = return_note

    # 恢复物品状态（如果物品不是待报废）
    item = db.query(Item).filter_by(id=record.item_id).first()
    if item and item.status == "borrowed":
        item.status = "available"

    db.commit()
    db.refresh(record)
    return record


def list_borrows(
    db: Session,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """所有借用记录"""
    q = db.query(BorrowRecord)
    if status:
        q = q.filter(BorrowRecord.status == status)

    total = q.count()
    records = (
        q.order_by(BorrowRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def my_borrows(
    db: Session,
    user_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """我的借用记录"""
    q = db.query(BorrowRecord).filter_by(user_id=user_id)
    if status:
        q = q.filter(BorrowRecord.status == status)

    total = q.count()
    records = (
        q.order_by(BorrowRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def list_overdue(db: Session):
    """逾期列表"""
    return (
        db.query(BorrowRecord)
        .filter(
            BorrowRecord.status.in_(["active", "overdue"]),
            BorrowRecord.due_date < date.today(),
        )
        .order_by(BorrowRecord.due_date)
        .all()
    )


def mark_overdue(db: Session):
    """定时任务：标记逾期"""
    records = (
        db.query(BorrowRecord)
        .filter(
            BorrowRecord.status == "active",
            BorrowRecord.due_date < date.today(),
        )
        .all()
    )
    for r in records:
        r.status = "overdue"
    db.commit()
    return len(records)


def get_borrow_history(db: Session, item_id: int, limit: int = 5):
    """物品的借用历史"""
    return (
        db.query(BorrowRecord)
        .filter_by(item_id=item_id)
        .order_by(BorrowRecord.id.desc())
        .limit(limit)
        .all()
    )
