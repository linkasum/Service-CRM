"""add master_id and created_at to order_parts

Revision ID: e74aced226d5
Revises: 001_initial
Create Date: 2026-04-23 00:14:32.854410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e74aced226d5'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order_parts', sa.Column('master_id', sa.Integer(), nullable=True))
    op.add_column('order_parts', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'order_parts_master_id_fkey',
        'order_parts', 'users',
        ['master_id'], ['id']
    )
    # Backfill existing rows with current timestamp
    op.execute("UPDATE order_parts SET created_at = NOW() WHERE created_at IS NULL")


def downgrade() -> None:
    op.drop_constraint('order_parts_master_id_fkey', 'order_parts', type_='foreignkey')
    op.drop_column('order_parts', 'created_at')
    op.drop_column('order_parts', 'master_id')
