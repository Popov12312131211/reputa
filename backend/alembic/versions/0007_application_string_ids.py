"""switch applications.id (and score_results.application_id) to string ids

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-06 14:00:00.000000

INFRA-004: ID заявки — не автоинкремент, а первые 10-12 символов sha256-хеша
(см. generate_application_id в app/models/application.py). Числовой integer-PK
не совместим с этим форматом, поэтому тип меняется на String(12).

Решение по существующим данным: этап активной разработки, в БД только
тестовые/демо-заявки с числовыми ID, которые не жалко потерять. Поэтому
таблицы score_results и applications пересоздаются (drop + create) в новом
виде, без миграции старых строк. Сначала удаляется score_results (у неё
внешний ключ на applications), затем applications, после чего обе таблицы
создаются заново с новыми типами ключей.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APPLICATION_ID_LENGTH = 12


def upgrade() -> None:
    """Upgrade schema."""
    # score_results ссылается на applications.id — сначала удаляем её.
    op.drop_index(op.f("ix_score_results_application_id"), table_name="score_results")
    op.drop_table("score_results")
    op.drop_table("applications")

    # Создаём applications заново — id теперь строковый (varchar(12)).
    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=APPLICATION_ID_LENGTH), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("purpose", sa.String(length=1024), nullable=False),
        sa.Column("telegram", sa.String(length=255), nullable=False),
        sa.Column("telegram_channel", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_queue"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)
    op.create_index(op.f("ix_applications_decided_by"), "applications", ["decided_by"], unique=False)

    # Создаём score_results заново — application_id теперь varchar(12), тот же FK.
    op.create_table(
        "score_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.String(length=APPLICATION_ID_LENGTH), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("positive_signals", sa.JSON(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=False),
        sa.Column("stability_score", sa.Integer(), nullable=False),
        sa.Column("financial_literacy_score", sa.Integer(), nullable=False),
        sa.Column("responsibility_score", sa.Integer(), nullable=False),
        sa.Column("report_content", sa.Text(), nullable=False),
        sa.Column("report_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_score_results_application_id"), "score_results", ["application_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_score_results_application_id"), table_name="score_results")
    op.drop_table("score_results")
    op.drop_table("applications")

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("purpose", sa.String(length=1024), nullable=False),
        sa.Column("telegram", sa.String(length=255), nullable=False),
        sa.Column("telegram_channel", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_queue"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)
    op.create_index(op.f("ix_applications_decided_by"), "applications", ["decided_by"], unique=False)

    op.create_table(
        "score_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("positive_signals", sa.JSON(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=False),
        sa.Column("stability_score", sa.Integer(), nullable=False),
        sa.Column("financial_literacy_score", sa.Integer(), nullable=False),
        sa.Column("responsibility_score", sa.Integer(), nullable=False),
        sa.Column("report_content", sa.Text(), nullable=False),
        sa.Column("report_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_score_results_application_id"), "score_results", ["application_id"], unique=False)