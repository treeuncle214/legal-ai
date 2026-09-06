"""baseline: 以当前 ORM 模型为基线建立版本

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-05

这是项目的首个 Alembic 基线迁移。它使用 SQLAlchemy 元数据创建所有表，
用于给（新建或既有）数据库打上版本号；后续的结构变更通过新增迁移脚本管理。

生产环境首次接入说明：
- 如果是全新数据库：直接执行 `alembic upgrade head` 即可建表。
- 如果数据库已由旧的 init_db（Base.metadata.create_all）创建：
  请执行 `alembic stamp 0001_baseline` 标记基线，避免重复建表。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.database.engine import Base  # noqa: F401
import backend.database.models  # noqa: F401  确保所有模型已注册到 Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
