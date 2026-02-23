"""
Driver service layer.

Bare-minimum in-memory persistence while we iterate quickly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class RouteStop:
    id: str
    label: str


@dataclass
class DriverRoute:
    id: str
    status: str  # available | accepted | completed
    driver_id: str | None = None
    stops: list[RouteStop] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z")


# In-memory store (temporary). Replace with SQL Server persistence later.
_ROUTES: dict[str, DriverRoute] = {}


def _ensure_seed_data() -> None:
    """
    Seed a small demo route so driver endpoints are testable immediately.

    In the real system, routes will be created by the nightly optimization job.
    """
    if _ROUTES:
        return

    route_id = str(uuid4())
    _ROUTES[route_id] = DriverRoute(
        id=route_id,
        status="available",
        stops=[
            RouteStop(id=str(uuid4()), label="Pickup: Example Home"),
            RouteStop(id=str(uuid4()), label="Dropoff: Example Employer"),
        ],
    )


def list_available_routes() -> dict:
    _ensure_seed_data()
    available = [r for r in _ROUTES.values() if r.status == "available"]
    return {"routes": [asdict(r) for r in available]}


def accept_route(route_id: str, data: dict) -> dict:
    _ensure_seed_data()
    route = _ROUTES.get(route_id)
    if not route:
        return {"error": "Route not found", "code": "not_found"}

    driver_id = (data.get("driver_id") or "").strip() or None
    route.status = "accepted"
    route.driver_id = driver_id
    return {"message": "Route accepted", "route": asdict(route)}


def get_route(route_id: str) -> dict:
    _ensure_seed_data()
    route = _ROUTES.get(route_id)
    if not route:
        return {"error": "Route not found", "code": "not_found"}
    return {"route": asdict(route)}


def complete_route(route_id: str) -> dict:
    _ensure_seed_data()
    route = _ROUTES.get(route_id)
    if not route:
        return {"error": "Route not found", "code": "not_found"}
    route.status = "completed"
    return {"message": "Route completed", "route": asdict(route)}


def remove_stop(route_id: str, data: dict) -> dict:
    """
    Remove a stop from a route.

    Body supports either:
    - { "stop_id": "<uuid>" }
    - { "stop_index": 0 }
    """
    _ensure_seed_data()
    route = _ROUTES.get(route_id)
    if not route:
        return {"error": "Route not found", "code": "not_found"}

    stop_id = (data.get("stop_id") or "").strip()
    stop_index = data.get("stop_index", None)

    if stop_id:
        route.stops = [s for s in route.stops if s.id != stop_id]
    elif isinstance(stop_index, int):
        if 0 <= stop_index < len(route.stops):
            route.stops.pop(stop_index)
    else:
        # No identifier provided: simplest behavior is to remove the first stop (if any).
        if route.stops:
            route.stops.pop(0)

    return {"message": "Stop removed", "route": asdict(route)}

