"""add tags, todo-tag mapping, and filtered todo index

Revision ID: b4e7c8d9f012
Revises: 3c1f2e4d5a6b
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b4e7c8d9f012"
down_revision = "3c1f2e4d5a6b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "todo_tags",
        sa.Column("todo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])
    op.create_index("uq_tags_user_lower_name", "tags", ["user_id", sa.text("lower(name)")], unique=True)
    op.create_index("ix_todo_tags_todo_id", "todo_tags", ["todo_id"])
    op.create_index("ix_todo_tags_tag_id", "todo_tags", ["tag_id"])
    op.create_index("ix_todos_user_completed_created_at", "todos", ["user_id", "completed", sa.text("created_at DESC")])


def downgrade():
    op.drop_index("ix_todos_user_completed_created_at", table_name="todos")
    op.drop_table("todo_tags")
    op.drop_table("tags")
