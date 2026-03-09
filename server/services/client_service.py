"""
Client service layer.

Bare-minimum in-memory persistence for ride requests.
Validation is intentionally minimal while we iterate quickly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(frozen=True)
class RideRequest:
    id: str
    pickup_location: str
    dropoff_location: str
    date: str
    pickup_window_start: str
    pickup_window_end: str
    dropoff_window_start: str
    dropoff_window_end: str
    status: str
    created_at: str


# In-memory store (temporary). Replace with SQL Server persistence later.
_RIDE_REQUESTS: dict[str, RideRequest] = {}


def _derive_date(value: str) -> str:
    """
    Best-effort YYYY-MM-DD derivation from an ISO-ish datetime string.
    """
    raw = (value or "").strip()
    return raw[:10] if len(raw) >= 10 else ""


def create_ride_request(data: dict) -> dict:
    pickup = (data.get("pickup_location") or "").strip()
    dropoff = (data.get("dropoff_location") or "").strip()
    pickup_window_start = (data.get("pickup_window_start") or "").strip()
    pickup_window_end = (data.get("pickup_window_end") or "").strip()
    dropoff_window_start = (data.get("dropoff_window_start") or "").strip()
    dropoff_window_end = (data.get("dropoff_window_end") or "").strip()
    date_str = (data.get("date") or "").strip() or _derive_date(pickup_window_start)

    ride_id = str(uuid4())
    ride = RideRequest(
        id=ride_id,
        pickup_location=pickup,
        dropoff_location=dropoff,
        date=date_str,
        pickup_window_start=pickup_window_start,
        pickup_window_end=pickup_window_end,
        dropoff_window_start=dropoff_window_start,
        dropoff_window_end=dropoff_window_end,
        status="Pending Optimization",
        created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )
    _RIDE_REQUESTS[ride_id] = ride

    return {"message": "Ride request created", "ride": asdict(ride)}


def list_ride_requests() -> dict:
    rides = [asdict(r) for r in _RIDE_REQUESTS.values()]
    rides.sort(key=lambda r: (r["date"], r["created_at"]))
    return {"rides": rides}


def get_ride_request(ride_id: str) -> dict:
    ride = _RIDE_REQUESTS.get(ride_id)
    if not ride:
        return {"error": "Ride request not found", "code": "not_found"}
    return {"ride": asdict(ride)}


def delete_ride_request(ride_id: str) -> dict:
    if ride_id not in _RIDE_REQUESTS:
        return {"error": "Ride request not found", "code": "not_found"}
    del _RIDE_REQUESTS[ride_id]
    return {"message": "Ride request deleted", "ride_id": ride_id}


def update_ride_request(ride_id: str, data: dict) -> dict:
    ride = _RIDE_REQUESTS.get(ride_id)
    if not ride:
        return {"error": "Ride request not found", "code": "not_found"}

    pickup = ride.pickup_location
    dropoff = ride.dropoff_location
    date_str = ride.date
    pickup_window_start = ride.pickup_window_start
    pickup_window_end = ride.pickup_window_end
    dropoff_window_start = ride.dropoff_window_start
    dropoff_window_end = ride.dropoff_window_end

    if "pickup_location" in data:
        pickup = (data.get("pickup_location") or "").strip()
    if "dropoff_location" in data:
        dropoff = (data.get("dropoff_location") or "").strip()
    if "pickup_window_start" in data:
        pickup_window_start = (data.get("pickup_window_start") or "").strip()
    if "pickup_window_end" in data:
        pickup_window_end = (data.get("pickup_window_end") or "").strip()
    if "dropoff_window_start" in data:
        dropoff_window_start = (data.get("dropoff_window_start") or "").strip()
    if "dropoff_window_end" in data:
        dropoff_window_end = (data.get("dropoff_window_end") or "").strip()
    if "date" in data:
        date_str = (data.get("date") or "").strip()

    if not date_str:
        date_str = _derive_date(pickup_window_start)

    updated = RideRequest(
        id=ride.id,
        pickup_location=pickup,
        dropoff_location=dropoff,
        date=date_str,
        pickup_window_start=pickup_window_start,
        pickup_window_end=pickup_window_end,
        dropoff_window_start=dropoff_window_start,
        dropoff_window_end=dropoff_window_end,
        status="Pending Optimization",
        created_at=ride.created_at,
    )
    _RIDE_REQUESTS[ride_id] = updated

    return {"message": "Ride request updated", "ride": asdict(updated)}

