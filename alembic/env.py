"""Alembic 迁移环境配置

从 backend.database.engine 读取应用实际连接的数据库地址，
自动兼容 SQLite（开发）与 PostgreSQL（生产）。
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 确保项目根目录在 sys.path 中，便于导入 backend 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入 engine 会触发 backend.database 包初始化，从而注册所有模型到 Base.metadata
from backend.database.engine import Base, engine  # noqa: E402

config = context.config

# 使用应用实际连接的数据库地址（含密码），确保迁移作用于正确的库
config.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：仅生成 SQL，不连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库并执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
