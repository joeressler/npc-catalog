from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CharacterGraph(Base):
    __tablename__ = "character_graphs"
    __table_args__ = (
        UniqueConstraint("campaign_id", "name", name="uq_character_graphs_campaign_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")
    player_visible: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="graphs")
    nodes: Mapped[list["GraphNode"]] = relationship(
        back_populates="graph",
        cascade="all, delete-orphan",
    )
    edges: Mapped[list["GraphEdge"]] = relationship(
        back_populates="graph",
        cascade="all, delete-orphan",
    )


class RelationType(Base):
    __tablename__ = "relation_types"
    __table_args__ = (
        UniqueConstraint("campaign_id", "name", name="uq_relation_types_campaign_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    polarity: Mapped[str] = mapped_column(String(20))

    campaign: Mapped["Campaign"] = relationship(back_populates="relation_types")
    edges: Mapped[list["GraphEdge"]] = relationship(back_populates="relation_type")


class GraphNode(Base):
    __tablename__ = "graph_nodes"
    __table_args__ = (
        UniqueConstraint("graph_id", "kind", "npc_id", name="uq_graph_nodes_graph_kind_npc"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("character_graphs.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))
    npc_id: Mapped[int | None] = mapped_column(ForeignKey("npcs.id", ondelete="CASCADE"), nullable=True)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pos_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    graph: Mapped["CharacterGraph"] = relationship(back_populates="nodes")
    npc: Mapped["NPC | None"] = relationship()


class GraphEdge(Base):
    __tablename__ = "graph_edges"
    __table_args__ = (
        UniqueConstraint(
            "graph_id",
            "from_node_id",
            "to_node_id",
            "relation_type_id",
            name="uq_graph_edges_directed_relation",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("character_graphs.id", ondelete="CASCADE"))
    relation_type_id: Mapped[int] = mapped_column(ForeignKey("relation_types.id", ondelete="RESTRICT"))
    from_node_id: Mapped[int] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    to_node_id: Mapped[int] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    notes: Mapped[str] = mapped_column(Text, default="")

    graph: Mapped["CharacterGraph"] = relationship(back_populates="edges")
    relation_type: Mapped["RelationType"] = relationship(back_populates="edges")
    from_node: Mapped["GraphNode"] = relationship(foreign_keys=[from_node_id])
    to_node: Mapped["GraphNode"] = relationship(foreign_keys=[to_node_id])
