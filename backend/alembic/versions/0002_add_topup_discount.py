"""add topup_discount_percent to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("topup_discount_percent", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "topup_discount_percent")
