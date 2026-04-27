"""物品录入页（Admin）"""
import re
from nicegui import ui, app
from api_client import api
from components.navbar import navbar


def _normalize_date(s: str) -> str | None:
    """把各种日期格式统一为 YYYY-MM-DD"""
    s = s.strip()
    if not s:
        return None
    # 已经是 YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    # YYYYMMDD → YYYY-MM-DD
    if re.match(r"^\d{8}$", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    # YYYY/MM/DD → YYYY-MM-DD
    if re.match(r"^\d{4}/\d{2}/\d{2}$", s):
        return s.replace("/", "-")
    return s  # 原样返回，让后端校验


@ui.page("/items/create")
def item_create_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    user = app.storage.user["user"]
    if user.get("role") != "admin":
        ui.navigate.to("/items")
        return

    navbar()

    with ui.column().classes("q-pa-md w-full max-w-3xl mx-auto"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/items")).props("flat round")
            ui.label("录入物品").classes("text-h5")

        # 加载分类列表
        categories = {}
        try:
            result = api.get_categories()
            if result.get("code") == 0:
                for c in result["data"]:
                    categories[c["id"]] = c["name"]
        except Exception:
            pass

        with ui.card().classes("w-full q-mt-md q-pa-lg"):
            name = ui.input("物品名称 *", placeholder="如：投影仪").classes("full-width").props("outlined")
            category = ui.select(categories, label="分类").classes("full-width").props("outlined")
            model_input = ui.input("型号/规格", placeholder="如：EPSON CB-X06").classes("full-width").props("outlined")
            with ui.input("购入日期", placeholder="YYYY-MM-DD").classes("full-width").props("outlined") as purchase_date:
                with ui.menu().props("no-parent-event") as menu:
                    with ui.date(mask="YYYY-MM-DD").bind_value(purchase_date) as dp:
                        with ui.row().classes("justify-end"):
                            ui.button("确定", on_click=menu.close).props("flat")
                with purchase_date.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu.open).classes("cursor-pointer")
            purchase_price = ui.input("购入价格", placeholder="如：3500.00").classes("full-width").props("outlined type=number")
            location = ui.input("存放位置", placeholder="如：教学楼A栋 301室").classes("full-width").props("outlined")
            remark = ui.textarea("备注").classes("full-width").props("outlined")

            msg = ui.label("").classes("text-red q-mt-sm")

            def do_create():
                if not name.value:
                    msg.text = "请填写物品名称"
                    return

                data = {"name": name.value}
                if category.value:
                    data["category_id"] = category.value
                if model_input.value:
                    data["model"] = model_input.value
                if purchase_date.value:
                    d = _normalize_date(purchase_date.value)
                    if d:
                        data["purchase_date"] = d
                if purchase_price.value:
                    try:
                        data["purchase_price"] = float(purchase_price.value)
                    except ValueError:
                        msg.text = "购入价格格式不正确"
                        return
                if location.value:
                    data["location"] = location.value
                if remark.value:
                    data["remark"] = remark.value
                try:
                    result = api.create_item(data)
                    if result.get("code") == 0:
                        ui.notify("物品录入成功！", type="positive")
                        item_id = result["data"]["id"]
                        ui.navigate.to(f"/items/{item_id}")
                    else:
                        msg.text = result.get("msg", "录入失败")
                except Exception as e:
                    msg.text = f"请求失败: {e}"

            with ui.row().classes("full-width justify-end gap-2 q-mt-md"):
                ui.button("取消", on_click=lambda: ui.navigate.to("/items")).props("flat")
                ui.button("确认录入", icon="save", on_click=do_create).props("color=blue")
