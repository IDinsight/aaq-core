"""add user_id to required tables

Revision ID: 3228425eb430
Revises: 6cc60b6a8f1d
Create Date: 2024-05-06 20:50:16.810876

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3228425eb430"
down_revision: Union[str, None] = "6cc60b6a8f1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content", sa.Column("user_id", sa.String(), nullable=False))
    op.create_foreign_key(
        "fk_content_user", "content", "user", ["user_id"], ["user_id"]
    )
    op.add_column("query", sa.Column("user_id", sa.String(), nullable=False))
    op.create_foreign_key("fk_query_user", "query", "user", ["user_id"], ["user_id"])
    op.add_column("urgency-query", sa.Column("user_id", sa.String(), nullable=False))
    op.create_foreign_key(
        "fk_urgency_query_user", "urgency-query", "user", ["user_id"], ["user_id"]
    )
    op.add_column("urgency-rule", sa.Column("user_id", sa.String(), nullable=False))
    op.create_foreign_key(
        "fk_urgency_rule_user", "urgency-rule", "user", ["user_id"], ["user_id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_urgency_rule_user", "urgency-rule", type_="foreignkey")
    op.drop_column("urgency-rule", "user_id")
    op.drop_constraint("fk_urgency_query_user", "urgency-query", type_="foreignkey")
    op.drop_column("urgency-query", "user_id")
    op.drop_constraint("fk_query_user", "query", type_="foreignkey")
    op.drop_column("query", "user_id")
    op.drop_constraint("fk_content_user", "content", type_="foreignkey")
    op.drop_column("content", "user_id")
    # ### end Alembic commands ###
