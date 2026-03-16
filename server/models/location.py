from __future__ import annotations
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from server.models.base import Base

class Location(Base):
    __tablename__ = "Locations"

    __table_args__ = {"schema": "dbo"}

    location_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    zip: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)