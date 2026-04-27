"""报废业务逻辑"""
from datetime import datetime
from sqlalchemy.orm import Session

from models.scrap import ScrapRecord
from models.item import Item
from models.user import User


def apply_scrap(db: Session, item_id: int, reason: str, applicant: User) -> ScrapRecord:
    """发起报废申请"""
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        raise ValueError("物品不存在")
    if item.status == "scrapped":
        raise ValueError("物品已报废")
    if item.status == "pending_scrap":
        raise ValueError("物品已有待审批的报废申请")

    # 检查是否已有 pending 的报废申请
    existing = (
        db.query(ScrapRecord)
        .filter_by(item_id=item_id, status="pending")
        .first()
    )
    if existing:
        raise ValueError("该物品已有待审批的报废申请")

    record = ScrapRecord(
        item_id=item_id,
        applicant_id=applicant.id,
        reason=reason,
        status="pending",
    )
    item.status = "pending_scrap"

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def approve_scrap(db: Session, scrap_id: int, approver: User, approve_note: str | None = None) -> ScrapRecord:
    """审批通过报废"""
    record = db.query(ScrapRecord).filter_by(id=scrap_id).first()
    if not record:
        raise ValueError("报废记录不存在")
    if record.status != "pending":
        raise ValueError("该申请不在待审批状态")

    record.status = "approved"
    record.approver_id = approver.id
    record.approve_time = datetime.now()
    record.approve_note = approve_note

    # 物品状态 → scrapped
    item = db.query(Item).filter_by(id=record.item_id).first()
    if item:
        item.status = "scrapped"

    db.commit()
    db.refresh(record)
    return record


def reject_scrap(db: Session, scrap_id: int, approver: User, approve_note: str | None = None) -> ScrapRecord:
    """审批驳回报废"""
    record = db.query(ScrapRecord).filter_by(id=scrap_id).first()
    if not record:
        raise ValueError("报废记录不存在")
    if record.status != "pending":
        raise ValueError("该申请不在待审批状态")

    record.status = "rejected"
    record.approver_id = approver.id
    record.approve_time = datetime.now()
    record.approve_note = approve_note

    # 恢复物品状态
    item = db.query(Item).filter_by(id=record.item_id).first()
    if item and item.status == "pending_scrap":
        # 检查是否有活跃借用记录来决定恢复什么状态
        from models.borrow import BorrowRecord
        active_borrow = (
            db.query(BorrowRecord)
            .filter_by(item_id=item.id, status="active")
            .first()
        )
        item.status = "borrowed" if active_borrow else "available"

    db.commit()
    db.refresh(record)
    return record


def list_scraps(
    db: Session,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """报废申请列表"""
    q = db.query(ScrapRecord)
    if status:
        q = q.filter(ScrapRecord.status == status)

    total = q.count()
    records = (
        q.order_by(ScrapRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total
