"""add generate_llm_response column to query table

Revision ID: e354e0c0aad1
Revises: c6258d82bfd5
Create Date: 2024-07-18 02:26:05.749460

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e354e0c0aad1"
down_revision: Union[str, None] = "c6258d82bfd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "query", sa.Column("query_generate_llm_response", sa.BOOLEAN(), nullable=True)
    )
    # WARNING: The query_generate_llm_response column for ALL previous queries will be
    # set to False even if the user had requested an LLM response (since we don't
    # collect this info yet).
    op.execute("UPDATE query SET query_generate_llm_response = False")
    op.alter_column(
        "query",
        "query_generate_llm_response",
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("query", "query_generate_llm_response")
    # ### end Alembic commands ###