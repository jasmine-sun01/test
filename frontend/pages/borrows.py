"""借用管理页（全部借用记录）"""
from nicegui import ui, app
from api_client import api
from components.navbar import navbar
from components.status_badge import BORROW_STATUS


@ui.page("/borrows")
def borrows_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    navbar()
    user = app.storage.user["user"]
    is_admin = user.get("role") == "admin"

    with ui.column().classes("q-pa-md w-full max-w-6xl mx-auto"):
        ui.label("借用管理").classes("text-h5")

        # 筛选
        with ui.row().classes("w-full gap-2 q-mt-md"):
            status_select = ui.select(
                {"": "全部", "active": "借用中", "returned": "已归还", "overdue": "逾期"},
                value="",
            ).classes("w-40").props("outlined dense")
            search_btn = ui.button("筛选", icon="filter_list").props("color=blue")

        table_container = ui.column().classes("w-full q-mt-md")

        def load_borrows(page=1):
            table_container.clear()
            params = {"page": page, "page_size": 20}
            if status_select.value:
                params["status"] = status_select.value

            try:
                result = api.list_borrows(**params)
                if result.get("code") != 0:
                    with table_container:
                        ui.label(f"加载失败: {result.get('msg')}").classes("text-red")
                    return

                data = result["data"]
                records = data.get("items", [])
                total = data.get("total", 0)

                with table_container:
                    if not records:
                        ui.label("暂无借用记录").classes("text-grey text-center q-pa-lg")
                        return

                    columns = [
                        {"name": "item_code", "label": "物品编号", "field": "item_code", "align": "left"},
                        {"name": "item_name", "label": "物品名称", "field": "item_name", "align": "left"},
                        {"name": "user_name", "label": "借用人", "field": "user_name", "align": "left"},
                        {"name": "borrow_date", "label": "借出日期", "field": "borrow_date", "align": "left"},
                        {"name": "due_date", "label": "应还日期", "field": "due_date", "align": "left"},
                        {"name": "status", "label": "状态", "field": "status_label", "align": "center"},
                        {"name": "action", "label": "操作", "field": "action", "align": "center"},
                    ]
                    rows = []
                    for r in records:
                        status_label = BORROW_STATUS.get(r["status"], (r["status"],))[0]
                        rows.append({
                            "id": r["id"],
                            "item_id": r["item_id"],
                            "item_code": r.get("item_code", ""),
                            "item_name": r.get("item_name", ""),
                            "user_name": r.get("user_name", ""),
                            "borrow_date": r.get("borrow_date", "")[:10],
                            "due_date": str(r.get("due_date", "")),
                            "status": r["status"],
                            "status_label": status_label,
                        })

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                    # 只有 active/overdue 状态且 (本人或管理员) 才能归还
                    table.add_slot("body-cell-action", '''
                        <q-td :props="props">
                            <q-btn v-if="props.row.status === 'active' || props.row.status === 'overdue'"
                                   flat dense color="green" label="归还"
                                   @click="$parent.$emit('return_item', props.row)" />
                            <q-btn flat dense color="blue" icon="visibility"
                                   @click="$parent.$emit('view_item', props.row)" />
                        </q-td>
                    ''')
                    table.on("return_item", lambda e: _show_return_dialog(e.args["id"], load_borrows))
                    table.on("view_item", lambda e: ui.navigate.to(f"/items/{e.args['item_id']}"))

                    # 分页
                    total_pages = (total + 19) // 20
                    if total_pages > 1:
                        with ui.row().classes("w-full justify-center q-mt-md"):
                            for p in range(1, total_pages + 1):
                                btn = ui.button(str(p), on_click=lambda _, pg=p: load_borrows(pg))
                                if p == page:
                                    btn.props("color=blue")
                                else:
                                    btn.props("flat")

            except Exception as e:
                with table_container:
                    ui.label(f"请求失败: {e}").classes("text-red")

        search_btn.on_click(lambda: load_borrows())
        load_borrows()


def _show_return_dialog(borrow_id: int, reload_fn):
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("归还物品").classes("text-h6")
        return_note = ui.input("物品状况备注", placeholder="如：完好无损").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_return():
                result = api.return_item(borrow_id, return_note.value or "")
                if result.get("code") == 0:
                    dialog.close()
                    ui.notify("归还成功！", type="positive")
                    reload_fn()
                else:
                    msg.text = result.get("msg", "归还失败")

            ui.button("确认归还", on_click=do_return).props("color=green")
    dialog.open()
