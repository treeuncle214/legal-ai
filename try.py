# migrate_classes.py
"""
数据库迁移：添加班级功能
执行方式：python migrate_classes.py
"""

import sqlite3
import os

DB_PATH = "data/assessment.db"

def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def run_migration():
    """执行迁移"""
    print("=" * 50)
    print("开始执行数据库迁移...")
    print("=" * 50)

    # 1. 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        print("请先启动后端程序创建数据库")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ==================== 创建班级表 ====================
        print("\n1. 创建 classes 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                teacher_id INTEGER NOT NULL,
                course_id INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        """)
        print("   ✅ classes 表创建成功")

        # ==================== 创建学生-班级关联表 ====================
        print("\n2. 创建 user_class 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_class (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (class_id) REFERENCES classes(id),
                UNIQUE(user_id, class_id)
            )
        """)
        print("   ✅ user_class 表创建成功")

        # ==================== 修改 tasks 表 ====================
        print("\n3. 修改 tasks 表（添加 class_id 和 course_id）...")
        
        # 检查 tasks 表是否已有 class_id 列
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'class_id' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN class_id INTEGER DEFAULT NULL")
            print("   ✅ 添加 class_id 列")
        else:
            print("   ℹ️ class_id 列已存在")
        
        if 'course_id' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN course_id INTEGER DEFAULT NULL")
            print("   ✅ 添加 course_id 列")
        else:
            print("   ℹ️ course_id 列已存在")

        # ==================== 创建索引（优化查询性能） ====================
        print("\n4. 创建索引...")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_classes_teacher_id ON classes(teacher_id)")
        print("   ✅ idx_classes_teacher_id 索引创建成功")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_class_user_id ON user_class(user_id)")
        print("   ✅ idx_user_class_user_id 索引创建成功")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_class_class_id ON user_class(class_id)")
        print("   ✅ idx_user_class_class_id 索引创建成功")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_class_id ON tasks(class_id)")
        print("   ✅ idx_tasks_class_id 索引创建成功")

        # ==================== 提交 ====================
        conn.commit()
        
        print("\n" + "=" * 50)
        print("✅ 迁移执行成功！")
        print("=" * 50)
        
        # 打印迁移后的表结构
        print("\n📋 当前数据库表结构：")
        
        for table in ['classes', 'user_class', 'tasks']:
            print(f"\n--- {table} 表 ---")
            cursor.execute(f"PRAGMA table_info({table})")
            for col in cursor.fetchall():
                print(f"  {col[1]}: {col[2]} (默认: {col[4]})")
        
        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def rollback():
    """回滚迁移（删除新增的表和字段）"""
    print("=" * 50)
    print("⚠️ 警告：这将删除 classes 表和 user_class 表！")
    print("=" * 50)
    
    confirm = input("确认执行回滚？(yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\n开始回滚...")
        
        # 删除表
        cursor.execute("DROP TABLE IF EXISTS user_class")
        print("   ✅ 删除 user_class 表")
        
        cursor.execute("DROP TABLE IF EXISTS classes")
        print("   ✅ 删除 classes 表")
        
        # 注意：不能直接删除 tasks 的列，SQLite 不支持 DROP COLUMN
        # 如需删除列，需要重建表，此处不做处理
        
        conn.commit()
        print("\n✅ 回滚完成")
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        run_migration()