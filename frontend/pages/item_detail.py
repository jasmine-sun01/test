"""物品详情页 — 扫码跳转目标（公开可查看，操作需登录）"""
from nicegui import ui, app
from api_client import api, _get, API_BASE
from components.navbar import navbar
from components.status_badge import item_status_badge, ITEM_STATUS


@ui.page("/items/{item_id}")
def item_detail_page(item_id: int):
    # 判断是否已登录
    logged_in = bool(app.storage.user.get("user") and app.storage.user.get("session_id"))
    user = app.storage.user.get("user") if logged_in else None

    # 已登录显示导航栏
    if logged_in:
        navbar()

    with ui.column().classes("q-pa-md w-full max-w-4xl mx-auto"):
        # 未登录提示条
        if not logged_in:
            with ui.card().classes("w-full q-mb-md bg-blue-1"):
                with ui.row().classes("items-center gap-4"):
                    ui.icon("info", color="blue").classes("text-h5")
                    ui.label("您当前未登录，仅可查看物品信息。登录后可借用/归还物品。")
                    ui.button("去登录", on_click=lambda: _go_login(item_id)).props("color=blue flat")

        try:
            # 公开接口，不需要 cookie
            import httpx
            with httpx.Client(base_url=API_BASE, timeout=30) as c:
                resp = c.get(f"/items/{item_id}")
                result = resp.json()

            if result.get("code") != 0:
                ui.label(f"❌ {result.get('msg', '物品不存在')}").classes("text-h5 text-red")
                return

            item = result["data"]
        except Exception as e:
            ui.label(f"请求失败: {e}").classes("text-red")
            return

        # 标题行
        with ui.row().classes("items-center gap-4"):
            if logged_in:
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/items")).props("flat round")
            ui.label("物品详情").classes("text-h5")

        # 详情卡片
        with ui.card().classes("w-full q-mt-md q-pa-lg"):
            with ui.row().classes("w-full gap-8"):
                # 左侧信息
                with ui.column().classes("flex-1"):
                    _info_row("名称", item["name"])
                    _info_row("编号", item["code"])
                    with ui.row().classes("items-center gap-2"):
                        ui.label("状态:").classes("text-bold w-20")
                        item_status_badge(item["status"])
                    _info_row("分类", item.get("category_name") or "-")
                    _info_row("型号", item.get("model") or "-")
                    _info_row("位置", item.get("location") or "-")
                    _info_row("购入日期", item.get("purchase_date") or "-")
                    price = item.get("purchase_price")
                    _info_row("购入价格", f"¥{price}" if price else "-")
                    _info_row("备注", item.get("remark") or "-")

                # 右侧二维码
                with ui.column().classes("items-center"):
                    ui.label("二维码").classes("text-bold q-mb-sm")
                    qr_url = api.get_qrcode_url(item_id)
                    ui.image(qr_url).classes("w-40 h-40")

        # 操作按钮（仅登录用户可见）
        if logged_in:
            action_row = ui.row().classes("q-mt-md gap-2")
            with action_row:
                if item["status"] == "available":
                    ui.button("借用此物品", icon="shopping_cart", on_click=lambda: _show_borrow_dialog(item_id)).props("color=blue")

                if item["status"] in ("available", "borrowed"):
                    ui.button("申请报废", icon="delete_forever", on_click=lambda: _show_scrap_dialog(item_id)).props("color=red outline")
        else:
            with ui.row().classes("q-mt-md"):
                ui.button("登录后借用", icon="login", on_click=lambda: _go_login(item_id)).props("color=blue outline")

        # 借用历史
        ui.label("📋 借用历史").classes("text-h6 q-mt-lg")
        history = item.get("borrow_history", [])
        if history:
            columns = [
                {"name": "user", "label": "借用人", "field": "user_name", "align": "left"},
                {"name": "borrow", "label": "借出日期", "field": "borrow_date", "align": "left"},
                {"name": "due", "label": "应还日期", "field": "due_date", "align": "left"},
                {"name": "return", "label": "归还日期", "field": "return_date", "align": "left"},
                {"name": "status", "label": "状态", "field": "status", "align": "center"},
            ]
            rows = []
            for h in history:
                from components.status_badge import BORROW_STATUS
                status_label = BORROW_STATUS.get(h["status"], (h["status"],))[0]
                rows.append({
                    "user_name": h.get("user_name", ""),
                    "borrow_date": h.get("borrow_date", "")[:10],
                    "due_date": h.get("due_date", ""),
                    "return_date": (h.get("return_date") or "未归还")[:10],
                    "status": status_label,
                })
            ui.table(columns=columns, rows=rows, row_key="borrow_date").classes("w-full")
        else:
            ui.label("暂无借用记录").classes("text-grey")


def _go_login(item_id: int):
    """跳转登录并记住回跳地址"""
    app.storage.user["redirect"] = f"/items/{item_id}"
    ui.navigate.to("/login")


def _info_row(label: str, value: str):
    with ui.row().classes("items-center gap-2"):
        ui.label(f"{label}:").classes("text-bold w-20")
        ui.label(str(value))


def _show_borrow_dialog(item_id: int):
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("借用物品").classes("text-h6")
        due_date = ui.input("预计归还日期", placeholder="YYYY-MM-DD").classes("full-width").props("outlined")
        purpose = ui.input("借用用途").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_borrow():
                if not due_date.value:
                    msg.text = "请填写归还日期"
                    return
                result = api.borrow_item(item_id, due_date.value, purpose.value or "")
                if result.get("code") == 0:
                    dialog.close()
                    ui.notify("借用成功！", type="positive")
                    ui.navigate.to(f"/items/{item_id}")
                else:
                    msg.text = result.get("msg", "借用失败")

            ui.button("确认借用", on_click=do_borrow).props("color=blue")
    dialog.open()


def _show_scrap_dialog(item_id: int):
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("申请报废").classes("text-h6")
        reason = ui.textarea("报废原因").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_scrap():
                if not reason.value:
                    msg.text = "请填写报废原因"
                    return
                result = api.apply_scrap(item_id, reason.value)
                if result.get("code") == 0:
                    dialog.close()
                    ui.notify("报废申请已提交", type="positive")
                    ui.navigate.to(f"/items/{item_id}")
                else:
                    msg.text = result.get("msg", "申请失败")

            ui.button("确认申请", on_click=do_scrap).props("color=red")
    dialog.open()
