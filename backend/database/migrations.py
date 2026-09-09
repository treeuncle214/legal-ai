"""
数据库迁移和初始化
"""

import os
from sqlalchemy import inspect, text

from backend.config import DB_PATH, DATABASE_URL
from backend.database.engine import engine, SessionLocal
from backend.database.models import User, Task, Submission, Rubric
from backend.config import SCORING_DIMENSIONS

# 判断是否 PostgreSQL
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in existing_columns


def _add_column(table_name: str, column_name: str, column_type: str, default: str = None):
    """通用列添加函数，兼容 SQLite 和 PostgreSQL"""
    if _column_exists(table_name, column_name):
        print(f"ℹ️ {table_name}.{column_name} 列已存在")
        return
    
    with engine.connect() as conn:
        if default is not None:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        conn.execute(text(sql))
        conn.commit()
        print(f"✅ 添加列: {table_name}.{column_name}")


def ensure_user_columns():
    """确保 User 表有新字段（college, major）"""
    _add_column("users", "college", "VARCHAR(100)")
    _add_column("users", "major", "VARCHAR(100)")


def ensure_task_columns():
    """确保 Task 表有新字段"""
    _add_column("tasks", "task_type", "VARCHAR(20)", "'任务实践'")
    _add_column("tasks", "enabled_indicators", "VARCHAR(500)", "''")
    _add_column("tasks", "max_submissions", "INTEGER", "3")
    _add_column("tasks", "allow_after_deadline", "INTEGER", "0")
    _add_column("tasks", "attachment_path", "VARCHAR(500)")
    _add_column("tasks", "attachment_filename", "VARCHAR(200)")
    _add_column("tasks", "weight", "INTEGER", "5")
    _add_column("tasks", "rubric_template_id", "INTEGER")
    _add_column("tasks", "task_rubric_id", "INTEGER")
    _add_column("tasks", "custom_prompt", "TEXT")


def ensure_submission_columns():
    """确保 Submission 表有新列"""
    # 维度得分列
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        _add_column("submissions", f"score_{key}", "FLOAT", "0")
        _add_column("submissions", f"level_{key}", "VARCHAR(10)", "''")
        _add_column("submissions", f"final_score_{key}", "FLOAT", "0")
    
    # AI 评分相关字段
    _add_column("submissions", "ai_score_status", "VARCHAR(20)", "'pending'")
    _add_column("submissions", "ai_score_error", "TEXT")
    _add_column("submissions", "ai_score_detail", "TEXT")
    
    # AI 评分控制字段（用 INTEGER 而非 BOOLEAN，兼容 SQLite 与 PostgreSQL）
    _add_column("submissions", "ai_scored", "INTEGER", "0")
    _add_column("submissions", "ai_scored_at", "TIMESTAMP")
    _add_column("submissions", "ai_scored_by", "VARCHAR(50)")
    
    # 测评报告字段
    _add_column("submissions", "evaluation_report", "TEXT")
    _add_column("submissions", "report_generated_at", "TIMESTAMP")
    
    # 教师审批字段
    _add_column("submissions", "is_reviewed", "INTEGER", "0")
    _add_column("submissions", "teacher_comment", "TEXT")
    _add_column("submissions", "reviewed_by", "VARCHAR(100)")
    _add_column("submissions", "reviewed_at", "TIMESTAMP")
    _add_column("submissions", "score_published", "INTEGER", "0")
    _add_column("submissions", "total_score", "FLOAT", "0")
    
    # 提交内容字段
    _add_column("submissions", "process_log", "TEXT")
    _add_column("submissions", "ai_interaction_log", "TEXT")
    _add_column("submissions", "final_output", "TEXT")
    _add_column("submissions", "tools_used", "TEXT")
    _add_column("submissions", "word_file_path", "VARCHAR(500)")
    _add_column("submissions", "word_content", "TEXT")
    _add_column("submissions", "submit_type", "VARCHAR(20)", "'text'")
    _add_column("submissions", "original_filenames", "TEXT")
    _add_column("submissions", "resubmit_count", "INTEGER", "0")


def ensure_batch_progress_table():
    """确保批量评分进度表存在（跨 worker 共享进度）"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS batch_progress (
                task_id INTEGER PRIMARY KEY,
                progress_data TEXT,
                updated_at TEXT
            )
        """))
        conn.commit()
    print("✅ batch_progress 表已就绪")


def migrate_old_score_columns():
    """将旧的5维度评分数据迁移到新4维度"""
    inspector = inspect(engine)
    existing = [col["name"] for col in inspector.get_columns("submissions")]
    
    has_old = any(col in existing for col in ["score_tool", "score_strategy"])
    
    if not has_old:
        print("ℹ️ 无旧版评分数据需要迁移")
        return
    
    print("⚠️ 检测到旧版评分数据，尝试迁移...")
    
    with engine.connect() as conn:
        columns = [col["name"] for col in inspector.get_columns("submissions")]
        
        select_cols = ["id"]
        for col in ["score_tool", "score_strategy", "score_critical", "score_ethics", "score_creative"]:
            if col in columns:
                select_cols.append(col)
        
        query = f"SELECT {', '.join(select_cols)} FROM submissions"
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        for row in rows:
            updates = {}
            
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
    """添加AI评分状态字段"""
    _add_column("submissions", "ai_score_status", "VARCHAR(20)", "'pending'")
    _add_column("submissions", "ai_score_error", "TEXT")
    _add_column("submissions", "ai_score_detail", "TEXT")


def init_db():
    """初始化数据库"""
    from backend.database.engine import Base
    
    # 确保数据目录存在（仅 SQLite 需要）
    if not IS_POSTGRESQL:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 确保新字段存在
    ensure_user_columns()
    ensure_task_columns()
    ensure_submission_columns()
    ensure_batch_progress_table()

    # 迁移旧数据
    migrate_old_score_columns()

    # 创建默认账号（仅开发/测试环境；生产环境由管理员手工创建账号）
    if os.getenv("ENVIRONMENT", "development") == "production":
        print("⚠️ 生产环境：跳过默认账号/测试账号创建")
        return

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
            db.commit()
            print("✅ 默认账号已创建：admin/admin123（教师）")
        else:
            # 确保现有账号密码被正确哈希
            if len(admin.password) < 20:
                admin.password = get_password_hash("admin123")
                db.commit()
                print("✅ 已更新admin密码哈希")
        
        # 创建测试学生账号
        test_student = db.query(User).filter(User.username == "2024001").first()
        if not test_student:
            student_user = User(
                username="2024001",
                password=get_password_hash("123456"),
                role="student",
                display_name="张三"
            )
            db.add(student_user)
            db.commit()
            print("✅ 测试学生账号已创建：2024001/123456")
        
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