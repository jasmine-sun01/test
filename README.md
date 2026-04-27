# 学校物品二维码管理系统

物品录入 → 借出 → 归还 → 报废 全生命周期管理

---

## 本地启动后端

### 1. 安装依赖

```bash
cd school-qrcode-system
pip install -r requirements.txt
```

### 2. 初始化数据库（首次运行）

```bash
cd backend
python init_db.py
```

默认创建以下测试账号：

| 用户名    | 密码      | 角色    |
|-----------|-----------|---------|
| admin     | admin123  | 管理员  |
| teacher1  | teacher1  | 教职工  |
| student1  | student1  | 学生    |

### 3. 启动后端

```bash
cd backend
python main.py
```

默认端口 **8000**，API 文档：http://localhost:8000/docs

### 4. 使用自定义端口

通过环境变量设置：

```bash
# macOS / Linux
API_PORT=9090 python main.py

# 或者 export
export API_PORT=9090
python main.py
```

### 5. 所有可配置环境变量

| 变量名         | 默认值                          | 说明                        |
|----------------|--------------------------------|-----------------------------|
| API_PORT       | 8000                           | 后端 API 端口               |
| DB_PATH        | data/school_qr.db              | SQLite 数据库文件路径        |
| SESSION_SECRET | dev-secret-change-in-prod      | Session 签名密钥             |
| SERVER_HOST    | localhost:8080                  | 二维码中的前端地址           |
| STATIC_DIR     | static                         | 静态文件目录（二维码/PDF）   |

### 6. 验证后端运行

```bash
# 健康检查
curl http://localhost:8000/

# 登录（获取 session cookie）
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 查看物品列表（带 cookie）
curl -b cookies.txt http://localhost:8000/api/items

# 查看仪表盘统计
curl -b cookies.txt http://localhost:8000/api/dashboard/stats
```

---

## 启动前端

```bash
cd frontend
python main.py
```

默认端口 **8080**，打开浏览器访问：http://localhost:8080

自定义端口：

```bash
FRONTEND_PORT=9091 python main.py
```

> 注意：前端需要后端先启动。默认连接 http://localhost:8000/api
> 如需修改后端地址：`API_BASE_URL=http://localhost:9090/api python main.py`

---

## 项目结构

```
school-qrcode-system/
├── docs/                  # 设计文档
├── backend/               # FastAPI 后端
│   ├── main.py            # 入口
│   ├── config.py          # 配置
│   ├── database.py        # SQLAlchemy 引擎
│   ├── init_db.py         # 建表 + 种子数据
│   ├── models/            # ORM 模型
│   ├── schemas/           # Pydantic 请求/响应
│   ├── services/          # 业务逻辑
│   ├── routers/           # API 路由
│   └── utils/             # 认证 & 依赖注入
├── frontend/              # NiceGUI 前端（待实现）
└── requirements.txt
```
