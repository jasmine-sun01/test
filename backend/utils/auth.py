"""Session 认证工具 — 基于 Cookie 的 Session 管理"""
import hashlib
import uuid
from datetime import datetime


def hash_password(password: str) -> str:
    """密码哈希 (SHA256)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(plain) == hashed


def generate_session_id() -> str:
    """生成随机 Session ID"""
    return uuid.uuid4().hex


# 内存 Session 存储 — 单机够用，重启后需重新登录
# 格式: {session_id: {"user_id": int, "username": str, "role": str, "created": datetime}}
_sessions: dict[str, dict] = {}


def create_session(user_id: int, username: str, role: str, real_name: str) -> str:
    """创建 Session，返回 session_id"""
    sid = generate_session_id()
    _sessions[sid] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "real_name": real_name,
        "created": datetime.now(),
    }
    return sid


def get_session(session_id: str) -> dict | None:
    """根据 session_id 获取 Session 数据"""
    return _sessions.get(session_id)


def destroy_session(session_id: str):
    """销毁 Session"""
    _sessions.pop(session_id, None)
