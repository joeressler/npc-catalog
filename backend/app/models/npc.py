from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    faction: Mapped[str] = mapped_column(String(200), default="")
    attitude: Mapped[str] = mapped_column(String(200))
    party_relationship: Mapped[str] = mapped_column(String(200))
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    player_visible: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
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
    catalog_location: Mapped["Location | None"] = relationship(back_populates="residents")
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
