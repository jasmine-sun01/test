"""登录页"""
from nicegui import ui, app
from api_client import api


@ui.page("/login")
@ui.page("/")
def login_page():
    # 已登录则跳转仪表盘
    if app.storage.user.get("user"):
        ui.navigate.to("/dashboard")
        return

    with ui.column().classes("absolute-center items-center"):
        ui.image("/static/Image.jpeg").classes("w-24 h-24 q-mb-md").style("border-radius: 12px")
        ui.label("北京市第八十中学望京实验学校物品管理系统").classes("text-h5 text-blue-8 q-mb-lg")

        with ui.card().classes("w-80 q-pa-lg"):
            ui.label("登录").classes("text-h5 text-center q-mb-md")

            username = ui.input("用户名", placeholder="请输入用户名").classes("full-width").props("outlined")
            password = ui.input("密码", placeholder="请输入密码", password=True, password_toggle_button=True).classes("full-width").props("outlined")
            msg = ui.label("").classes("text-red text-center")

            async def do_login():
                if not username.value or not password.value:
                    msg.text = "请输入用户名和密码"
                    return
                msg.text = ""
                try:
                    result = api.login(username.value, password.value)
                    if result.get("code") == 0:
                        app.storage.user["user"] = result["data"]
                        # 登录后跳转回之前的页面（扫码场景）
                        redirect = app.storage.user.pop("redirect", None)
                        ui.navigate.to(redirect or "/dashboard")
                    else:
                        msg.text = result.get("msg", "登录失败")
                except Exception as e:
                    msg.text = f"连接后端失败: {e}"

            ui.button("登 录", on_click=do_login, icon="login").classes("full-width q-mt-md").props("color=blue-8")
            password.on("keydown.enter", do_login)

        with ui.row().classes("q-mt-md text-grey"):
            ui.label("测试账号: admin/admin123  teacher1/teacher1  student1/student1").classes("text-caption")
