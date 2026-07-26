"""story paths schema

Revision ID: 003
Revises: 002
Create Date: 2026-07-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_story_paths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO session_story_paths (session_id, name, sort_order)
        SELECT DISTINCT session_id, 'Main timeline', 0
        FROM session_beats
        """
    )

    with op.batch_alter_table("session_beats", schema=None) as batch_op:
        batch_op.add_column(sa.Column("path_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE session_beats
        SET path_id = (
            SELECT session_story_paths.id
            FROM session_story_paths
            WHERE session_story_paths.session_id = session_beats.session_id
            LIMIT 1
        )
        """
    )

    with op.batch_alter_table("session_beats", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_session_beats_path_id",
            "session_story_paths",
            ["path_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.drop_column("session_id")

    with op.batch_alter_table("session_beats", schema=None) as batch_op:
        batch_op.alter_column("path_id", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("session_beats", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE session_beats
        SET session_id = (
            SELECT session_story_paths.session_id
            FROM session_story_paths
            WHERE session_story_paths.id = session_beats.path_id
        )
        """
    )

    with op.batch_alter_table("session_beats", schema=None) as batch_op:
        batch_op.drop_constraint("fk_session_beats_path_id", type_="foreignkey")
        batch_op.drop_column("path_id")
        batch_op.create_foreign_key(
            "fk_session_beats_session_id",
            "sessions",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.alter_column("session_id", nullable=False)

    op.drop_table("session_story_paths")
