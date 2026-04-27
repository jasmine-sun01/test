"""清理物品表并插入完整的多分类测试数据"""
import hashlib
from datetime import date, datetime
from database import init_db, SessionLocal
from models import User, Category, Item, BorrowRecord, ScrapRecord
from services.qrcode_service import generate_qrcode


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def run():
    db = SessionLocal()
    try:
        # ========== 1. 清理旧数据 ==========
        db.query(ScrapRecord).delete()
        db.query(BorrowRecord).delete()
        db.query(Item).delete()
        db.query(Category).delete()
        db.query(User).delete()
        db.commit()
        print("✓ 已清理所有旧数据")

        # ========== 2. 重建用户 ==========
        users = [
            ("admin", "admin123", "系统管理员", "admin", "13800000000"),
            ("teacher1", "teacher1", "张老师", "staff", "13811111111"),
            ("teacher2", "teacher2", "王老师", "staff", "13822222222"),
            ("student1", "student1", "李同学", "student", "13900000001"),
            ("student2", "student2", "赵同学", "student", "13900000002"),
            ("student3", "student3", "陈同学", "student", "13900000003"),
        ]
        user_map = {}
        for uname, pwd, rname, role, phone in users:
            u = User(username=uname, password_hash=hash_password(pwd),
                     real_name=rname, role=role, phone=phone)
            db.add(u)
            db.flush()
            user_map[uname] = u.id
            print(f"  ✓ 用户: {uname} / {pwd} ({role})")

        # ========== 3. 重建分类 ==========
        categories_data = [
            ("电子设备", "电脑、投影仪、平板等"),
            ("体育器材", "篮球、足球、羽毛球拍等"),
            ("实验器材", "显微镜、烧杯、万用表等"),
            ("办公用品", "打印机、订书机、白板等"),
            ("图书", "教材、参考书、期刊等"),
            ("教学器材", "教具、模型、挂图等"),
            ("乐器", "钢琴、吉他、小提琴等"),
            ("家具", "课桌、椅子、书柜等"),
        ]
        cat_map = {}
        for name, desc in categories_data:
            c = Category(name=name, description=desc)
            db.add(c)
            db.flush()
            cat_map[name] = c.id
            print(f"  ✓ 分类: {name}")

        # ========== 4. 插入测试物品 ==========
        seq = 0

        def make_code():
            nonlocal seq
            seq += 1
            return f"ITM-20260424-{seq:04d}"

        items_data = [
            # --- 电子设备 ---
            ("EPSON CB-X06 投影仪", "电子设备", "EPSON CB-X06", "2023-09-01", 3599.00, "教学楼A栋 301室", "3600流明，XGA分辨率，含遥控器"),
            ("联想ThinkPad E14 笔记本", "电子设备", "ThinkPad E14 Gen5", "2024-03-15", 4299.00, "计算机实验室 201室", "i5-13500H/16G/512G，教师办公用"),
            ("iPad Air (第5代)", "电子设备", "iPad Air M1 64GB", "2024-06-01", 4399.00, "信息中心 105室", "教学演示用，含Apple Pencil"),
            ("Dell P2422H 显示器", "电子设备", "P2422H 24寸", "2023-06-15", 1299.00, "办公楼 302室", "IPS面板，旋转升降支架"),
            ("佳能PIXMA G3810打印机", "电子设备", "Canon G3810", "2024-01-10", 999.00, "教务处 101室", "彩色喷墨，无线打印"),

            # --- 体育器材 ---
            ("摩腾GG7X 篮球", "体育器材", "Molten GG7X", "2024-04-15", 189.00, "体育器材室", "比赛用球，共10个"),
            ("红双喜DHS 乒乓球拍", "体育器材", "DHS 6星横拍", "2024-02-20", 299.00, "体育器材室", "套装含3个球"),
            ("尤尼克斯羽毛球拍", "体育器材", "YONEX ARC-7", "2023-11-08", 459.00, "体育器材室", "全碳素，含拍包"),
            ("跳绳（计数款）", "体育器材", "Li-Ning AQAH182", "2024-03-01", 39.00, "体育器材室", "电子计数，钢丝绳，共20根"),
            ("足球（5号）", "体育器材", "STAR SB515", "2024-05-10", 129.00, "体育器材室", "PU材质比赛球，共8个"),

            # --- 实验器材 ---
            ("生物显微镜", "实验器材", "Olympus CX23", "2022-09-01", 6800.00, "生物实验室 401室", "双目，40X-1000X"),
            ("数字万用表", "实验器材", "Fluke 15B+", "2023-03-20", 580.00, "物理实验室 302室", "自动量程，共15台"),
            ("电子天平", "实验器材", "梅特勒 ME204", "2023-06-15", 4200.00, "化学实验室 501室", "0.1mg精度，220g量程"),
            ("示波器", "实验器材", "Rigol DS1054Z", "2022-12-10", 2800.00, "电子实验室 203室", "50MHz 4通道"),

            # --- 办公用品 ---
            ("得力碎纸机", "办公用品", "Deli 9939", "2024-01-20", 699.00, "行政办公室 201室", "4级保密，15张/次"),
            ("白板（磁性）", "办公用品", "120x90cm 双面", "2023-09-01", 189.00, "会议室 A301", "含白板笔和磁扣套装"),
            ("考勤机", "办公用品", "中控 ZKTeco K40", "2024-02-01", 399.00, "校门口门卫室", "指纹+刷卡，容量3000人"),

            # --- 图书 ---
            ("高等数学（第七版）上册", "图书", "ISBN 978-7-04-039663-8", "2024-03-15", 34.90, "图书馆 A区 3层 12架", "同济大学版，共50本"),
            ("Python编程：从入门到实践（第3版）", "图书", "ISBN 978-7-115-57614-2", "2024-06-01", 89.80, "图书馆 B区 2层 05架", "人民邮电出版社"),
            ("新概念英语（第二册）", "图书", "ISBN 978-7-5600-1346-1", "2023-09-10", 29.90, "图书馆 A区 1层 08架", "外研社，教学用书，共30本"),
            ("大学物理实验", "图书", "ISBN 978-7-04-052834-4", "2024-02-28", 39.80, "图书馆 A区 3层 15架", "高等教育出版社"),
            ("数据结构（C语言版）", "图书", "ISBN 978-7-302-33064-6", "2023-08-15", 49.00, "图书馆 B区 2层 03架", "严蔚敏著，清华大学出版社"),

            # --- 教学器材 ---
            ("人体骨骼模型", "教学器材", "170cm全身骨架", "2022-06-01", 1280.00, "生物教研室 501室", "医用级PVC材质"),
            ("地球仪（大号）", "教学器材", "32cm带灯光", "2023-09-01", 158.00, "地理教研室 302室", "中英文标注，LED底灯"),
            ("三角板教学套装", "教学器材", "60cm磁性", "2024-01-15", 89.00, "教学楼B栋 数学组", "含直尺、三角板、量角器"),

            # --- 乐器 ---
            ("雅马哈电钢琴", "乐器", "Yamaha P-145", "2024-01-10", 3299.00, "音乐教室 601室", "88键重锤，含X架和踏板"),
            ("古典吉他", "乐器", "Yamaha C40", "2023-09-15", 699.00, "音乐教室 601室", "39寸入门款，共5把"),
            ("竖笛（高音）", "乐器", "AULOS 204A", "2024-03-01", 68.00, "音乐教室 601室", "日本产，ABS树脂，共30支"),

            # --- 家具 ---
            ("学生课桌椅套装", "家具", "标准型 60x40cm", "2023-07-01", 280.00, "教学楼C栋 仓库", "钢木结构，可调高度，共200套"),
            ("教师办公桌", "家具", "1.4m L型转角", "2024-01-20", 1580.00, "办公楼 305室", "含抽屉柜和键盘托"),
        ]

        for name, cat_name, model, pdate, price, loc, remark in items_data:
            item = Item(
                code=make_code(),
                name=name,
                category_id=cat_map[cat_name],
                model=model,
                status="available",
                purchase_date=date.fromisoformat(pdate),
                purchase_price=price,
                location=loc,
                remark=remark,
            )
            db.add(item)
            db.flush()
            # 生成二维码
            qr_path = generate_qrcode(item.id, item.code)
            item.qrcode_path = qr_path
            print(f"  ✓ 物品: [{cat_name}] {name} → {item.code}")

        db.commit()
        print(f"\n=== 完成！共插入 {len(users)} 个用户、{len(categories_data)} 个分类、{len(items_data)} 个物品 ===")

    finally:
        db.close()


if __name__ == "__main__":
    print("=== 清理并重建测试数据 ===\n")
    init_db()
    run()
