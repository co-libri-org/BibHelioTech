"""empty message

Revision ID: f8b664f24f81
Revises: e3207db7c9b1
Create Date: 2024-09-05 14:52:03.674826

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8b664f24f81'
down_revision = 'e3207db7c9b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hp_event', schema=None) as batch_op:
        batch_op.alter_column('conf_idx',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hp_event', schema=None) as batch_op:
        batch_op.alter_column('conf_idx',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###