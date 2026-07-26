"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "npcs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role_occupation", sa.String(length=200), nullable=False),
        sa.Column("alignment", sa.String(length=2), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("faction", sa.String(length=200), nullable=False),
        sa.Column("attitude", sa.String(length=200), nullable=False),
        sa.Column("party_relationship", sa.String(length=200), nullable=False),
        sa.Column("appearance", sa.Text(), nullable=False),
        sa.Column("voice_mannerisms", sa.Text(), nullable=False),
        sa.Column("personality_traits", sa.Text(), nullable=False),
        sa.Column("motivation_goal", sa.Text(), nullable=False),
        sa.Column("secret_hook", sa.Text(), nullable=False),
        sa.Column("knowledge", sa.Text(), nullable=False),
        sa.Column("inventory", sa.Text(), nullable=False),
        sa.Column("dm_notes", sa.Text(), nullable=False),
        sa.Column("session_log", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_npcs_alignment", "npcs", ["alignment"], unique=False)
    op.create_index("ix_npcs_campaign_name", "npcs", ["campaign_id", "name"], unique=False)
    op.create_index("ix_npcs_faction", "npcs", ["faction"], unique=False)
    op.create_index("ix_npcs_location", "npcs", ["location"], unique=False)
    op.create_table(
        "aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("npc_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["npc_id"], ["npcs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("npc_id", "name", name="uq_aliases_npc_name"),
    )
    op.create_table(
        "npc_tags",
        sa.Column("npc_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["npc_id"], ["npcs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("npc_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("npc_tags")
    op.drop_table("aliases")
    op.drop_index("ix_npcs_location", table_name="npcs")
    op.drop_index("ix_npcs_faction", table_name="npcs")
    op.drop_index("ix_npcs_campaign_name", table_name="npcs")
    op.drop_index("ix_npcs_alignment", table_name="npcs")
    op.drop_table("npcs")
    op.drop_table("tags")
    op.drop_table("campaigns")
