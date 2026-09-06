"""create threshold_settings table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "threshold_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("auto_reject_threshold", sa.Integer(), nullable=False),
        sa.Column("auto_approve_threshold", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "threshold_settings",
            sa.Column("id", sa.Integer()),
            sa.Column("auto_reject_threshold", sa.Integer()),
            sa.Column("auto_approve_threshold", sa.Integer()),
        ),
        [
            {
                "id": 1,
                "auto_reject_threshold": 30,
                "auto_approve_threshold": 70,
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("threshold_settings")