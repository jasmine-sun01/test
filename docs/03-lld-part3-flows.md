# LLD Part 3: 业务逻辑流程

## 1. 物品录入流程

```
管理员                    后端                       数据库
  │                       │                          │
  │── POST /api/items ──►│                          │
  │   (name,category...) │                          │
  │                       │── 生成编号 ITM-xxx ─────►│
  │                       │── 生成二维码图片          │
  │                       │   (qrcode库→PNG存盘)     │
  │                       │── INSERT item ──────────►│
  │                       │                          │
  │◄── 物品详情+二维码 ──│                          │
```

编号生成逻辑:
1. 查询今天已有的最大编号: `SELECT MAX(code) FROM item WHERE code LIKE 'ITM-20260423-%'`
2. 序号 +1，补零到4位
3. 若当天无记录，从 0001 开始

---

## 2. 借用流程

```
用户                      后端                       数据库
  │                       │                          │
  │── POST /api/borrows ─►│                          │
  │   (item_id, due_date) │                          │
  │                       │── 查询 item 状态 ───────►│
  │                       │◄── status=available ─────│
  │                       │                          │
  │                       │── 检查用户未还数量 ──────►│
  │                       │◄── count < 10 ───────────│
  │                       │                          │
  │                       │── BEGIN 事务              │
  │                       │── INSERT borrow_record ──►│
  │                       │── UPDATE item             │
  │                       │   status→'borrowed' ────►│
  │                       │── COMMIT                  │
  │                       │                          │
  │◄── 借用成功 ──────────│                          │
```

关键点:
- 事务保证: item 状态更新与 borrow_record 插入在同一事务中
- 并发控制: 通过数据库行锁（SELECT ... FOR UPDATE）防止同一物品被同时借出

---

## 3. 归还流程

```
用户                      后端                       数据库
  │                       │                          │
  │── PUT /borrows/{id}  │                          │
  │   /return            │                          │
  │                       │── 查询 borrow_record ───►│
  │                       │◄── status=active ────────│
  │                       │                          │
  │                       │── 校验: 是本人或管理员    │
  │                       │                          │
  │                       │── BEGIN 事务              │
  │                       │── UPDATE borrow_record    │
  │                       │   status→'returned'      │
  │                       │   return_date→now() ────►│
  │                       │── UPDATE item             │
  │                       │   status→'available' ───►│
  │                       │── COMMIT                  │
  │                       │                          │
  │◄── 归还成功 ──────────│                          │
```

---

## 4. 报废流程

```
申请人                 后端                    数据库                 管理员
  │                    │                       │                      │
  │── POST /scraps ──►│                       │                      │
  │  (item_id,reason) │                       │                      │
  │                    │── 检查物品状态         │                      │
  │                    │── INSERT scrap_record─►│                      │
  │                    │── UPDATE item          │                      │
  │                    │   status→pending_scrap►│                      │
  │◄── 申请已提交 ────│                       │                      │
  │                    │                       │                      │
  │                    │◄─── PUT /scraps/{id}/approve ────────────────│
  │                    │                       │                      │
  │                    │── BEGIN 事务           │                      │
  │                    │── UPDATE scrap_record  │                      │
  │                    │   status→'approved'   │                      │
  │                    │   approver, time ────►│                      │
  │                    │── UPDATE item          │                      │
  │                    │   status→'scrapped' ─►│                      │
  │                    │── COMMIT               │                      │
  │                    │                       │  ──► 审批完成 ────────│
```

特殊情况:
- 物品在「已借出」状态也可发起报废申请，状态变为 `pending_scrap`
- 报废驳回时: 物品状态恢复为 `available`（如当时无人借用）或 `borrowed`（如仍在借中）
- 需要在 scrap_record 中记录申请时的原始物品状态，便于驳回时恢复

---

## 5. 逾期检测（定时任务）

```
定时任务 (每天凌晨1点)           数据库
  │                              │
  │── 查询所有 active 且         │
  │   due_date < 今天的记录 ───►│
  │                              │
  │── 批量 UPDATE                │
  │   status → 'overdue' ──────►│
  │                              │
  │── (可选) 发送提醒通知         │
```

实现方式: 后端启动时注册 APScheduler 定时任务

---

## 6. 关键业务规则汇总

| 规则 | 说明 |
|------|------|
| 借用前检查 | 物品必须为 available 状态 |
| 借用上限 | 单用户未归还不超过 10 件 |
| 借期上限 | 最长 90 天 |
| 归还权限 | 本人或管理员可操作 |
| 报废申请 | available 和 borrowed 状态均可发起 |
| 报废审批 | 仅管理员可操作 |
| 报废不可逆 | scrapped 状态为终态 |
| 逾期标记 | 每天自动扫描，超期标记 overdue |
