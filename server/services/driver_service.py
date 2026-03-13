from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
from server.models.route import Route as RouteModel
from server.models.route_stop import RouteStop as StopModel

def list_available_routes() -> dict:
    engine = get_engine()
    with Session(engine) as session:
        # We only want routes that haven't been completed or fully assigned yet
        stmt = select(RouteModel).where(RouteModel.status == "available")
        results = session.execute(stmt).scalars().all()
        
        return {
            "routes": [
                {
                    "id": str(r.route_id),
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "stop_count": len(r.stops)
                } for r in results
            ]
        }

def get_route(route_id: str) -> dict:
    engine = get_engine()
    with Session(engine) as session:
        # Use session.get for primary key lookup
        route = session.get(RouteModel, int(route_id))
        if not route:
            return {"error": "Route not found", "code": "not_found"}
            
        # Format the stops for the Driver's mobile-style view
        stops = []
        for s in route.stops:
            stops.append({
                "id": str(s.stop_id),
                "label": s.stop_type, # e.g., 'pickup' or 'dropoff'
                "arrival_time": s.planned_arrival_time.isoformat() if s.planned_arrival_time else None
            })

        return {
            "route": {
                "id": str(route.route_id),
                "status": route.status,
                "stops": stops
            }
        }

def accept_route(route_id: str, data: dict) -> dict:
    engine = get_engine()
    try:
        with Session(engine) as session:
            route = session.get(RouteModel, int(route_id))
            if not route:
                return {"error": "Route not found", "code": "not_found"}

            route.status = "accepted"
            route.driver_id = data.get("driver_id") # Link to the driver's User ID
            session.commit()
            
            return {"message": "Route accepted", "route": {"id": str(route.route_id), "status": route.status}}
    except Exception as e:
        return {"error": str(e), "code": "db_failure"}

def complete_route(route_id: str) -> dict:
    engine = get_engine()
    with Session(engine) as session:
        route = session.get(RouteModel, int(route_id))
        if not route:
            return {"error": "Route not found", "code": "not_found"}
            
        route.status = "completed"
        session.commit()
        return {"message": "Route completed", "route": {"id": str(route.route_id), "status": "completed"}}