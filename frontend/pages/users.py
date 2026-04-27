"""用户管理页（Admin only）"""
from nicegui import ui, app
from api_client import api
from components.navbar import navbar


ROLE_LABELS = {"admin": "管理员", "staff": "教职工", "student": "学生"}


@ui.page("/users")
def users_page():
    if not app.storage.user.get("user") or not app.storage.user.get("session_id"):
        ui.navigate.to("/login")
        return

    user = app.storage.user["user"]
    if user.get("role") != "admin":
        ui.navigate.to("/dashboard")
        return

    navbar()

    with ui.column().classes("q-pa-md w-full max-w-6xl mx-auto"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("用户管理").classes("text-h5")
            ui.button("添加用户", icon="person_add", on_click=lambda: _show_create_dialog(load_users)).props("color=blue")

        table_container = ui.column().classes("w-full q-mt-md")

        def load_users(page=1):
            table_container.clear()

            try:
                result = api.list_users(page=page, page_size=20)
                if result.get("code") != 0:
                    with table_container:
                        ui.label(f"加载失败: {result.get('msg')}").classes("text-red")
                    return

                data = result["data"]
                users = data.get("items", [])
                total = data.get("total", 0)

                with table_container:
                    if not users:
                        ui.label("暂无用户").classes("text-grey text-center q-pa-lg")
                        return

                    columns = [
                        {"name": "username", "label": "用户名", "field": "username", "align": "left"},
                        {"name": "real_name", "label": "姓名", "field": "real_name", "align": "left"},
                        {"name": "role", "label": "角色", "field": "role_label", "align": "center"},
                        {"name": "phone", "label": "电话", "field": "phone", "align": "left"},
                        {"name": "is_active", "label": "状态", "field": "active_label", "align": "center"},
                        {"name": "action", "label": "操作", "field": "action", "align": "center"},
                    ]
                    rows = []
                    for u in users:
                        rows.append({
                            "id": u["id"],
                            "username": u["username"],
                            "real_name": u["real_name"],
                            "role": u["role"],
                            "role_label": ROLE_LABELS.get(u["role"], u["role"]),
                            "phone": u.get("phone") or "-",
                            "is_active": u.get("is_active", True),
                            "active_label": "启用" if u.get("is_active", True) else "已禁用",
                        })

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                    table.add_slot("body-cell-action", '''
                        <q-td :props="props">
                            <q-btn flat dense color="blue" label="编辑"
                                   @click="$parent.$emit('edit', props.row)" class="q-mr-xs" />
                            <q-btn v-if="props.row.is_active"
                                   flat dense color="red" label="禁用"
                                   @click="$parent.$emit('disable', props.row)" />
                        </q-td>
                    ''')
                    table.on("edit", lambda e: _show_edit_dialog(e.args, load_users))
                    table.on("disable", lambda e: _do_disable(e.args["id"], load_users))

                    # 分页
                    total_pages = (total + 19) // 20
                    if total_pages > 1:
                        with ui.row().classes("w-full justify-center q-mt-md"):
                            for p in range(1, total_pages + 1):
                                btn = ui.button(str(p), on_click=lambda _, pg=p: load_users(pg))
                                if p == page:
                                    btn.props("color=blue")
                                else:
                                    btn.props("flat")

            except Exception as e:
                with table_container:
                    ui.label(f"请求失败: {e}").classes("text-red")

        load_users()


def _show_create_dialog(reload_fn):
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("添加用户").classes("text-h6")
        username = ui.input("用户名 *").classes("full-width").props("outlined")
        password = ui.input("密码 *", password=True).classes("full-width").props("outlined")
        real_name = ui.input("真实姓名 *").classes("full-width").props("outlined")
        role = ui.select({"student": "学生", "staff": "教职工", "admin": "管理员"}, value="student", label="角色").classes("full-width").props("outlined")
        phone = ui.input("电话").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_create():
                if not username.value or not password.value or not real_name.value:
                    msg.text = "请填写必填项"
                    return
                data = {
                    "username": username.value,
                    "password": password.value,
                    "real_name": real_name.value,
                    "role": role.value,
                }
                if phone.value:
                    data["phone"] = phone.value

                result = api.create_user(data)
                if result.get("code") == 0:
                    dialog.close()
                    ui.notify("用户创建成功", type="positive")
                    reload_fn()
                else:
                    msg.text = result.get("msg", "创建失败")

            ui.button("创建", on_click=do_create).props("color=blue")
    dialog.open()


def _show_edit_dialog(user_data: dict, reload_fn):
    user_id = user_data["id"]
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("编辑用户").classes("text-h6")
        ui.label(f"用户名: {user_data['username']}").classes("text-grey")
        real_name = ui.input("真实姓名", value=user_data["real_name"]).classes("full-width").props("outlined")
        role = ui.select(
            {"student": "学生", "staff": "教职工", "admin": "管理员"},
            value=user_data["role"],
            label="角色",
        ).classes("full-width").props("outlined")
        phone = ui.input("电话", value=user_data.get("phone") or "").classes("full-width").props("outlined")
        msg = ui.label("").classes("text-red")

        with ui.row().classes("full-width justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")

            def do_update():
                data = {}
                if real_name.value:
                    data["real_name"] = real_name.value
                if role.value:
                    data["role"] = role.value
                if phone.value:
                    data["phone"] = phone.value

                result = api.update_user(user_id, data)
                if result.get("code") == 0:
                    dialog.close()
                    ui.notify("用户更新成功", type="positive")
                    reload_fn()
                else:
                    msg.text = result.get("msg", "更新失败")

            ui.button("保存", on_click=do_update).props("color=blue")
    dialog.open()


def _do_disable(user_id: int, reload_fn):
    result = api.disable_user(user_id)
    if result.get("code") == 0:
        ui.notify("用户已禁用", type="warning")
        reload_fn()
    else:
        ui.notify(result.get("msg", "操作失败"), type="negative")
