from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
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

    campaign: Mapped["Campaign"] = relationship(back_populates="locations")
    loot: Mapped[list["LocationLoot"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationLoot.sort_order",
    )
    objects: Mapped[list["LocationObject"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationObject.sort_order",
    )
    npcs: Mapped[list["NPC"]] = relationship(
        secondary="location_npcs",
        order_by="NPC.name",
    )
    residents: Mapped[list["NPC"]] = relationship(
        back_populates="catalog_location",
        order_by="NPC.name",
    )


class LocationLoot(Base):
    __tablename__ = "location_loot"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column()

    location: Mapped["Location"] = relationship(back_populates="loot")


class LocationObject(Base):
    __tablename__ = "location_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column()

    location: Mapped["Location"] = relationship(back_populates="objects")


class LocationNPC(Base):
    __tablename__ = "location_npcs"

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    npc_id: Mapped[int] = mapped_column(
        ForeignKey("npcs.id", ondelete="CASCADE"),
        primary_key=True,
    )


class SessionLocation(Base):
    __tablename__ = "session_locations"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    )
