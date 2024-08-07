"""add extra api_key columns to user table

Revision ID: 9400641b16d3
Revises: 30549f0b428a
Create Date: 2024-07-18 17:33:08.655320

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9400641b16d3"
down_revision: Union[str, None] = "30549f0b428a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("api_key_first_characters", sa.String(length=5), nullable=True),
    )
    op.add_column(
        "user", sa.Column("api_key_updated_datetime_utc", sa.DateTime(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "api_key_updated_datetime_utc")
    op.drop_column("user", "api_key_first_characters")
    # ### end Alembic commands ###
