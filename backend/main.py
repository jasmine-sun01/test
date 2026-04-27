"""FastAPI 后端入口"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

from config import API_PORT, STATIC_DIR, QRCODE_DIR, EXPORT_DIR
from database import init_db, SessionLocal
from services.borrow_service import mark_overdue

# 确保静态目录存在
for d in [STATIC_DIR, QRCODE_DIR, EXPORT_DIR]:
    os.makedirs(d, exist_ok=True)


# --- 定时任务：逾期标记 ---
scheduler = BackgroundScheduler()


def _run_overdue_check():
    """每天检查逾期借用"""
    db = SessionLocal()
    try:
        count = mark_overdue(db)
        if count:
            print(f"[定时任务] 标记 {count} 条逾期借用记录")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    init_db()
    print("✓ 数据库初始化完成")
    scheduler.add_job(_run_overdue_check, "cron", hour=1, minute=0)
    scheduler.start()
    print("✓ 逾期检测定时任务已启动 (每天 01:00)")
    yield
    # 关闭时
    scheduler.shutdown()


# --- FastAPI 应用 ---
app = FastAPI(
    title="北京市第八十中学望京实验学校物品管理系统",
    description="物品录入→借出→归还→报废 全生命周期管理",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS（前端 NiceGUI 可能跑在不同端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（二维码图片等）
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- 注册路由 ---
from routers.auth import router as auth_router
from routers.items import router as items_router
from routers.borrows import router as borrows_router
from routers.scraps import router as scraps_router
from routers.users import router as users_router
from routers.dashboard import router as dashboard_router

app.include_router(auth_router)
app.include_router(items_router)
app.include_router(borrows_router)
app.include_router(scraps_router)
app.include_router(users_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"msg": "北京市第八十中学望京实验学校物品管理系统 API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=True)
