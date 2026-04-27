"""封装后端 API 调用 — 每次请求从 NiceGUI app.storage.user 读 session_id"""
import os
import httpx
from nicegui import app

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


def _get_session_id() -> str | None:
    """从 NiceGUI 用户存储读取 session_id"""
    try:
        return app.storage.user.get("session_id")
    except Exception:
        return None


def _cookies() -> dict:
    """构造 Cookie dict"""
    sid = _get_session_id()
    return {"session_id": sid} if sid else {}


def _post(path: str, **kwargs) -> dict:
    with httpx.Client(base_url=API_BASE, timeout=30) as c:
        resp = c.post(path, cookies=_cookies(), **kwargs)
        return resp.json()


def _get(path: str, **kwargs) -> dict:
    with httpx.Client(base_url=API_BASE, timeout=30) as c:
        resp = c.get(path, cookies=_cookies(), **kwargs)
        return resp.json()


def _put(path: str, **kwargs) -> dict:
    with httpx.Client(base_url=API_BASE, timeout=30) as c:
        resp = c.put(path, cookies=_cookies(), **kwargs)
        return resp.json()


def _delete(path: str, **kwargs) -> dict:
    with httpx.Client(base_url=API_BASE, timeout=30) as c:
        resp = c.delete(path, cookies=_cookies(), **kwargs)
        return resp.json()


class ApiClient:

    # ---------- 认证 ----------
    def login(self, username: str, password: str) -> dict:
        """登录 — 特殊处理：需要从 response 提取 session_id cookie"""
        with httpx.Client(base_url=API_BASE, timeout=30) as c:
            resp = c.post("/auth/login", json={"username": username, "password": password})
            data = resp.json()
            # 把后端返回的 session_id cookie 存到 NiceGUI user storage
            sid = resp.cookies.get("session_id")
            if sid:
                app.storage.user["session_id"] = sid
            return data

    def logout(self) -> dict:
        result = _post("/auth/logout")
        try:
            app.storage.user.pop("session_id", None)
        except Exception:
            pass
        return result

    def get_me(self) -> dict:
        return _get("/auth/me")

    # ---------- 物品 ----------
    def list_items(self, **params) -> dict:
        return _get("/items", params=params)

    def get_item(self, item_id: int) -> dict:
        return _get(f"/items/{item_id}")

    def create_item(self, data: dict) -> dict:
        return _post("/items", json=data)

    def update_item(self, item_id: int, data: dict) -> dict:
        return _put(f"/items/{item_id}", json=data)

    def delete_item(self, item_id: int) -> dict:
        return _delete(f"/items/{item_id}")

    def get_categories(self) -> dict:
        return _get("/items/categories")

    def get_qrcode_url(self, item_id: int) -> str:
        """返回二维码图片的完整 URL（含 session cookie 无法直接用，走代理）"""
        return f"{API_BASE.replace('/api', '')}/api/items/{item_id}/qrcode"

    # ---------- 借用 ----------
    def borrow_item(self, item_id: int, due_date: str, purpose: str = "") -> dict:
        return _post("/borrows", json={
            "item_id": item_id, "due_date": due_date, "purpose": purpose,
        })

    def return_item(self, borrow_id: int, return_note: str = "") -> dict:
        return _put(f"/borrows/{borrow_id}/return", json={"return_note": return_note})

    def list_borrows(self, **params) -> dict:
        return _get("/borrows", params=params)

    def my_borrows(self, **params) -> dict:
        return _get("/borrows/my", params=params)

    def list_overdue(self) -> dict:
        return _get("/borrows/overdue")

    # ---------- 报废 ----------
    def apply_scrap(self, item_id: int, reason: str) -> dict:
        return _post("/scraps", json={"item_id": item_id, "reason": reason})

    def approve_scrap(self, scrap_id: int, note: str = "") -> dict:
        return _put(f"/scraps/{scrap_id}/approve", json={"approve_note": note})

    def reject_scrap(self, scrap_id: int, note: str = "") -> dict:
        return _put(f"/scraps/{scrap_id}/reject", json={"approve_note": note})

    def list_scraps(self, **params) -> dict:
        return _get("/scraps", params=params)

    # ---------- 用户 ----------
    def list_users(self, **params) -> dict:
        return _get("/users", params=params)

    def create_user(self, data: dict) -> dict:
        return _post("/users", json=data)

    def update_user(self, user_id: int, data: dict) -> dict:
        return _put(f"/users/{user_id}", json=data)

    def disable_user(self, user_id: int) -> dict:
        return _put(f"/users/{user_id}/disable")

    # ---------- 仪表盘 ----------
    def get_stats(self) -> dict:
        return _get("/dashboard/stats")

    def get_top_borrowed(self, limit: int = 10) -> dict:
        return _get("/dashboard/top-borrowed", params={"limit": limit})


# 全局单例
api = ApiClient()
