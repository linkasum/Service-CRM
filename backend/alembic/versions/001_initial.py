"""Alembic script template"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание всех таблиц"""
    
    # Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('permissions', sa.JSON(), nullable=True, default=list),
        sa.Column('description', sa.String(length=500), nullable=True),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id')),
        sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_telegram_chat_id', 'users', ['telegram_chat_id'])
    
    # Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('client_name', sa.String(length=200), nullable=False),
        sa.Column('client_phone', sa.String(length=20), nullable=False),
        sa.Column('device_model', sa.String(length=300), nullable=False),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('complaint', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
        sa.Column('master_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('acceptor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ready_at', sa.DateTime(), nullable=True),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('parts_cost', sa.Float(), nullable=False, server_default='0'),
        sa.Column('work_cost', sa.Float(), nullable=False, server_default='0'),
        sa.Column('diagnostic_act_text', sa.Text(), nullable=True),
        sa.Column('warranty_days', sa.Integer(), nullable=True),
        sa.Column('warranty_until', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_orders_client_name', 'orders', ['client_name'])
    op.create_index('ix_orders_client_phone', 'orders', ['client_phone'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])
    
    # Parts
    op.create_table(
        'parts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=300), nullable=False),
        sa.Column('article', sa.String(length=100), nullable=False, unique=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('sale_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_parts_name', 'parts', ['name'])
    op.create_index('ix_parts_article', 'parts', ['article'])
    
    # Order Parts (many-to-many)
    op.create_table(
        'order_parts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('part_id', sa.Integer(), sa.ForeignKey('parts.id'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_at_order', sa.Float(), nullable=False, server_default='0'),
    )
    
    # Salary Configs
    op.create_table(
        'salary_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('formula_string', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Salary Records
    op.create_table(
        'salary_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('calculated_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='accrued'),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_salary_records_user_id', 'salary_records', ['user_id'])
    op.create_index('ix_salary_records_period_start', 'salary_records', ['period_start'])
    op.create_index('ix_salary_records_period_end', 'salary_records', ['period_end'])
    
    # Notification Tasks
    op.create_table(
        'notification_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('client_phone', sa.String(length=20), nullable=True),
        sa.Column('chat_id', sa.BigInteger(), nullable=True),
        sa.Column('message_text', sa.String(length=2000), nullable=False),
        sa.Column('send_at', sa.DateTime(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_notification_tasks_send_at', 'notification_tasks', ['send_at'])
    
    # Document Templates
    op.create_table(
        'document_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(length=50), nullable=False, unique=True),
        sa.Column('content_template', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_document_templates_type', 'document_templates', ['type'])
    
    # Company Settings
    op.create_table(
        'company_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_name', sa.String(length=300), nullable=False, server_default='Сервисный центр'),
        sa.Column('inn', sa.String(length=12), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('logo_path', sa.String(length=500), nullable=True),
        sa.Column('review_link', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Удаление всех таблиц"""
    op.drop_table('company_settings')
    op.drop_table('document_templates')
    op.drop_table('notification_tasks')
    op.drop_index('ix_salary_records_period_end', table_name='salary_records')
    op.drop_index('ix_salary_records_period_start', table_name='salary_records')
    op.drop_index('ix_salary_records_user_id', table_name='salary_records')
    op.drop_table('salary_records')
    op.drop_table('salary_configs')
    op.drop_table('order_parts')
    op.drop_index('ix_parts_article', table_name='parts')
    op.drop_index('ix_parts_name', table_name='parts')
    op.drop_table('parts')
    op.drop_index('ix_orders_created_at', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_client_phone', table_name='orders')
    op.drop_index('ix_orders_client_name', table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_users_telegram_chat_id', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_table('roles')
