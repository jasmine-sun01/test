# LLD Part 2: API 接口详细设计

## 1. 通用约定

- Base URL: `http://localhost:8000/api`
- 认证: 用户名+密码登录后，服务端创建 Session，通过 Cookie 自动携带，无需手动传 Token
- 分页参数: `page` (默认1), `page_size` (默认20, 最大100)
- 响应格式统一:

```json
// 成功
{ "code": 0, "data": {...}, "msg": "ok" }

// 列表
{ "code": 0, "data": { "items": [...], "total": 100, "page": 1, "page_size": 20 }, "msg": "ok" }

// 错误
{ "code": 40001, "data": null, "msg": "物品不存在" }
```

---

## 2. 错误码定义

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 40001 | 资源不存在 |
| 40002 | 参数校验失败 |
| 40003 | 物品状态不允许该操作 |
| 40004 | 重复操作（如重复借用） |
| 40101 | 未登录 / Token 过期 |
| 40301 | 权限不足 |
| 50001 | 服务器内部错误 |

---

## 3. 认证接口

### POST /api/auth/login

请求:
```json
{ "username": "zhangsan", "password": "123456" }
```

响应: Set-Cookie 头设置 session_id，返回用户信息
```json
{
  "code": 0,
  "data": { "id": 1, "username": "zhangsan", "real_name": "张三", "role": "staff" }
}
```

### POST /api/auth/logout
清除 Session，返回成功

### GET /api/auth/me
响应: 当前登录用户信息（未登录返回 40101）

---

## 4. 物品接口

### POST /api/items — 录入物品 (Admin)

请求:
```json
{
  "name": "投影仪",
  "category_id": 1,
  "model": "EPSON CB-X06",
  "purchase_date": "2026-01-15",
  "purchase_price": 3500.00,
  "location": "教学楼A栋 301室",
  "remark": "含遥控器和VGA线"
}
```

响应: 完整物品对象（含自动生成的 code 和 qrcode_path）

### GET /api/items — 物品列表

查询参数: `keyword`, `category_id`, `status`, `page`, `page_size`

### GET /api/items/{id} — 物品详情

响应含: 基本信息 + 当前借用信息（如有） + 最近5条借用历史

### GET /api/items/{id}/qrcode — 获取二维码

响应: PNG 图片 (Content-Type: image/png)

### POST /api/items/qrcode-pdf — 批量二维码 PDF (Admin)

请求:
```json
{ "item_ids": [1, 2, 3, 5, 8] }
```

响应: PDF 文件流

### POST /api/items/import — CSV 批量导入 (Admin)

请求: multipart/form-data, 字段 `file` (CSV文件)

CSV 格式: `名称,分类,型号,购入日期,价格,位置,备注`

---

## 5. 借用接口

### POST /api/borrows — 发起借用

请求:
```json
{
  "item_id": 1,
  "due_date": "2026-05-10",
  "purpose": "课堂教学使用"
}
```

校验规则:
- 物品状态必须为 `available`
- `due_date` 不得早于今天，不得超过90天
- 同一用户未归还数量不超过10件

### PUT /api/borrows/{id}/return — 归还

请求:
```json
{ "return_note": "完好无损" }
```

校验: 只能归还自己的借用记录，或管理员代归还

### GET /api/borrows/my — 我的借用

查询参数: `status` (active/returned/overdue), `page`, `page_size`

### GET /api/borrows/overdue — 逾期列表 (Admin)

返回所有逾期未还记录

---

## 6. 报废接口

### POST /api/scraps — 发起报废申请

请求:
```json
{
  "item_id": 1,
  "reason": "屏幕损坏，无法维修"
}
```

校验: 物品状态不能为 `scrapped`；已有待审批的报废申请不可重复提交

### PUT /api/scraps/{id}/approve — 审批通过 (Admin)

请求:
```json
{ "approve_note": "确认报废" }
```

副作用: 物品状态 → `scrapped`

### PUT /api/scraps/{id}/reject — 审批驳回 (Admin)

请求:
```json
{ "approve_note": "建议先维修" }
```

副作用: 物品状态恢复为之前状态

---

## 7. 仪表盘接口

### GET /api/dashboard/stats

响应:
```json
{
  "code": 0,
  "data": {
    "total_items": 520,
    "available_count": 380,
    "borrowed_count": 105,
    "overdue_count": 12,
    "scrapped_count": 23
  }
}
```

### GET /api/dashboard/top-borrowed?limit=10

响应: 借用次数 Top N 物品列表
