"""Удаляем поле rating

Revision ID: 7c37dbeff975
Revises: aedbe46678af
Create Date: 2021-08-31 17:33:08.600057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c37dbeff975'
down_revision = 'aedbe46678af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'rating')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
