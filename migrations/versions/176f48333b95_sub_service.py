"""sub-service

Revision ID: 176f48333b95
Revises: eddb65123f65
Create Date: 2025-02-14 17:52:03.045763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '176f48333b95'
down_revision: Union[str, None] = 'eddb65123f65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bookings', sa.Column('sub_services', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bookings', 'sub_services')
    # ### end Alembic commands ###
