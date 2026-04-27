"""状态标签组件 — 不同状态用不同颜色"""
from nicegui import ui


# 物品状态
ITEM_STATUS = {
    "available": ("可用", "green"),
    "borrowed": ("已借出", "orange"),
    "pending_scrap": ("待报废", "red"),
    "scrapped": ("已报废", "grey"),
}

# 借用状态
BORROW_STATUS = {
    "active": ("借用中", "blue"),
    "returned": ("已归还", "green"),
    "overdue": ("逾期", "red"),
}

# 报废状态
SCRAP_STATUS = {
    "pending": ("待审批", "orange"),
    "approved": ("已通过", "green"),
    "rejected": ("已驳回", "red"),
}


def item_status_badge(status: str):
    """物品状态标签"""
    label, color = ITEM_STATUS.get(status, (status, "grey"))
    ui.badge(label, color=color)


def borrow_status_badge(status: str):
    """借用状态标签"""
    label, color = BORROW_STATUS.get(status, (status, "grey"))
    ui.badge(label, color=color)


def scrap_status_badge(status: str):
    """报废状态标签"""
    label, color = SCRAP_STATUS.get(status, (status, "grey"))
    ui.badge(label, color=color)
