"""create employee_thresholds and drop threshold_settings

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-06 13:00:00.000000

APP-008: пороги автообработки переносятся с синглтона `threshold_settings`
на персональные пороги сотрудников (`employee_thresholds`). Данные прежней
строки-синглтона (id=1) переносятся как дефолтные значения в записи всех
существующих сотрудников, после чего старая таблица удаляется.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "employee_thresholds",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("auto_reject_threshold", sa.Integer(), nullable=False),
        sa.Column("auto_approve_threshold", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    bind = op.get_bind()

    # Переносим значения прежней строки-синглтона (id=1); если её нет —
    # используем дефолты 30/70 (те же, что сидировала миграция 0004).
    old = bind.execute(
        sa.text(
            "SELECT auto_reject_threshold, auto_approve_threshold "
            "FROM threshold_settings WHERE id = 1"
        )
    ).first()
    reject, approve = (old if old else (30, 70))
    if reject is None or approve is None:
        reject, approve = 30, 70

    employee_ids = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT id FROM users WHERE role = 'employee'")
        )
    ]
    for employee_id in employee_ids:
        bind.execute(
            sa.text(
                "INSERT INTO employee_thresholds "
                "(user_id, auto_reject_threshold, auto_approve_threshold) "
                "VALUES (:uid, :reject, :approve)"
            ),
            {"uid": employee_id, "reject": reject, "approve": approve},
        )

    op.drop_table("threshold_settings")


def downgrade() -> None:
    """Downgrade schema."""
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
    op.drop_table("employee_thresholds")
