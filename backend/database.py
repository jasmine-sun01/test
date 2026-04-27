"""SQLAlchemy 引擎 & Session 管理"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import DATABASE_URL, DB_PATH


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


# 确保数据库目录存在
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

# 创建引擎（SQLite 开启 WAL 模式提升并发性能）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


# SQLite 开启外键约束
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session 工厂
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI 依赖注入：获取数据库 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（如果不存在）"""
    import models  # noqa: F401 — 触发所有 model 注册
    Base.metadata.create_all(bind=engine)
