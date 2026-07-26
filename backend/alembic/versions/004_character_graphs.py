"""character graphs schema

Revision ID: 004
Revises: 003
Create Date: 2026-07-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "character_graphs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "name", name="uq_character_graphs_campaign_name"),
    )
    op.create_table(
        "relation_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("polarity", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "name", name="uq_relation_types_campaign_name"),
    )
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graph_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("npc_id", sa.Integer(), nullable=True),
        sa.Column("pos_x", sa.Float(), nullable=True),
        sa.Column("pos_y", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["graph_id"], ["character_graphs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["npc_id"], ["npcs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("graph_id", "kind", "npc_id", name="uq_graph_nodes_graph_kind_npc"),
    )
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graph_id", sa.Integer(), nullable=False),
        sa.Column("relation_type_id", sa.Integer(), nullable=False),
        sa.Column("from_kind", sa.String(length=20), nullable=False),
        sa.Column("from_npc_id", sa.Integer(), nullable=True),
        sa.Column("to_kind", sa.String(length=20), nullable=False),
        sa.Column("to_npc_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["from_npc_id"], ["npcs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["graph_id"], ["character_graphs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["relation_type_id"], ["relation_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_npc_id"], ["npcs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "graph_id",
            "from_kind",
            "from_npc_id",
            "to_kind",
            "to_npc_id",
            "relation_type_id",
            name="uq_graph_edges_directed_relation",
        ),
    )


def downgrade() -> None:
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
    op.drop_table("relation_types")
    op.drop_table("character_graphs")
