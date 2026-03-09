from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class OptimizationRun(Base):
    __tablename__ = "Optimization_runs"

    run_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    ride_date: Mapped[date] = mapped_column(Date, nullable=False)

