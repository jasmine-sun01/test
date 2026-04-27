"""物品路由: /api/items"""
import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import ApiResponse, PaginatedData
from schemas.item import ItemCreate, ItemUpdate, ItemOut, QrcodePdfRequest
from services import item_service
from services.qrcode_service import generate_qrcode, generate_qrcode_pdf
from services.borrow_service import get_borrow_history
from utils.deps import get_current_user, require_admin
from models.user import User

router = APIRouter(prefix="/api/items", tags=["物品管理"])


def _item_to_out(item, db: Session) -> dict:
    """Item ORM → 输出 dict（含 category_name）"""
    d = ItemOut.model_validate(item).model_dump()
    d["category_name"] = item_service.get_category_name(db, item.category_id)
    return d


@router.post("")
def create_item(data: ItemCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        item = item_service.create_item(db, data)
        # 生成二维码
        qr_path = generate_qrcode(item.id, item.code)
        item.qrcode_path = qr_path
        db.commit()
        db.refresh(item)
        return ApiResponse(data=_item_to_out(item, db))
    except ValueError as e:
        return ApiResponse(code=40002, msg=str(e))


@router.get("")
def list_items(
    keyword: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = item_service.list_items(db, keyword, category_id, status, page, page_size)
    return ApiResponse(data=PaginatedData(
        items=[_item_to_out(i, db) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cats = item_service.list_categories(db)
    return ApiResponse(data=[{"id": c.id, "name": c.name, "description": c.description} for c in cats])


@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = item_service.get_item(db, item_id)
    if not item:
        return ApiResponse(code=40001, msg="物品不存在")

    data = _item_to_out(item, db)
    # 附加借用历史
    history = get_borrow_history(db, item_id, limit=5)
    from models.user import User as UserModel
    data["borrow_history"] = []
    for h in history:
        u = db.query(UserModel).filter_by(id=h.user_id).first()
        data["borrow_history"].append({
            "id": h.id,
            "user_name": u.real_name if u else "",
            "borrow_date": h.borrow_date.isoformat() if h.borrow_date else "",
            "due_date": str(h.due_date) if h.due_date else "",
            "return_date": h.return_date.isoformat() if h.return_date else None,
            "status": h.status,
        })
    return ApiResponse(data=data)


@router.put("/{item_id}")
def update_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        item = item_service.update_item(db, item_id, data)
        return ApiResponse(data=_item_to_out(item, db))
    except ValueError as e:
        return ApiResponse(code=40001, msg=str(e))


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        item_service.delete_item(db, item_id)
        return ApiResponse(msg="删除成功")
    except ValueError as e:
        return ApiResponse(code=40003, msg=str(e))


@router.get("/{item_id}/qrcode")
def get_qrcode(item_id: int, db: Session = Depends(get_db)):
    item = item_service.get_item(db, item_id)
    if not item:
        return ApiResponse(code=40001, msg="物品不存在")
    if not item.qrcode_path:
        # 按需生成
        qr_path = generate_qrcode(item.id, item.code)
        item.qrcode_path = qr_path
        db.commit()
    return FileResponse(item.qrcode_path, media_type="image/png")


@router.post("/qrcode-pdf")
def batch_qrcode_pdf(data: QrcodePdfRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    items = []
    for iid in data.item_ids:
        item = item_service.get_item(db, iid)
        if item:
            if not item.qrcode_path:
                item.qrcode_path = generate_qrcode(item.id, item.code)
                db.commit()
            items.append({"qrcode_path": item.qrcode_path, "name": item.name, "code": item.code})

    if not items:
        return ApiResponse(code=40001, msg="未找到有效物品")

    pdf_path = generate_qrcode_pdf(items)
    return FileResponse(pdf_path, media_type="application/pdf", filename="qrcodes.pdf")


@router.post("/import")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """CSV 批量导入物品"""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))

    created = 0
    errors = []
    for row_num, row in enumerate(reader, 1):
        if row_num == 1 and row[0].startswith("名称"):
            continue  # 跳过表头
        if len(row) < 1:
            continue
        try:
            # CSV: 名称,分类,型号,购入日期,价格,位置,备注
            name = row[0].strip()
            category_name = row[1].strip() if len(row) > 1 else ""
            model_val = row[2].strip() if len(row) > 2 else None
            purchase_date = row[3].strip() if len(row) > 3 else None
            price = row[4].strip() if len(row) > 4 else None
            location = row[5].strip() if len(row) > 5 else None
            remark = row[6].strip() if len(row) > 6 else None

            # 查找分类 ID
            cat_id = None
            if category_name:
                from models.category import Category
                cat = db.query(Category).filter_by(name=category_name).first()
                if cat:
                    cat_id = cat.id

            from decimal import Decimal
            from datetime import date as dt_date
            item_data = ItemCreate(
                name=name,
                category_id=cat_id,
                model=model_val or None,
                purchase_date=dt_date.fromisoformat(purchase_date) if purchase_date else None,
                purchase_price=Decimal(price) if price else None,
                location=location or None,
                remark=remark or None,
            )
            item = item_service.create_item(db, item_data)
            qr_path = generate_qrcode(item.id, item.code)
            item.qrcode_path = qr_path
            db.commit()
            created += 1
        except Exception as e:
            errors.append(f"第{row_num}行: {str(e)}")

    return ApiResponse(data={"created": created, "errors": errors})
