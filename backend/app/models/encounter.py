from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    short_description: Mapped[str] = mapped_column(Text, default="")
    battlefield_description: Mapped[str] = mapped_column(Text, default="")
    further_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="encounters")
    enemies: Mapped[list["EncounterEnemy"]] = relationship(
        back_populates="encounter",
        cascade="all, delete-orphan",
        order_by="EncounterEnemy.sort_order",
    )
    loot: Mapped[list["EncounterLoot"]] = relationship(
        back_populates="encounter",
        cascade="all, delete-orphan",
        order_by="EncounterLoot.sort_order",
    )
    objects: Mapped[list["EncounterObject"]] = relationship(
        back_populates="encounter",
        cascade="all, delete-orphan",
        order_by="EncounterObject.sort_order",
    )
    npcs: Mapped[list["NPC"]] = relationship(
        secondary="encounter_npcs",
        order_by="NPC.name",
    )


class EncounterEnemy(Base):
    __tablename__ = "encounter_enemies"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(200))
    creature_type: Mapped[str] = mapped_column(String(200), default="")
    sort_order: Mapped[int] = mapped_column()

    encounter: Mapped["Encounter"] = relationship(back_populates="enemies")


class EncounterLoot(Base):
    __tablename__ = "encounter_loot"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column()

    encounter: Mapped["Encounter"] = relationship(back_populates="loot")


class EncounterObject(Base):
    __tablename__ = "encounter_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column()

    encounter: Mapped["Encounter"] = relationship(back_populates="objects")


class EncounterNPC(Base):
    __tablename__ = "encounter_npcs"

    encounter_id: Mapped[int] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    npc_id: Mapped[int] = mapped_column(
        ForeignKey("npcs.id", ondelete="CASCADE"),
        primary_key=True,
    )
