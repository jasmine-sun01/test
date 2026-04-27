"""应用配置"""
import os

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "data/school_qr.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Session 密钥
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-prod")

# 服务端口
API_PORT = int(os.getenv("API_PORT", "8000"))

# 二维码中的服务器地址（扫码后跳转用）
SERVER_HOST = os.getenv("SERVER_HOST", "localhost:8080")

# 静态文件目录
STATIC_DIR = os.getenv("STATIC_DIR", "static")
QRCODE_DIR = os.path.join(STATIC_DIR, "qrcodes")
EXPORT_DIR = os.path.join(STATIC_DIR, "exports")
