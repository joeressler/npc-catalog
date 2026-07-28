from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    npcs: Mapped[list["NPC"]] = relationship(
        secondary="session_npcs",
        order_by="NPC.name",
    )
    encounters: Mapped[list["Encounter"]] = relationship(
        secondary="session_encounters",
        order_by="Encounter.title",
    )
    locations: Mapped[list["Location"]] = relationship(
        secondary="session_locations",
        order_by="Location.title",
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


class SessionEncounter(Base):
    __tablename__ = "session_encounters"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    encounter_id: Mapped[int] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"),
        primary_key=True,
    )
