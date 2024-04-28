"""Create UD tables

Revision ID: e08196283751
Revises: e8ddc3de6210
Create Date: 2024-04-28 10:17:08.744169

"""

from typing import Sequence, Union

import pgvector
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e08196283751"
down_revision: Union[str, None] = "e8ddc3de6210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "urgency-queries",
        sa.Column("urgency_query_id", sa.Integer(), nullable=False),
        sa.Column("message_text", sa.String(), nullable=False),
        sa.Column("message_datetime_utc", sa.DateTime(), nullable=False),
        sa.Column("feedback_secret_key", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("urgency_query_id"),
    )
    op.create_index(
        op.f("ix_urgency-queries_urgency_query_id"),
        "urgency-queries",
        ["urgency_query_id"],
        unique=False,
    )
    op.create_table(
        "urgency~rules",
        sa.Column("urgency_rule_id", sa.Integer(), nullable=False),
        sa.Column("urgency_rule_text", sa.String(), nullable=False),
        sa.Column(
            "urgency_rule_vector", pgvector.sqlalchemy.Vector(dim=1536), nullable=False
        ),
        sa.Column("urgency_rule_metadata", sa.JSON(), nullable=True),
        sa.Column("created_datetime_utc", sa.DateTime(), nullable=False),
        sa.Column("updated_datetime_utc", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("urgency_rule_id"),
    )
    op.create_table(
        "urgency~responses",
        sa.Column("urgency_response_id", sa.Integer(), nullable=False),
        sa.Column("is_urgent", sa.Boolean(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("query_id", sa.Integer(), nullable=False),
        sa.Column("response_datetime_utc", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["query_id"],
            ["urgency-queries.urgency_query_id"],
        ),
        sa.PrimaryKeyConstraint("urgency_response_id"),
    )
    op.create_index(
        op.f("ix_urgency~responses_urgency_response_id"),
        "urgency~responses",
        ["urgency_response_id"],
        unique=False,
    )
    op.drop_index(
        "content_idx",
        table_name="content",
        postgresql_with={"m": "16", "ef_construction": "64"},
        postgresql_using="hnsw",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        "content_idx",
        "content",
        ["content_embedding"],
        unique=False,
        postgresql_with={"m": "16", "ef_construction": "64"},
        postgresql_using="hnsw",
    )
    op.drop_index(
        op.f("ix_urgency~responses_urgency_response_id"), table_name="urgency~responses"
    )
    op.drop_table("urgency~responses")
    op.drop_table("urgency~rules")
    op.drop_index(
        op.f("ix_urgency-queries_urgency_query_id"), table_name="urgency-queries"
    )
    op.drop_table("urgency-queries")
    # ### end Alembic commands ###