"""顶部导航栏组件"""
from nicegui import ui, app
from api_client import api


def navbar():
    """渲染顶部导航栏，根据用户角色显示不同菜单"""
    user = app.storage.user.get("user")
    if not user:
        return

    role = user.get("role", "")
    real_name = user.get("real_name", "")

    with ui.header().classes("bg-blue-8 text-white shadow-2 items-center justify-between"):
        with ui.row().classes("items-center gap-0"):
            ui.label("📦 望京实验学校物品管理").classes("text-h6 q-mr-md cursor-pointer").on("click", lambda: ui.navigate.to("/dashboard"))

            ui.button("仪表盘", icon="dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat color=white")
            ui.button("物品管理", icon="inventory_2", on_click=lambda: ui.navigate.to("/items")).props("flat color=white")
            ui.button("借用管理", icon="swap_horiz", on_click=lambda: ui.navigate.to("/borrows")).props("flat color=white")
            ui.button("我的借用", icon="person", on_click=lambda: ui.navigate.to("/my-borrows")).props("flat color=white")
            ui.button("报废管理", icon="delete_forever", on_click=lambda: ui.navigate.to("/scraps")).props("flat color=white")

            if role == "admin":
                ui.button("用户管理", icon="group", on_click=lambda: ui.navigate.to("/users")).props("flat color=white")

        with ui.row().classes("items-center"):
            role_labels = {"admin": "管理员", "staff": "教职工", "student": "学生"}
            ui.badge(role_labels.get(role, role), color="white", text_color="blue-8").classes("q-mr-sm")
            ui.label(real_name).classes("q-mr-md")
            ui.button("退出", icon="logout", on_click=_logout).props("flat color=white")


async def _logout():
    """退出登录"""
    try:
        api.logout()
    except Exception:
        pass
    app.storage.user.clear()
    ui.navigate.to("/login")
