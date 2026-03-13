from __future__ import annotations
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship # Added relationship

from server.models.base import Base

class ClientLocation(Base):
    __tablename__ = "Client_locations"
    __table_args__ = (CheckConstraint("location_type IN ('home','work','volunteer')", name="CHK_LocationType"),)

    client_location_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("Locations.location_id"), nullable=False)
    
    # NEW RELATIONSHIP
    location: Mapped["Location"] = relationship("Location")

    location_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)