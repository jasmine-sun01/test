# LLD Part 1: 数据库模型设计

## 1. ER 关系图

```
┌──────────┐       ┌──────────────┐       ┌──────────────┐
│ category │       │     user     │       │   category   │
│──────────│       │──────────────│       │──────────────│
│ id (PK)  │       │ id (PK)      │       │ id (PK)      │
│ name     │       │ username     │       │ name         │
│ desc     │       │ password_hash│       │ description  │
└────┬─────┘       │ role         │       └──────────────┘
     │1            │ is_active    │
     │             └──────┬───────┘
     │                    │1
     │n                   │
┌────┴─────────────┐      │
│      item        │      │
│──────────────────│      │
│ id (PK)          │      │
│ code (UQ)        │      │       n                n
│ name             │◄─────┼──── borrow_record ────►│
│ category_id (FK) │      │    ┌───────────────┐   │
│ model            │      │    │ id (PK)       │   │
│ status           │      │    │ item_id (FK)  │   │
│ purchase_date    │      │    │ user_id (FK)  │   │
│ purchase_price   │      │    │ borrow_date   │   │
│ location         │      │    │ due_date      │   │
│ qrcode_path      │      │    │ return_date   │   │
│ remark           │      │    │ status        │   │
└────┬─────────────┘      │    │ purpose       │   │
     │1                   │    └───────────────┘   │
     │                    │                        │
     │n                   │n                       │
┌────┴─────────────┐      │
│  scrap_record    │──────┘
│──────────────────│
│ id (PK)          │
│ item_id (FK)     │
│ applicant_id(FK) │
│ approver_id (FK) │
│ reason           │
│ status           │
│ apply_time       │
│ approve_time     │
└──────────────────┘
```

---

## 2. 表结构详细定义

### 2.1 user — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, 自增 | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(128) | NOT NULL | 密码哈希 (bcrypt) |
| real_name | VARCHAR(50) | NOT NULL | 真实姓名 |
| role | VARCHAR(20) | NOT NULL | 角色: admin / staff / student |
| phone | VARCHAR(20) | | 联系电话 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否启用 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

### 2.2 category — 分类表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, 自增 | 主键 |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 分类名称（电子设备、体育器材等） |
| description | VARCHAR(200) | | 分类描述 |

### 2.3 item — 物品表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, 自增 | 主键 |
| code | VARCHAR(32) | UNIQUE, NOT NULL | 物品编号（自动生成，如 ITM-20260423-0001） |
| name | VARCHAR(100) | NOT NULL | 物品名称 |
| category_id | INTEGER | FK → category.id | 所属分类 |
| model | VARCHAR(100) | | 型号/规格 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'available' | 状态: available / borrowed / pending_scrap / scrapped |
| purchase_date | DATE | | 购入日期 |
| purchase_price | DECIMAL(10,2) | | 购入价格 |
| location | VARCHAR(100) | | 存放位置 |
| qrcode_path | VARCHAR(200) | | 二维码图片存储路径 |
| remark | TEXT | | 备注 |
| created_at | DATETIME | DEFAULT NOW | 录入时间 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

**索引:** `idx_item_status`, `idx_item_category`, `idx_item_code`

### 2.4 borrow_record — 借用记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, 自增 | 主键 |
| item_id | INTEGER | FK → item.id, NOT NULL | 借用物品 |
| user_id | INTEGER | FK → user.id, NOT NULL | 借用人 |
| borrow_date | DATETIME | NOT NULL, DEFAULT NOW | 借出时间 |
| due_date | DATE | NOT NULL | 预计归还日期 |
| return_date | DATETIME | | 实际归还时间（NULL = 未还） |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | 状态: active / returned / overdue |
| purpose | VARCHAR(200) | | 借用用途 |
| return_note | VARCHAR(200) | | 归还备注（物品状况） |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

**索引:** `idx_borrow_item`, `idx_borrow_user`, `idx_borrow_status`

### 2.5 scrap_record — 报废记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, 自增 | 主键 |
| item_id | INTEGER | FK → item.id, NOT NULL | 报废物品 |
| applicant_id | INTEGER | FK → user.id, NOT NULL | 申请人 |
| approver_id | INTEGER | FK → user.id | 审批人 |
| reason | TEXT | NOT NULL | 报废原因 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 状态: pending / approved / rejected |
| apply_time | DATETIME | NOT NULL, DEFAULT NOW | 申请时间 |
| approve_time | DATETIME | | 审批时间 |
| approve_note | VARCHAR(200) | | 审批备注 |

**索引:** `idx_scrap_item`, `idx_scrap_status`

---

## 3. 状态枚举值

### 物品状态 (item.status)
- `available` — 可用
- `borrowed` — 已借出
- `pending_scrap` — 待报废（审批中）
- `scrapped` — 已报废

### 借用状态 (borrow_record.status)
- `active` — 借用中
- `returned` — 已归还
- `overdue` — 逾期（由定时任务自动标记）

### 报废状态 (scrap_record.status)
- `pending` — 待审批
- `approved` — 已通过
- `rejected` — 已驳回

---

## 4. 物品编号生成规则

格式: `ITM-{YYYYMMDD}-{4位序号}`

示例: `ITM-20260423-0001`, `ITM-20260423-0002`

每天序号从 0001 开始，通过查询当天最大序号 +1 生成。
