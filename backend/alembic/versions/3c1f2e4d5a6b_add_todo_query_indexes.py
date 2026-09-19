"""add indexes for user-scoped todo queries

Revision ID: 3c1f2e4d5a6b
Revises: a0790c76a129
Create Date: 2026-09-19 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "3c1f2e4d5a6b"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CONCURRENTLY prevents long writes from being blocked on a large production table.
    # Alembic must leave its transaction before PostgreSQL accepts this statement.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_todos_user_created_at_id",
            "todos",
            ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
            unique=False,
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_todos_user_completed_created_at_id",
            "todos",
            [
                "user_id",
                "completed",
                sa.text("created_at DESC"),
                sa.text("id DESC"),
            ],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_todos_user_completed_created_at_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_todos_user_created_at_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
