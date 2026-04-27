"""报废管理页"""
from nicegui import ui, app
from api_client import api
from components.navbar import navbar
from components.status_badge import SCRAP_STATUS


@ui.page("/scraps")
def scraps_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    navbar()
    user = app.storage.user["user"]
    is_admin = user.get("role") == "admin"

    with ui.column().classes("q-pa-md w-full max-w-6xl mx-auto"):
        ui.label("报废管理").classes("text-h5")

        # 筛选
        with ui.row().classes("w-full gap-2 q-mt-md"):
            status_select = ui.select(
                {"": "全部", "pending": "待审批", "approved": "已通过", "rejected": "已驳回"},
                value="",
            ).classes("w-40").props("outlined dense")
            search_btn = ui.button("筛选", icon="filter_list").props("color=blue")

        table_container = ui.column().classes("w-full q-mt-md")

        def load_scraps(page=1):
            table_container.clear()
            params = {"page": page, "page_size": 20}
            if status_select.value:
                params["status"] = status_select.value

            try:
                result = api.list_scraps(**params)
                if result.get("code") != 0:
                    with table_container:
                        ui.label(f"加载失败: {result.get('msg')}").classes("text-red")
                    return

                data = result["data"]
                records = data.get("items", [])
                total = data.get("total", 0)

                with table_container:
                    if not records:
                        ui.label("暂无报废记录").classes("text-grey text-center q-pa-lg")
                        return

                    columns = [
                        {"name": "item_code", "label": "物品编号", "field": "item_code", "align": "left"},
                        {"name": "item_name", "label": "物品名称", "field": "item_name", "align": "left"},
                        {"name": "applicant", "label": "申请人", "field": "applicant_name", "align": "left"},
                        {"name": "reason", "label": "报废原因", "field": "reason", "align": "left"},
                        {"name": "apply_time", "label": "申请时间", "field": "apply_time", "align": "left"},
                        {"name": "status", "label": "状态", "field": "status_label", "align": "center"},
                    ]

                    if is_admin:
                        columns.append({"name": "action", "label": "操作", "field": "action", "align": "center"})

                    rows = []
                    for r in records:
                        status_label = SCRAP_STATUS.get(r["status"], (r["status"],))[0]
                        rows.append({
                            "id": r["id"],
                            "item_code": r.get("item_code", ""),
                            "item_name": r.get("item_name", ""),
                            "applicant_name": r.get("applicant_name", ""),
                            "reason": r.get("reason", "")[:30],
                            "apply_time": r.get("apply_time", "")[:16],
                            "status": r["status"],
                            "status_label": status_label,
                        })

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                    if is_admin:
                        table.add_slot("body-cell-action", '''
                            <q-td :props="props">
                                <q-btn v-if="props.row.status === 'pending'"
                                       flat dense color="green" label="通过"
                                       @click="$parent.$emit('approve', props.row)" class="q-mr-xs" />
                                <q-btn v-if="props.row.status === 'pending'"
                                       flat dense color="red" label="驳回"
                                       @click="$parent.$emit('reject', props.row)" />
                            </q-td>
                        ''')
                        table.on("approve", lambda e: _show_approve_dialog(e.args["id"], True, load_scraps))
                        table.on("reject", lambda e: _show_approve_dialog(e.args["id"], False, load_scraps))

                    # 分页
                    total_pages = (total + 19) // 20
                    if total_pages > 1:
                        with ui.row().classes("w-full justify-center q-mt-md"):
                            for p in range(1, total_pages + 1):
                                btn = ui.button(str(p), on_click=lambda _, pg=p: load_scraps(pg))
                                if p == page:
                                    btn.props("color=blue")
                                else:
                                    btn.props("flat")

            except Exception as e:
                with table_container:
                    ui.label(f"请求失败: {e}").classes("text-red")

        search_btn.on_click(lambda: load_scraps())
        load_scraps()


def _show_approve_dialog(scrap_id: int, is_approve: bool, reload_fn):
    title = "审批通过" if is_approve else "审批驳回"
    color = "green" if is_approve else "red"

    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label(title).classes("text-h6")
        note = ui.input("审批备注", placeholder="如：确认报废 / 建议先维修").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_action():
                if is_approve:
                    result = api.approve_scrap(scrap_id, note.value or "")
                else:
                    result = api.reject_scrap(scrap_id, note.value or "")

                if result.get("code") == 0:
                    dialog.close()
                    ui.notify(f"{title}成功", type="positive")
                    reload_fn()
                else:
                    msg.text = result.get("msg", "操作失败")

            ui.button("确认", on_click=do_action).props(f"color={color}")
    dialog.open()
