from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    encounters: Mapped[list["Encounter"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="Encounter.title",
    )
    locations: Mapped[list["Location"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="Location.title",
    )
