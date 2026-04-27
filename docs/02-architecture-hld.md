# 学校物品二维码管理系统 — 架构设计 (HLD)

## 1. 技术选型

| 层 | 技术 | 说明 |
|----|------|------|
| **后端框架** | FastAPI (Python) | 高性能异步 API 框架，自带 Swagger 文档 |
| **数据库** | SQLite + SQLAlchemy ORM | 轻量级，零配置，适合学校单机场景 |
| **前端框架** | NiceGUI (Python) | 纯 Python 编写 Web UI，基于 Vue/Quasar，支持响应式 |
| **二维码生成** | qrcode + Pillow | 生成二维码图片 |
| **PDF 导出** | reportlab | 批量二维码打印 PDF |
| **认证** | JWT (python-jose) | 无状态 Token 认证 |
| **部署** | Docker Compose | 一键启动前后端 |

---

## 2. 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                      用户设备                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ PC 浏览器 │  │ 手机浏览器 │  │ 手机扫码 → 物品详情   │   │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘   │
└───────┼─────────────┼───────────────────┼───────────────┘
        │             │                   │
        └─────────────┼───────────────────┘
                      │ HTTP/HTTPS
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   NiceGUI 前端 (Python)                   │
│                   端口: 8080                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ 登录  │ │ 仪表盘│ │物品管理│ │借用管理│ │报废管理│          │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘          │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API 调用
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI 后端 (Python)                    │
│                  端口: 8000                               │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ 物品模块    │  │ 借用模块    │  │ 报废模块    │        │
│  │ /api/items  │  │ /api/borrows│  │ /api/scraps │        │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │
│         │               │               │              │
│  ┌──────┴───────────────┴───────────────┴──────┐       │
│  │           Service 业务逻辑层                  │       │
│  │  物品服务 │ 借用服务 │ 报废服务 │ 用户服务      │       │
│  └──────────────────────┬──────────────────────┘       │
│                         │                              │
│  ┌──────────────────────┴──────────────────────┐       │
│  │          SQLAlchemy ORM / Repository         │       │
│  └──────────────────────┬──────────────────────┘       │
│         ┌───────────────┼───────────────┐              │
│  ┌──────┴──┐     ┌──────┴──┐     ┌──────┴──┐          │
│  │二维码生成│     │PDF 导出  │     │JWT 认证  │          │
│  │ qrcode  │     │reportlab │     │python-jose│          │
│  └─────────┘     └─────────┘     └──────────┘          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
               ┌──────────────┐
               │   SQLite DB   │
               │  school_qr.db │
               └──────────────┘
```

---

## 3. 项目目录结构

```
school-qrcode-system/
├── docs/                          # 文档
│   ├── 01-requirements.md
│   ├── 02-architecture-hld.md
│   └── 03-lld.md
├── backend/                       # 后端 FastAPI
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置（DB路径、JWT密钥等）
│   ├── database.py                # SQLAlchemy 引擎 & Session
│   ├── models/                    # ORM 模型
│   │   ├── item.py                # 物品表
│   │   ├── borrow.py              # 借用记录表
│   │   ├── scrap.py               # 报废记录表
│   │   ├── user.py                # 用户表
│   │   └── category.py            # 分类表
│   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── item.py
│   │   ├── borrow.py
│   │   ├── scrap.py
│   │   └── user.py
│   ├── routers/                   # API 路由
│   │   ├── items.py               # /api/items
│   │   ├── borrows.py             # /api/borrows
│   │   ├── scraps.py              # /api/scraps
│   │   ├── users.py               # /api/users
│   │   └── auth.py                # /api/auth
│   ├── services/                  # 业务逻辑
│   │   ├── item_service.py
│   │   ├── borrow_service.py
│   │   ├── scrap_service.py
│   │   ├── qrcode_service.py      # 二维码生成 & PDF 导出
│   │   └── user_service.py
│   └── utils/
│       ├── auth.py                # JWT 工具
│       └── deps.py                # 依赖注入（当前用户等）
├── frontend/                      # 前端 NiceGUI
│   ├── main.py                    # NiceGUI 入口
│   ├── pages/                     # 各页面
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   ├── items.py
│   │   ├── item_detail.py
│   │   ├── item_create.py
│   │   ├── borrows.py
│   │   ├── scraps.py
│   │   ├── users.py
│   │   └── my_borrows.py
│   ├── components/                # 可复用 UI 组件
│   │   ├── navbar.py
│   │   ├── item_card.py
│   │   └── status_badge.py
│   └── api_client.py              # 封装后端 API 调用
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── requirements.txt
```

---

## 4. API 概览

### 4.1 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT Token |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 4.2 物品管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/items` | 物品列表（支持分页、筛选） |
| POST | `/api/items` | 录入物品 (Admin) |
| GET | `/api/items/{id}` | 物品详情 |
| PUT | `/api/items/{id}` | 编辑物品 (Admin) |
| DELETE | `/api/items/{id}` | 删除物品 (Admin) |
| POST | `/api/items/import` | CSV 批量导入 (Admin) |
| GET | `/api/items/{id}/qrcode` | 获取二维码图片 |
| POST | `/api/items/qrcode-pdf` | 批量生成二维码 PDF |

### 4.3 借用管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/borrows` | 借用记录列表 |
| POST | `/api/borrows` | 发起借用 |
| PUT | `/api/borrows/{id}/return` | 归还 |
| GET | `/api/borrows/my` | 我的借用记录 |
| GET | `/api/borrows/overdue` | 逾期列表 |

### 4.4 报废管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scraps` | 报废申请列表 |
| POST | `/api/scraps` | 发起报废申请 |
| PUT | `/api/scraps/{id}/approve` | 审批通过 (Admin) |
| PUT | `/api/scraps/{id}/reject` | 审批驳回 (Admin) |

### 4.5 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表 (Admin) |
| POST | `/api/users` | 创建用户 (Admin) |
| PUT | `/api/users/{id}` | 编辑用户 (Admin) |
| PUT | `/api/users/{id}/disable` | 禁用用户 (Admin) |

### 4.6 仪表盘

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats` | 统计概览数据 |
| GET | `/api/dashboard/top-borrowed` | 借用频次 Top N |
| GET | `/api/reports/export` | 导出借用报表 CSV |