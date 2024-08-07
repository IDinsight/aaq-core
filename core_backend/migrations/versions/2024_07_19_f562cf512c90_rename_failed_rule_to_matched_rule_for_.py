"""rename failed_rule to matched_rule for UD

Revision ID: f562cf512c90
Revises: 9400641b16d3
Create Date: 2024-07-17 13:58:29.227622

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f562cf512c90"
down_revision: Union[str, None] = "9400641b16d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        table_name="urgency-response",
        column_name="failed_rules",
        new_column_name="matched_rules",
    )


def downgrade() -> None:
    op.alter_column(
        table_name="urgency-response",
        column_name="matched_rules",
        new_column_name="failed_rules",
    )
