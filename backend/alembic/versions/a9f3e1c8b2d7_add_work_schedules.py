"""add work schedules

Revision ID: a9f3e1c8b2d7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9f3e1c8b2d7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'work_schedules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_work_schedules_user_id', 'work_schedules', ['user_id'])
    op.create_index('ix_work_schedules_date', 'work_schedules', ['date'])
    op.create_unique_constraint('uq_work_schedules_user_date', 'work_schedules', ['user_id', 'date'])


def downgrade() -> None:
    op.drop_table('work_schedules')
