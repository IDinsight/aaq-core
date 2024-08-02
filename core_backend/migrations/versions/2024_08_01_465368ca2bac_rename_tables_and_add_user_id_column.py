"""Rename tables and add user_id column

Revision ID: 465368ca2bac
Revises: 9d0519332fdd
Create Date: 2024-08-01 20:36:52.629572

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "465368ca2bac"  # pragma: allowlist secret
down_revision: Union[str, None] = "9d0519332fdd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.rename_table("query-response", "query_response")

    op.rename_table("query-response-feedback", "query_response_feedback")
    op.execute(
        'ALTER INDEX "ix_query-response-feedback_feedback_id" '
        "RENAME TO ix_query_response_feedback_feedback_id"
    )
    op.execute(
        'ALTER INDEX "query-response-feedback_pkey" '
        "RENAME TO query_response_feedback_pkey"
    )

    op.rename_table("content-feedback", "content_feedback")
    op.execute(
        'ALTER INDEX "ix_content-feedback_feedback_id" '
        "RENAME TO ix_content_feedback_feedback_id"
    )
    op.execute('ALTER INDEX "content-feedback_pkey" RENAME TO content_feedback_pkey')

    op.rename_table("urgency-rule", "urgency_rule")
    op.execute('ALTER INDEX "urgency-rule_pkey" RENAME TO urgency_rule_pkey')

    op.rename_table("urgency-query", "urgency_query")
    op.execute(
        'ALTER INDEX "ix_urgency-query_urgency_query_id" '
        "RENAME TO ix_urgency_query_urgency_query_id"
    )
    op.execute('ALTER INDEX "urgency-query_pkey" RENAME TO urgency_query_pkey')

    op.rename_table("urgency-response", "urgency_response")
    op.execute(
        'ALTER INDEX "ix_urgency-response_urgency_response_id" '
        "RENAME TO ix_urgency_response_urgency_response_id"
    )
    op.execute('ALTER INDEX "urgency-response_pkey" RENAME TO urgency_response_pkey')

    op.rename_table("content-tag", "content_tag")

    # Add user_id column to query_response
    op.add_column("query_response", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        constraint_name="fk_query_response_user_id_user",
        source_table="query_response",
        referent_table="user",
        local_cols=["user_id"],
        remote_cols=["user_id"],
    )
    op.execute(
        """
        UPDATE query_response qr
        SET user_id = q.user_id
        FROM query q
        WHERE qr.query_id = q.query_id
        """
    )
    op.alter_column("query_response", "user_id", nullable=False)

    # Add user_id column to query_response_feedback
    op.add_column(
        "query_response_feedback", sa.Column("user_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        constraint_name="fk_query_response_feedback_user_id_user",
        source_table="query_response_feedback",
        referent_table="user",
        local_cols=["user_id"],
        remote_cols=["user_id"],
    )
    op.execute(
        """
        UPDATE query_response_feedback qrf
        SET user_id = q.user_id
        FROM query q
        WHERE qrf.query_id = q.query_id
        """
    )
    op.alter_column("query_response_feedback", "user_id", nullable=False)

    # Add user_id column to content_feedback
    op.add_column("content_feedback", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        constraint_name="fk_content_feedback_user_id_user",
        source_table="content_feedback",
        referent_table="user",
        local_cols=["user_id"],
        remote_cols=["user_id"],
    )
    op.execute(
        """
        UPDATE content_feedback cf
        SET user_id = q.user_id
        FROM query q
        WHERE cf.query_id = q.query_id
        """
    )
    op.alter_column("content_feedback", "user_id", nullable=False)

    # Add user_id column to urgency_rule
    # op.add_column("content_tag", sa.Column("user_id", sa.Integer(), nullable=True))
    # op.create_foreign_key(
    #     constraint_name="fk_content_tag_user_id_user",
    #     source_table="content_tag",
    #     referent_table="user",
    #     local_cols=["user_id"],
    #     remote_cols=["user_id"],
    # )
    # op.execute(
    #     """
    #     UPDATE content_tag ct
    #     SET user_id = c.user_id
    #     FROM content c
    #     WHERE ct.content_id = c.content_id
    #     """
    # )
    # op.alter_column("content_tag", "user_id", nullable=False)

    # Add user_id column to urgency_response
    op.add_column("urgency_response", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        constraint_name="fk_urgency_response_user_id_user",
        source_table="urgency_response",
        referent_table="user",
        local_cols=["user_id"],
        remote_cols=["user_id"],
    )
    op.execute(
        """
        UPDATE urgency_response ur
        SET user_id = uq.user_id
        FROM urgency_query uq
        WHERE ur.query_id = uq.urgency_query_id
        """
    )
    op.alter_column("urgency_response", "user_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint(
        "fk_query_response_user_id_user", "query_response", type_="foreignkey"
    )
    op.drop_column("query_response", "user_id")

    op.drop_constraint(
        "fk_query_response_feedback_user_id_user",
        "query_response_feedback",
        type_="foreignkey",
    )
    op.drop_column("query_response_feedback", "user_id")

    op.drop_constraint(
        "fk_content_feedback_user_id_user", "content_feedback", type_="foreignkey"
    )
    op.drop_column("content_feedback", "user_id")

    # op.drop_constraint(
    #     "fk_content_tag_user_id_user", "content_tag", type_="foreignkey")
    # op.drop_column("content_tag", "user_id")

    op.drop_constraint(
        "fk_urgency_response_user_id_user", "urgency_response", type_="foreignkey"
    )
    op.drop_column("urgency_response", "user_id")

    # Rename tables
    op.rename_table("query_response", "query-response")

    op.rename_table("query_response_feedback", "query-response-feedback")
    op.execute(
        "ALTER INDEX ix_query_response_feedback_feedback_id "
        'RENAME TO "ix_query-response-feedback_feedback_id"'
    )
    op.execute(
        "ALTER INDEX query_response_feedback_pkey "
        'RENAME TO "query-response-feedback_pkey"'
    )

    op.rename_table("content_feedback", "content-feedback")
    op.execute(
        "ALTER INDEX ix_content_feedback_feedback_id "
        'RENAME TO "ix_content-feedback_feedback_id"'
    )
    op.execute("ALTER INDEX content_feedback_pkey " 'RENAME TO "content-feedback_pkey"')

    op.rename_table("urgency_rule", "urgency-rule")
    op.execute("ALTER INDEX urgency_rule_pkey " 'RENAME TO "urgency-rule_pkey"')

    op.rename_table("urgency_query", "urgency-query")
    op.execute(
        "ALTER INDEX ix_urgency_query_urgency_query_id "
        'RENAME TO "ix_urgency-query_urgency_query_id"'
    )
    op.execute("ALTER INDEX urgency_query_pkey " 'RENAME TO "urgency-query_pkey"')

    op.rename_table("urgency_response", "urgency-response")
    op.execute(
        "ALTER INDEX ix_urgency_response_urgency_response_id "
        'RENAME TO "ix_urgency-response_urgency_response_id"'
    )
    op.execute("ALTER INDEX urgency_response_pkey " 'RENAME TO "urgency-response_pkey"')

    op.rename_table("content_tag", "content-tag")
