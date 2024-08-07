"""add content shared count

Revision ID: 4d3f01bf891f
Revises: 28861161249b
Create Date: 2024-07-05 00:47:47.155062

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d3f01bf891f"
down_revision: Union[str, None] = "28861161249b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("content", sa.Column("query_count", sa.Integer(), nullable=True))
    op.execute("UPDATE content SET query_count = 0")  # for existing rows
    op.alter_column("content", "query_count", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("content", "query_count")
    # ### end Alembic commands ###
