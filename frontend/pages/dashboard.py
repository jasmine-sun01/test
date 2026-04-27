"""仪表盘页"""
from nicegui import ui, app
from api_client import api
from components.navbar import navbar


@ui.page("/dashboard")
def dashboard_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    navbar()

    with ui.column().classes("q-pa-md w-full max-w-6xl mx-auto"):
        ui.label("仪表盘").classes("text-h5 q-mb-md")

        # 统计卡片
        try:
            result = api.get_stats()
            stats = result.get("data", {}) if result.get("code") == 0 else {}
        except Exception:
            stats = {}

        with ui.row().classes("w-full gap-4"):
            _stat_card("物品总数", stats.get("total_items", 0), "inventory_2", "blue")
            _stat_card("可用", stats.get("available_count", 0), "check_circle", "green")
            _stat_card("在借", stats.get("borrowed_count", 0), "swap_horiz", "orange")
            _stat_card("逾期", stats.get("overdue_count", 0), "warning", "red")
            _stat_card("已报废", stats.get("scrapped_count", 0), "delete", "grey")

        # 借用频次 Top 10
        with ui.row().classes("w-full gap-4 q-mt-lg"):
            with ui.card().classes("flex-1"):
                ui.label("📊 借用频次 Top 10").classes("text-h6 q-mb-sm")
                try:
                    result = api.get_top_borrowed(limit=10)
                    top_list = result.get("data", []) if result.get("code") == 0 else []
                except Exception:
                    top_list = []

                if top_list:
                    max_count = max(item["borrow_count"] for item in top_list) if top_list else 1
                    for item in top_list:
                        pct = int(item["borrow_count"] / max_count * 100)
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(item["name"]).classes("w-32 text-right")
                            ui.linear_progress(value=pct / 100, show_value=False).classes("flex-1").props("color=blue")
                            ui.label(str(item["borrow_count"])).classes("w-8")
                else:
                    ui.label("暂无借用记录").classes("text-grey")

            with ui.card().classes("flex-1"):
                ui.label("⏰ 快捷操作").classes("text-h6 q-mb-sm")
                ui.button("物品列表", icon="inventory_2", on_click=lambda: ui.navigate.to("/items")).classes("full-width q-mb-sm")
                ui.button("录入物品", icon="add_circle", on_click=lambda: ui.navigate.to("/items/create")).classes("full-width q-mb-sm")
                ui.button("我的借用", icon="person", on_click=lambda: ui.navigate.to("/my-borrows")).classes("full-width q-mb-sm")
                ui.button("报废管理", icon="delete_forever", on_click=lambda: ui.navigate.to("/scraps")).classes("full-width")


def _stat_card(title: str, value: int, icon: str, color: str):
    """统计卡片"""
    with ui.card().classes("flex-1 text-center q-pa-md"):
        ui.icon(icon, size="2em", color=color)
        ui.label(str(value)).classes(f"text-h4 text-{color}")
        ui.label(title).classes("text-grey")
