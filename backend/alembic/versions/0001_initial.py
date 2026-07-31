"""Initial database schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='developer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_table(
        'compliance_cards',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('current_version_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_table(
        'card_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('card_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('config_input', sa.JSON(), nullable=True),
        sa.Column('tool_manifest_input', sa.JSON(), nullable=True),
        sa.Column('runtime_trace_input', sa.Text(), nullable=True),
        sa.Column('card_data', sa.JSON(), nullable=False),
        sa.Column('completeness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_classification', sa.String(length=50), nullable=False, server_default='low'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_by_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_table(
        'regulation_mappings',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('version_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('framework', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='non-compliant'),
        sa.Column('details', sa.JSON(), nullable=False)
    )
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_foreign_key('fk_card_user', 'compliance_cards', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_card_version_card', 'card_versions', 'compliance_cards', ['card_id'], ['id'])
    op.create_foreign_key('fk_card_version_user', 'card_versions', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_regulation_version', 'regulation_mappings', 'card_versions', ['version_id'], ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_compliance_cards_current_version_id', 'compliance_cards', ['current_version_id'])


def downgrade() -> None:
    op.drop_index('ix_compliance_cards_current_version_id', table_name='compliance_cards')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('audit_logs')
    op.drop_table('regulation_mappings')
    op.drop_table('card_versions')
    op.drop_table('compliance_cards')
    op.drop_table('users')
