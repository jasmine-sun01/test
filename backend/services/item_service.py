"""物品业务逻辑"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.item import Item
from models.category import Category
from schemas.item import ItemCreate, ItemUpdate


def generate_item_code(db: Session) -> str:
    """生成物品编号: ITM-YYYYMMDD-XXXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"ITM-{today}-"

    # 查询当天最大编号
    last = (
        db.query(Item.code)
        .filter(Item.code.like(f"{prefix}%"))
        .order_by(Item.code.desc())
        .first()
    )

    if last:
        seq = int(last[0].split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def create_item(db: Session, data: ItemCreate) -> Item:
    """录入物品"""
    # 校验分类存在
    if data.category_id:
        cat = db.query(Category).filter_by(id=data.category_id).first()
        if not cat:
            raise ValueError("分类不存在")

    code = generate_item_code(db)
    item = Item(
        code=code,
        name=data.name,
        category_id=data.category_id,
        model=data.model,
        status="available",
        purchase_date=data.purchase_date,
        purchase_price=data.purchase_price,
        location=data.location,
        remark=data.remark,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: int) -> Item | None:
    """获取单个物品"""
    return db.query(Item).filter_by(id=item_id).first()


def list_items(
    db: Session,
    keyword: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """分页查询物品列表"""
    q = db.query(Item)

    if keyword:
        q = q.filter(
            (Item.name.contains(keyword)) | (Item.code.contains(keyword))
        )
    if category_id:
        q = q.filter(Item.category_id == category_id)
    if status:
        q = q.filter(Item.status == status)

    total = q.count()
    items = (
        q.order_by(Item.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_item(db: Session, item_id: int, data: ItemUpdate) -> Item:
    """更新物品"""
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        raise ValueError("物品不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int):
    """删除物品"""
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        raise ValueError("物品不存在")
    if item.status == "borrowed":
        raise ValueError("物品正在借出中，不能删除")

    db.delete(item)
    db.commit()


def get_category_name(db: Session, category_id: int | None) -> str | None:
    """获取分类名称"""
    if not category_id:
        return None
    cat = db.query(Category).filter_by(id=category_id).first()
    return cat.name if cat else None


def list_categories(db: Session):
    """获取所有分类"""
    return db.query(Category).all()
