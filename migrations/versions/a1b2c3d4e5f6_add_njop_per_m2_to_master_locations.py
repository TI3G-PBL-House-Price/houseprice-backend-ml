"""Add njop_per_m2 to master_locations

Revision ID: a1b2c3d4e5f6
Revises: e70def023971
Create Date: 2026-11-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e70def023971'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('master_locations', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'njop_per_m2',
                sa.Numeric(precision=18, scale=2),
                nullable=True,
                comment='Median NJOP per m2 (Rupiah) berdasarkan data NJOP Jakarta'
            )
        )


def downgrade():
    with op.batch_alter_table('master_locations', schema=None) as batch_op:
        batch_op.drop_column('njop_per_m2')
