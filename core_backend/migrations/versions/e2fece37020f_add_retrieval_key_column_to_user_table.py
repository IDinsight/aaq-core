"""add retrieval_key column to user table

Revision ID: e2fece37020f
Revises: 55cf4d21158b
Create Date: 2024-04-27 14:00:42.061870

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2fece37020f"
down_revision: Union[str, None] = "55cf4d21158b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("retrieval_key", sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "retrieval_key")
    # ### end Alembic commands ###
