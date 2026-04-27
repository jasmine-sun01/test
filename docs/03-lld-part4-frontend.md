# LLD Part 4: 前端页面设计 + 二维码/PDF 方案

## 1. 前端技术方案

使用 **NiceGUI** (Python Web UI 框架):
- 基于 Vue.js + Quasar 组件库，纯 Python 编写
- 内置响应式布局，自动适配手机/PC
- 通过 `httpx` 调用后端 REST API

```
frontend/
├── main.py              # NiceGUI 入口，路由注册
├── api_client.py         # httpx 封装，统一调用后端 API
├── pages/
│   ├── login.py          # 登录页
│   ├── dashboard.py      # 仪表盘
│   ├── items.py          # 物品列表
│   ├── item_detail.py    # 物品详情（扫码跳转目标）
│   ├── item_create.py    # 物品录入表单
│   ├── borrows.py        # 借用管理
│   ├── scraps.py         # 报废管理
│   ├── users.py          # 用户管理
│   └── my_borrows.py     # 我的借用
└── components/
    ├── navbar.py          # 顶部导航栏
    ├── item_card.py       # 物品卡片组件
    └── status_badge.py    # 状态标签（颜色区分）
```

---

## 2. 页面布局

### 2.1 整体结构

```
┌─────────────────────────────────────────┐
│  顶部导航栏 (navbar)                     │
│  Logo  物品管理  借用管理  报废  我的借用  │
│                          [张三] [退出]   │
├─────────────────────────────────────────┤
│                                         │
│              页面内容区                   │
│                                         │
└─────────────────────────────────────────┘
```

### 2.2 仪表盘

```
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ 物品总数 │ │ 在借数量│ │ 逾期数量│ │ 已报废  │
│  520    │ │  105   │ │  12    │ │  23    │
└────────┘ └────────┘ └────────┘ └────────┘

┌──────────────────┐ ┌──────────────────┐
│ 借用频次 Top 10   │ │ 最近逾期物品      │
│ ▓▓▓▓▓▓▓ 投影仪   │ │ ITM-xxx 张三 3天  │
│ ▓▓▓▓▓  篮球      │ │ ITM-xxx 李四 1天  │
│ ▓▓▓▓   万用表    │ │ ...              │
└──────────────────┘ └──────────────────┘
```

### 2.3 物品详情页（扫码跳转目标）

URL: `/items/{id}`  ← 二维码编码此 URL

```
┌─────────────────────────────────────────┐
│  物品详情                                │
├─────────────────────────────────────────┤
│  名称: 投影仪          状态: [可用]      │
│  编号: ITM-20260423-0001                │
│  分类: 电子设备                          │
│  型号: EPSON CB-X06                     │
│  位置: 教学楼A栋 301室                   │
│  购入: 2026-01-15  ¥3,500.00           │
│                                         │
│  [借用此物品]  [申请报废]                 │
│                                         │
│  ── 借用历史 ──                          │
│  张三  2026-04-01 ~ 2026-04-10  已归还  │
│  李四  2026-03-15 ~ 2026-03-20  已归还  │
└─────────────────────────────────────────┘
```

---

## 3. 二维码方案

### 3.1 生成逻辑

```python
import qrcode
from PIL import Image

def generate_qrcode(item_id: int, item_code: str) -> str:
    """生成二维码，返回保存路径"""
    # 二维码内容 = 物品详情页 URL
    url = f"http://{SERVER_HOST}:8080/items/{item_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # 保存路径: static/qrcodes/ITM-20260423-0001.png
    path = f"static/qrcodes/{item_code}.png"
    img.save(path)
    return path
```

### 3.2 扫码流程

```
手机扫码 → 浏览器打开 URL → 物品详情页
                              │
                              ├── 未登录 → 跳转登录 → 回到详情页
                              │
                              ├── 可用 → 显示 [借用] 按钮
                              │
                              └── 已借出 → 显示借用人和归还日期
```

---

## 4. PDF 批量打印方案

### 4.1 布局

每页 A4 纸排列 2×4 = 8 个二维码标签:

```
┌─────────────┬─────────────┐
│  [二维码]    │  [二维码]    │
│  投影仪      │  篮球       │
│  ITM-xxx-01 │  ITM-xxx-02 │
├─────────────┼─────────────┤
│  [二维码]    │  [二维码]    │
│  万用表      │  显微镜      │
│  ITM-xxx-03 │  ITM-xxx-04 │
├─────────────┼─────────────┤
│     ...     │     ...     │
└─────────────┴─────────────┘
```

### 4.2 实现

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_qrcode_pdf(items: list) -> str:
    """生成包含多个物品二维码的 PDF"""
    pdf_path = f"static/exports/qrcodes_{timestamp}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)

    cols, rows = 2, 4  # 每页 2列 x 4行
    cell_w, cell_h = A4[0] / cols, A4[1] / rows

    for i, item in enumerate(items):
        page_idx = i % (cols * rows)
        if page_idx == 0 and i > 0:
            c.showPage()  # 翻页

        col = page_idx % cols
        row = page_idx // cols

        x = col * cell_w + 20
        y = A4[1] - (row + 1) * cell_h + 20

        # 画二维码图片
        c.drawImage(item.qrcode_path, x, y + 30, 80, 80)
        # 物品名称
        c.drawString(x, y + 15, item.name)
        # 物品编号
        c.drawString(x, y, item.code)

    c.save()
    return pdf_path
```

---

## 5. 前端 API 调用封装

```python
# frontend/api_client.py
import httpx

class ApiClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        # 使用 httpx.AsyncClient 自动管理 Cookie（Session）
        self.client = httpx.AsyncClient(base_url=base_url)

    async def login(self, username, password):
        resp = await self.client.post(
            "/auth/login",
            json={"username": username, "password": password}
        )
        # session_id 自动存入 client.cookies
        return resp.json()["data"]

    async def get_items(self, **params):
        resp = await self.client.get("/items", params=params)
        return resp.json()["data"]

    async def borrow_item(self, item_id, due_date, purpose):
        resp = await self.client.post(
            "/borrows",
            json={"item_id": item_id, "due_date": due_date, "purpose": purpose}
        )
        return resp.json()
```

---

## 6. 部署方案

### docker-compose.yml

```yaml
version: "3.8"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data          # SQLite 数据持久化
      - ./static:/app/static      # 二维码图片、PDF
    environment:
      - SESSION_SECRET=your-secret-key
      - DB_PATH=/app/data/school_qr.db

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8080:8080"
    environment:
      - API_BASE_URL=http://backend:8000/api
    depends_on:
      - backend
```

一键启动: `docker-compose up -d`
