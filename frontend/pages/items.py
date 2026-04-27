"""物品列表页"""
from nicegui import ui, app
from api_client import api
from components.navbar import navbar
from components.status_badge import ITEM_STATUS


@ui.page("/items")
def items_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    navbar()
    user = app.storage.user["user"]
    is_admin = user.get("role") == "admin"

    with ui.column().classes("q-pa-md w-full max-w-6xl mx-auto"):
        # 标题 + 操作按钮
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("物品管理").classes("text-h5")
            if is_admin:
                ui.button("录入物品", icon="add", on_click=lambda: ui.navigate.to("/items/create")).props("color=blue")

        # 搜索栏
        with ui.row().classes("w-full gap-2 q-mt-md"):
            keyword_input = ui.input("搜索关键词", placeholder="名称或编号").classes("flex-1").props("outlined dense")
            status_select = ui.select(
                {"": "全部状态", "available": "可用", "borrowed": "已借出", "pending_scrap": "待报废", "scrapped": "已报废"},
                value="",
            ).classes("w-40").props("outlined dense")
            search_btn = ui.button("搜索", icon="search").props("color=blue")

        # 表格容器
        table_container = ui.column().classes("w-full q-mt-md")

        def load_items(page=1):
            table_container.clear()
            params = {"page": page, "page_size": 20}
            if keyword_input.value:
                params["keyword"] = keyword_input.value
            if status_select.value:
                params["status"] = status_select.value

            try:
                result = api.list_items(**params)
                if result.get("code") != 0:
                    with table_container:
                        ui.label(f"加载失败: {result.get('msg')}").classes("text-red")
                    return

                data = result["data"]
                items = data.get("items", [])
                total = data.get("total", 0)

                with table_container:
                    if not items:
                        ui.label("暂无物品").classes("text-grey text-center q-pa-lg")
                        return

                    # 表格
                    columns = [
                        {"name": "code", "label": "编号", "field": "code", "align": "left"},
                        {"name": "name", "label": "名称", "field": "name", "align": "left"},
                        {"name": "category", "label": "分类", "field": "category_name", "align": "left"},
                        {"name": "status", "label": "状态", "field": "status", "align": "center"},
                        {"name": "location", "label": "位置", "field": "location", "align": "left"},
                        {"name": "action", "label": "操作", "field": "action", "align": "center"},
                    ]
                    rows = []
                    for item in items:
                        status_label = ITEM_STATUS.get(item["status"], (item["status"],))[0]
                        rows.append({
                            "id": item["id"],
                            "code": item["code"],
                            "name": item["name"],
                            "category_name": item.get("category_name") or "-",
                            "status": status_label,
                            "location": item.get("location") or "-",
                        })

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                    table.add_slot("body-cell-action", '''
                        <q-td :props="props">
                            <q-btn flat dense color="blue" icon="visibility" @click="$parent.$emit('view', props.row)" />
                        </q-td>
                    ''')
                    table.on("view", lambda e: ui.navigate.to(f"/items/{e.args['id']}"))

                    # 分页
                    total_pages = (total + 19) // 20
                    if total_pages > 1:
                        with ui.row().classes("w-full justify-center q-mt-md"):
                            for p in range(1, total_pages + 1):
                                btn = ui.button(str(p), on_click=lambda _, pg=p: load_items(pg))
                                if p == page:
                                    btn.props("color=blue")
                                else:
                                    btn.props("flat")

            except Exception as e:
                with table_container:
                    ui.label(f"请求失败: {e}").classes("text-red")

        search_btn.on_click(lambda: load_items())
        load_items()
