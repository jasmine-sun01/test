"""NiceGUI 前端入口"""
import os
from pathlib import Path
from nicegui import ui, app

# 全局状态：当前登录用户信息
# 存储在 app.storage.user 中（NiceGUI 自带 per-user storage）

FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8080"))

# 应用图标
FAVICON = Path(__file__).parent / "Image.jpeg"

# 静态文件：让 Image.jpeg 可通过 /static/Image.jpeg 访问
app.add_static_files("/static", str(Path(__file__).parent))


def init_routes():
    """注册所有页面路由"""
    from pages.login import login_page
    from pages.dashboard import dashboard_page
    from pages.items import items_page
    from pages.item_create import item_create_page      # 固定路径必须在动态路径之前
    from pages.item_detail import item_detail_page
    from pages.borrows import borrows_page
    from pages.my_borrows import my_borrows_page
    from pages.scraps import scraps_page
    from pages.users import users_page


init_routes()

ui.run(
    title="北京市第八十中学望京实验学校物品管理系统",
    port=FRONTEND_PORT,
    storage_secret="school-qr-storage-secret",
    dark=False,
    favicon=FAVICON,
)
