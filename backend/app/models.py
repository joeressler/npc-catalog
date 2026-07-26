from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    npcs: Mapped[list["NPC"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="GameSession.number",
    )
    graphs: Mapped[list["CharacterGraph"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CharacterGraph.name",
    )
    relation_types: Mapped[list["RelationType"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="RelationType.name",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    npcs: Mapped[list["NPC"]] = relationship(
        secondary="npc_tags",
        back_populates="tags",
    )


class NPC(Base):
    __tablename__ = "npcs"
    __table_args__ = (
        Index("ix_npcs_campaign_name", "campaign_id", "name"),
        Index("ix_npcs_alignment", "alignment"),
        Index("ix_npcs_location", "location"),
        Index("ix_npcs_faction", "faction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    role_occupation: Mapped[str] = mapped_column(String(200))
    alignment: Mapped[str] = mapped_column(String(2))
    location: Mapped[str] = mapped_column(String(200))
    faction: Mapped[str] = mapped_column(String(200), default="")
    attitude: Mapped[str] = mapped_column(String(200))
    party_relationship: Mapped[str] = mapped_column(String(200))
    appearance: Mapped[str] = mapped_column(Text, default="")
    voice_mannerisms: Mapped[str] = mapped_column(Text, default="")
    personality_traits: Mapped[str] = mapped_column(Text, default="")
    motivation_goal: Mapped[str] = mapped_column(Text, default="")
    secret_hook: Mapped[str] = mapped_column(Text, default="")
    knowledge: Mapped[str] = mapped_column(Text, default="")
    inventory: Mapped[str] = mapped_column(Text, default="")
    dm_notes: Mapped[str] = mapped_column(Text, default="")
    session_log: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="npcs")
    aliases: Mapped[list["Alias"]] = relationship(
        back_populates="npc",
        cascade="all, delete-orphan",
        order_by="Alias.name",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="npc_tags",
        back_populates="npcs",
        order_by="Tag.name",
    )


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = (UniqueConstraint("npc_id", "name", name="uq_aliases_npc_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npcs.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))

    npc: Mapped["NPC"] = relationship(back_populates="aliases")


class NPCTag(Base):
    __tablename__ = "npc_tags"

    npc_id: Mapped[int] = mapped_column(
        ForeignKey("npcs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class GameSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "number", name="uq_sessions_campaign_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(200), default="")
    overall_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="sessions")
    story_paths: Mapped[list["SessionStoryPath"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionStoryPath.sort_order",
    )
    clues: Mapped[list["SessionClue"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionClue.sort_order",
    )
    secrets: Mapped[list["SessionSecret"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionSecret.sort_order",
    )
    characters: Mapped[list["NPC"]] = relationship(
        secondary="session_npcs",
        order_by="NPC.name",
    )


class SessionStoryPath(Base):
    __tablename__ = "session_story_paths"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column()

    session: Mapped["GameSession"] = relationship(back_populates="story_paths")
    beats: Mapped[list["SessionBeat"]] = relationship(
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="SessionBeat.sort_order",
    )


class SessionBeat(Base):
    __tablename__ = "session_beats"

    id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("session_story_paths.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column()

    path: Mapped["SessionStoryPath"] = relationship(back_populates="beats")


class SessionClue(Base):
    __tablename__ = "session_clues"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column()

    session: Mapped["GameSession"] = relationship(back_populates="clues")


class SessionSecret(Base):
    __tablename__ = "session_secrets"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column()

    session: Mapped["GameSession"] = relationship(back_populates="secrets")


class SessionNPC(Base):
    __tablename__ = "session_npcs"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    npc_id: Mapped[int] = mapped_column(
        ForeignKey("npcs.id", ondelete="CASCADE"),
        primary_key=True,
    )


class CharacterGraph(Base):
    __tablename__ = "character_graphs"
    __table_args__ = (
        UniqueConstraint("campaign_id", "name", name="uq_character_graphs_campaign_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")
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
