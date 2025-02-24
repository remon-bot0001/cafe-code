"""Initial migration

Revision ID: a5c6ad8ca391
Revises: 
Create Date: 2025-02-18 16:23:04.901489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5c6ad8ca391'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        # ここでroleカラムにデフォルト値「user」を設定
        batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False, server_default='user'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        # roleカラムを削除
        batch_op.drop_column('role')

    # ### end Alembic commands ###
