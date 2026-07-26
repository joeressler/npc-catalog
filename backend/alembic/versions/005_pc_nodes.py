"""pc nodes and node-id edges

Revision ID: 005
Revises: 004
Create Date: 2026-07-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    node_cols = {row[1] for row in conn.execute(sa.text("pragma table_info(graph_nodes)")).fetchall()}
    if "label" not in node_cols:
        with op.batch_alter_table("graph_nodes", schema=None) as batch_op:
            batch_op.add_column(sa.Column("label", sa.String(length=200), nullable=True))

    edge_cols = {row[1] for row in conn.execute(sa.text("pragma table_info(graph_edges)")).fetchall()}
    if "from_node_id" not in edge_cols:
        with op.batch_alter_table("graph_edges", schema=None) as batch_op:
            batch_op.add_column(sa.Column("from_node_id", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("to_node_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE graph_edges
        SET from_node_id = (
            SELECT graph_nodes.id
            FROM graph_nodes
            WHERE graph_nodes.graph_id = graph_edges.graph_id
              AND graph_nodes.kind = graph_edges.from_kind
              AND (
                (graph_edges.from_npc_id IS NULL AND graph_nodes.npc_id IS NULL)
                OR graph_nodes.npc_id = graph_edges.from_npc_id
              )
            LIMIT 1
        )
        WHERE from_node_id IS NULL AND from_kind IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE graph_edges
        SET to_node_id = (
            SELECT graph_nodes.id
            FROM graph_nodes
            WHERE graph_nodes.graph_id = graph_edges.graph_id
              AND graph_nodes.kind = graph_edges.to_kind
              AND (
                (graph_edges.to_npc_id IS NULL AND graph_nodes.npc_id IS NULL)
                OR graph_nodes.npc_id = graph_edges.to_npc_id
              )
            LIMIT 1
        )
        WHERE to_node_id IS NULL AND to_kind IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE TABLE graph_edges_new (
            id INTEGER NOT NULL PRIMARY KEY,
            graph_id INTEGER NOT NULL,
            relation_type_id INTEGER NOT NULL,
            from_node_id INTEGER NOT NULL,
            to_node_id INTEGER NOT NULL,
            notes TEXT NOT NULL,
            FOREIGN KEY(graph_id) REFERENCES character_graphs (id) ON DELETE CASCADE,
            FOREIGN KEY(relation_type_id) REFERENCES relation_types (id) ON DELETE RESTRICT,
            FOREIGN KEY(from_node_id) REFERENCES graph_nodes (id) ON DELETE CASCADE,
            FOREIGN KEY(to_node_id) REFERENCES graph_nodes (id) ON DELETE CASCADE,
            CONSTRAINT uq_graph_edges_directed_relation
                UNIQUE (graph_id, from_node_id, to_node_id, relation_type_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO graph_edges_new (id, graph_id, relation_type_id, from_node_id, to_node_id, notes)
        SELECT id, graph_id, relation_type_id, from_node_id, to_node_id, notes
        FROM graph_edges
        WHERE from_node_id IS NOT NULL AND to_node_id IS NOT NULL
        """
    )
    op.execute("DROP TABLE graph_edges")
    op.execute("ALTER TABLE graph_edges_new RENAME TO graph_edges")


def downgrade() -> None:
    op.execute(
        """
        CREATE TABLE graph_edges_old (
            id INTEGER NOT NULL PRIMARY KEY,
            graph_id INTEGER NOT NULL,
            relation_type_id INTEGER NOT NULL,
            from_kind VARCHAR(20) NOT NULL,
            from_npc_id INTEGER,
            to_kind VARCHAR(20) NOT NULL,
            to_npc_id INTEGER,
            notes TEXT NOT NULL,
            FOREIGN KEY(graph_id) REFERENCES character_graphs (id) ON DELETE CASCADE,
            FOREIGN KEY(relation_type_id) REFERENCES relation_types (id) ON DELETE RESTRICT,
            FOREIGN KEY(from_npc_id) REFERENCES npcs (id) ON DELETE CASCADE,
            FOREIGN KEY(to_npc_id) REFERENCES npcs (id) ON DELETE CASCADE,
            CONSTRAINT uq_graph_edges_directed_relation
                UNIQUE (graph_id, from_kind, from_npc_id, to_kind, to_npc_id, relation_type_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO graph_edges_old (
            id, graph_id, relation_type_id, from_kind, from_npc_id, to_kind, to_npc_id, notes
        )
        SELECT
            e.id,
            e.graph_id,
            e.relation_type_id,
            f.kind,
            f.npc_id,
            t.kind,
            t.npc_id,
            e.notes
        FROM graph_edges e
        JOIN graph_nodes f ON f.id = e.from_node_id
        JOIN graph_nodes t ON t.id = e.to_node_id
        """
    )
    op.execute("DROP TABLE graph_edges")
    op.execute("ALTER TABLE graph_edges_old RENAME TO graph_edges")

    with op.batch_alter_table("graph_nodes", schema=None) as batch_op:
        batch_op.drop_column("label")
