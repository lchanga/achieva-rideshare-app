from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

# Import the actual SQLAlchemy Model and the DB engine helper
from server.db import get_engine 
from server.models.ride_request import RideRequest as RideRequestModel

def _parse_ts(ts_str: str) -> datetime:
    """Helper to convert ISO strings to datetime objects for SQL."""
    if not ts_str:
        return datetime.utcnow()
    # Normalize 'Z' to '+00:00' for Python's fromisoformat
    clean_ts = ts_str.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(clean_ts)
    except ValueError:
        # Fallback if the string is just a date like '2026-03-10'
        return datetime.strptime(clean_ts[:10], '%Y-%m-%d')

def create_ride_request(data: dict) -> dict:
    engine = get_engine() 
    try:
        with Session(engine) as session:
            # We map the frontend JSON fields to the SQLAlchemy Model columns
            new_ride = RideRequestModel(
                passenger_id=data.get("passenger_id", 1), # Default for demo
                pickup_client_location_id=data.get("pickup_location_id"),
                dropoff_client_location_id=data.get("dropoff_location_id"),
                ride_date=_parse_ts(data.get("pickup_window_start")).date(),
                pickup_window_start=_parse_ts(data.get("pickup_window_start")),
                pickup_window_end=_parse_ts(data.get("pickup_window_end")),
                dropoff_window_start=_parse_ts(data.get("dropoff_window_start")),
                dropoff_window_end=_parse_ts(data.get("dropoff_window_end")),
                status="requested",
                api_shipment_label=f"shipment_{int(datetime.utcnow().timestamp())}"
            )
            
            session.add(new_ride)
            session.commit()
            session.refresh(new_ride) # Populate the auto-incremented request_id

            return {
                "message": "Ride request created", 
                "ride": {
                    "id": str(new_ride.request_id), 
                    "status": new_ride.status,
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
            }
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "code": "db_failure"}

def list_ride_requests() -> dict:
    engine = get_engine()
    with Session(engine) as session:
        # Get all rides, ordered by date
        stmt = select(RideRequestModel).order_by(RideRequestModel.ride_date.desc())
        results = session.execute(stmt).scalars().all()
        
        rides = []
        for r in results:
            rides.append({
                "id": str(r.request_id),
                "status": r.status,
                "date": r.ride_date.isoformat() if r.ride_date else None,
                "pickup_location": f"Location ID: {r.pickup_client_location_id}",
                "dropoff_location": f"Location ID: {r.dropoff_client_location_id}"
            })
        return {"rides": rides}

def get_ride_request(ride_id: str) -> dict:
    engine = get_engine()
    with Session(engine) as session:
        # Convert string ID from URL to integer for the DB lookup
        ride = session.get(RideRequestModel, int(ride_id))
        if not ride:
            return {"error": "Ride request not found", "code": "not_found"}
        return {
            "ride": {
                "id": str(ride.request_id),
                "status": ride.status,
                "date": ride.ride_date.isoformat()
            }
        }

def delete_ride_request(ride_id: str) -> dict:
    engine = get_engine()
    with Session(engine) as session:
        ride = session.get(RideRequestModel, int(ride_id))
        if not ride:
            return {"error": "Ride request not found", "code": "not_found"}
        
        session.delete(ride)
        session.commit()
        return {"message": "Ride request deleted", "ride_id": ride_id}