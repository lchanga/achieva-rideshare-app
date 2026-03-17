from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
from server.models.optimized_route import OptimizedRoute
from server.models.route_stop import RouteStop

APP_TIMEZONE = ZoneInfo("America/New_York")


def _coerce_route_id(route_id: str) -> int | None:
    try:
        return int(route_id)
    except (TypeError, ValueError):
        return None


def _serialize_route(route: OptimizedRoute, stops: list[RouteStop]) -> dict:
    return {
        "id": str(route.route_id),
        "status": route.status,
        "driver_id": str(route.driver_id) if route.driver_id is not None else None,
        "route_date": route.route_date.isoformat() if route.route_date else None,
        "accepted_at": route.accepted_at.isoformat() if route.accepted_at else None,
        "stop_count": len(stops),
        "stops": [
            {
                "id": str(stop.stop_id),
                "label": stop.stop_type,
                "arrival_time": stop.planned_arrival.isoformat() if stop.planned_arrival else None,
                "status": stop.status,
            }
            for stop in stops
        ],
    }

def get_route(route_id: str) -> dict:
    route_pk = _coerce_route_id(route_id)
    if route_pk is None:
        return {"error": "Route not found", "code": "not_found"}

    with Session(get_engine()) as session:
        route = session.get(OptimizedRoute, route_pk)
        if not route:
            return {"error": "Route not found", "code": "not_found"}

        stops = session.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_pk)
            .order_by(RouteStop.stop_sequence.asc())
        ).scalars().all()
        return {"route": _serialize_route(route, stops)}


def get_driver_today_route(driver_id: str) -> dict:
    driver_pk = _coerce_route_id(driver_id)
    if driver_pk is None:
        return {"error": "Driver not found", "code": "not_found"}

    today_local = datetime.now(APP_TIMEZONE).date()

    with Session(get_engine()) as session:
        route = session.execute(
            select(OptimizedRoute)
            .where(
                OptimizedRoute.driver_id == driver_pk,
                OptimizedRoute.route_date == today_local,
            )
            .order_by(OptimizedRoute.route_id.asc())
        ).scalar_one_or_none()
        if not route:
            return {"message": "You don't have a ride today.", "route": None}

        stops = session.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route.route_id)
            .order_by(RouteStop.stop_sequence.asc())
        ).scalars().all()
        return {"message": "You have a ride today.", "route": _serialize_route(route, stops)}


def accept_route(route_id: str, data: dict) -> dict:
    route_pk = _coerce_route_id(route_id)
    if route_pk is None:
        return {"error": "Route not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            route = session.get(OptimizedRoute, route_pk)
            if not route:
                return {"error": "Route not found", "code": "not_found"}

            route.status = "assigned"
            route.driver_id = int(data["driver_id"]) if data.get("driver_id") is not None else None
            route.accepted_at = datetime.utcnow()
            session.commit()

            stops = session.execute(
                select(RouteStop)
                .where(RouteStop.route_id == route_pk)
                .order_by(RouteStop.stop_sequence.asc())
            ).scalars().all()
            return {"message": "Route accepted", "route": _serialize_route(route, stops)}
    except Exception as e:
        return {"error": str(e), "code": "db_failure"}


def complete_route(route_id: str) -> dict:
    route_pk = _coerce_route_id(route_id)
    if route_pk is None:
        return {"error": "Route not found", "code": "not_found"}

    with Session(get_engine()) as session:
        route = session.get(OptimizedRoute, route_pk)
        if not route:
            return {"error": "Route not found", "code": "not_found"}

        if route.status not in ("assigned", "in_progress"):
            return {
                "error": f"Cannot complete route from status '{route.status}'",
                "code": "invalid_status_transition",
            }

        route.status = "completed"
        session.commit()
        stops = session.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_pk)
            .order_by(RouteStop.stop_sequence.asc())
        ).scalars().all()
        return {"message": "Route completed", "route": _serialize_route(route, stops)}


def start_route(route_id: str) -> dict:
    route_pk = _coerce_route_id(route_id)
    if route_pk is None:
        return {"error": "Route not found", "code": "not_found"}

    with Session(get_engine()) as session:
        route = session.get(OptimizedRoute, route_pk)
        if not route:
            return {"error": "Route not found", "code": "not_found"}

        if route.status not in ("assigned", "scheduled", "available"):
            return {
                "error": f"Cannot start route from status '{route.status}'",
                "code": "invalid_status_transition",
            }

        route.status = "in_progress"
        route.accepted_at = datetime.utcnow()
        session.commit()

        stops = session.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_pk)
            .order_by(RouteStop.stop_sequence.asc())
        ).scalars().all()
        return {"message": "Route started", "route": _serialize_route(route, stops)}


def remove_stop(route_id: str, data: dict) -> dict:
    route_pk = _coerce_route_id(route_id)
    if route_pk is None:
        return {"error": "Route not found", "code": "not_found"}

    with Session(get_engine()) as session:
        route = session.get(OptimizedRoute, route_pk)
        if not route:
            return {"error": "Route not found", "code": "not_found"}

        stop = None
        if data.get("stop_id") is not None:
            try:
                stop = session.get(RouteStop, int(data["stop_id"]))
            except (TypeError, ValueError):
                return {"error": "Invalid stop_id", "code": "invalid_request"}
            if stop and stop.route_id != route_pk:
                stop = None
        elif data.get("stop_index") is not None:
            try:
                requested_index = int(data["stop_index"])
            except (TypeError, ValueError):
                return {"error": "Invalid stop_index", "code": "invalid_request"}
            stop = session.execute(
                select(RouteStop)
                .where(RouteStop.route_id == route_pk)
                .order_by(RouteStop.stop_sequence.asc())
                .offset(requested_index)
                .limit(1)
            ).scalar_one_or_none()
        else:
            return {"error": "Provide stop_id or stop_index", "code": "invalid_request"}

        if not stop:
            return {"error": "Stop not found", "code": "not_found"}

        stop.status = "skipped"
        session.commit()

        stops = session.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_pk)
            .order_by(RouteStop.stop_sequence.asc())
        ).scalars().all()
        return {"message": "Stop removed from route", "route": _serialize_route(route, stops)}