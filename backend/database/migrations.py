"""
数据库迁移和初始化
"""

import os
from sqlalchemy import inspect, text

from backend.config import DB_PATH
from backend.database.engine import engine, SessionLocal
from backend.database.models import User, Task, Submission, Rubric
from backend.config import SCORING_DIMENSIONS


def ensure_user_columns():
    """确保 User 表有新字段（college, major）"""
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("users")]
    
    with engine.connect() as conn:
        if "college" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN college VARCHAR(100)"))
            print("✅ 添加列: college")
        else:
            print("ℹ️ college 列已存在")
        
        if "major" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN major VARCHAR(100)"))
            print("✅ 添加列: major")
        else:
            print("ℹ️ major 列已存在")
        
        conn.commit()


def ensure_task_columns():
    """确保 Task 表有新字段"""
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("tasks")]
    
    with engine.connect() as conn:
        if "task_type" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN task_type VARCHAR(20) DEFAULT '任务实践'"))
            print("✅ 添加列: task_type")
        
        if "enabled_indicators" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN enabled_indicators VARCHAR(500) DEFAULT ''"))
            print("✅ 添加列: enabled_indicators")
        
        if "max_submissions" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN max_submissions INTEGER DEFAULT 3"))
            print("✅ 添加列: max_submissions")
        
        if "allow_after_deadline" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN allow_after_deadline INTEGER DEFAULT 0"))
            print("✅ 添加列: allow_after_deadline")
        
        if "attachment_path" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN attachment_path VARCHAR(500)"))
            print("✅ 添加列: attachment_path")
        
        if "attachment_filename" not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN attachment_filename VARCHAR(200)"))
            print("✅ 添加列: attachment_filename")
        
        conn.commit()


def ensure_submission_columns():
    """确保 Submission 表有新列"""
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("submissions")]
    
    with engine.connect() as conn:
        # 维度得分列
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            for suffix, col_type in [("score", "FLOAT"), ("level", "VARCHAR(10)"), ("final_score", "FLOAT")]:
                col_name = f"{suffix}_{key}"
                if col_name not in existing_columns:
                    default = "''" if suffix == "level" else "0"
                    conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {col_name} {col_type} DEFAULT {default}"))
                    print(f"✅ 添加列: {col_name}")
        
        # AI 评分相关字段
        ai_score_fields = [
            ("ai_score_status", "VARCHAR(20)", "'pending'"),
            ("ai_score_error", "TEXT", "NULL"),
            ("ai_score_detail", "TEXT", "NULL")
        ]
        
        for field_name, field_type, default in ai_score_fields:
            if field_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {field_name} {field_type} DEFAULT {default}"))
                print(f"✅ 添加列: {field_name}")
        
        # AI 评分控制字段
        ai_control_fields = [
            ("ai_scored", "BOOLEAN", "0"),
            ("ai_scored_at", "DATETIME", "NULL"),
            ("ai_scored_by", "VARCHAR(50)", "NULL")
        ]
        
        for field_name, field_type, default in ai_control_fields:
            if field_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {field_name} {field_type} DEFAULT {default}"))
                print(f"✅ 添加列: {field_name}")
        
        # 测评报告字段
        report_fields = [
            ("evaluation_report", "TEXT", "NULL"),
            ("report_generated_at", "DATETIME", "NULL")
        ]
        
        for field_name, field_type, default in report_fields:
            if field_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {field_name} {field_type} DEFAULT {default}"))
                print(f"✅ 添加列: {field_name}")
        
        conn.commit()


def migrate_old_score_columns():
    """将旧的5维度评分数据迁移到新4维度"""
    inspector = inspect(engine)
    existing = [col["name"] for col in inspector.get_columns("submissions")]
    
    has_old = any(col in existing for col in ["score_tool", "score_strategy"])
    
    if not has_old:
        return
    
    print("⚠️ 检测到旧版评分数据，尝试迁移...")
    
    with engine.connect() as conn:
        # 获取所有列名
        columns = [col["name"] for col in inspector.get_columns("submissions")]
        
        # 动态构建查询
        select_cols = ["id"]
        if "score_tool" in columns:
            select_cols.append("score_tool")
        if "score_strategy" in columns:
            select_cols.append("score_strategy")
        if "score_critical" in columns:
            select_cols.append("score_critical")
        if "score_ethics" in columns:
            select_cols.append("score_ethics")
        if "score_creative" in columns:
            select_cols.append("score_creative")
        
        query = f"SELECT {', '.join(select_cols)} FROM submissions"
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        for row in rows:
            updates = {}
            
            # 旧 key -> 新 key 映射
            if hasattr(row, 'score_tool') and hasattr(row, 'score_strategy'):
                if row.score_tool is not None and row.score_strategy is not None:
                    updates["score_ai_retrieval"] = (row.score_tool + row.score_strategy) / 2
                elif row.score_tool is not None:
                    updates["score_ai_retrieval"] = row.score_tool
                elif row.score_strategy is not None:
                    updates["score_ai_retrieval"] = row.score_strategy
            
            if hasattr(row, 'score_critical') and row.score_critical is not None:
                updates["score_critical"] = row.score_critical
            
            if hasattr(row, 'score_ethics') and row.score_ethics is not None:
                updates["score_ethics"] = row.score_ethics
            
            if hasattr(row, 'score_creative') and row.score_creative is not None:
                updates["score_integration"] = row.score_creative
            
            if updates:
                set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                updates["id"] = row.id
                conn.execute(text(f"UPDATE submissions SET {set_clause} WHERE id = :id"), updates)
        
        conn.commit()
        print("✅ 旧数据迁移完成")


def add_ai_score_status_column():
    """添加AI评分状态字段（使用SQLAlchemy）"""
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("submissions")]
    
    with engine.connect() as conn:
        if 'ai_score_status' not in existing_columns:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN ai_score_status VARCHAR(20) DEFAULT 'pending'"))
            print("✅ 添加列: ai_score_status")
        else:
            print("ℹ️ ai_score_status 列已存在")
            
        if 'ai_score_error' not in existing_columns:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN ai_score_error TEXT"))
            print("✅ 添加列: ai_score_error")
        else:
            print("ℹ️ ai_score_error 列已存在")
            
        if 'ai_score_detail' not in existing_columns:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN ai_score_detail TEXT"))
            print("✅ 添加列: ai_score_detail")
        else:
            print("ℹ️ ai_score_detail 列已存在")
        
        conn.commit()


def init_db():
    """初始化数据库"""
    from backend.database.engine import Base
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 确保新字段存在
    ensure_user_columns()      # 🆕 添加用户表字段
    ensure_task_columns()
    ensure_submission_columns()
    
    # 迁移旧数据
    migrate_old_score_columns()
    
    # 创建默认账号
    db = SessionLocal()
    try:
        from backend.core.auth import get_password_hash
        
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                password=get_password_hash("admin123"),
                role="teacher",
                display_name="管理员"
            )
            db.add(admin_user)
            
            test_student = User(
                username="2024001",
                password=get_password_hash("123456"),
                role="student",
                display_name="张三"
            )
            db.add(test_student)
            
            db.commit()
            print("✅ 默认账号已创建：admin/admin123（教师）、2024001/123456（学生）")
        else:
            # 确保现有账号密码被正确哈希（如果是明文密码）
            if len(admin.password) < 20:  # 简单判断是否为哈希值
                admin.password = get_password_hash("admin123")
                db.commit()
                print("✅ 已更新admin密码哈希")
        
        # 添加更多测试学生（可选）
        for i in range(2, 6):
            student_username = f"202400{i}"
            student = db.query(User).filter(User.username == student_username).first()
            if not student:
                test_student = User(
                    username=student_username,
                    password=get_password_hash("123456"),
                    role="student",
                    display_name=f"测试学生{i}"
                )
                db.add(test_student)
        db.commit()
        print("✅ 测试学生账号已创建")
        
    except Exception as e:
        print(f"⚠️ 创建默认账号失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("✅ 数据库初始化完成！")


def reset_db():
    """重置数据库（危险操作，仅用于开发）"""
    confirm = input("⚠️ 这将删除所有数据，是否继续？(yes/no): ")
    if confirm.lower() == 'yes':
        from backend.database.engine import Base
        Base.metadata.drop_all(bind=engine)
        print("✅ 所有表已删除")
        init_db()
        print("✅ 数据库已重置")
    else:
        print("操作已取消")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_db()
    else:
        init_db()