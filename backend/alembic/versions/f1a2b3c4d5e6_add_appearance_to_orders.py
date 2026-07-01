"""add appearance to orders

Revision ID: f1a2b3c4d5e6
Revises: e74aced226d5
Create Date: 2026-04-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e74aced226d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('appearance', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'appearance')
