"""初始化数据库：建表 + 插入默认数据"""
import hashlib
from database import init_db, SessionLocal
from models import User, Category


def hash_password(password: str) -> str:
    """简单密码哈希（SHA256），生产环境建议用 bcrypt"""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data():
    """插入默认管理员和常用分类"""
    db = SessionLocal()
    try:
        # 默认管理员（如果不存在）
        if not db.query(User).filter_by(username="admin").first():
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                real_name="系统管理员",
                role="admin",
            )
            db.add(admin)
            print("  ✓ 创建默认管理员: admin / admin123")

        # 测试用户
        test_users = [
            ("teacher1", "teacher1", "张老师", "staff"),
            ("student1", "student1", "李同学", "student"),
        ]
        for uname, pwd, rname, role in test_users:
            if not db.query(User).filter_by(username=uname).first():
                db.add(User(
                    username=uname,
                    password_hash=hash_password(pwd),
                    real_name=rname,
                    role=role,
                ))
                print(f"  ✓ 创建测试用户: {uname} / {pwd} ({role})")

        # 默认分类
        default_categories = [
            ("电子设备", "电脑、投影仪、平板等"),
            ("体育器材", "篮球、足球、羽毛球拍等"),
            ("实验器材", "显微镜、烧杯、万用表等"),
            ("办公用品", "打印机、订书机、白板等"),
            ("图书", "教材、参考书、期刊等"),
            ("教学器材", "教具、模型、挂图等"),
        ]
        for name, desc in default_categories:
            if not db.query(Category).filter_by(name=name).first():
                db.add(Category(name=name, description=desc))
                print(f"  ✓ 创建分类: {name}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    print("=== 初始化数据库 ===")
    print("1. 建表...")
    init_db()
    print("  ✓ 所有表创建完成")
    print("2. 插入默认数据...")
    seed_data()
    print("=== 初始化完成 ===")
