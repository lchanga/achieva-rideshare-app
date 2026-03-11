from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import List

from server.optimizer.google import GoogleOptimizer
from server.db import get_engine
from sqlalchemy.orm import Session
from sqlalchemy import text, select

# Import your models
from server.models.ride_request import RideRequest
from server.models.optimized_route import OptimizedRoute

app = FastAPI(
    title="Achieva Rideshare API",
    description="Backend engine for ride optimization and routing",
    version="1.0.0"
)

# --- SCHEMAS (For PWA Data Validation) ---
class RideCreate(BaseModel):
    passenger_id: int
    pickup_location_id: int
    dropoff_location_id: int

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "message": "Achieva Routing Engine is active"}


@app.get("/rides", tags=["Rides"])
def get_all_rides():
    """
    Returns a list of all ride requests. 
    Useful for checking if rides have been 'scheduled' by the optimizer.
    """
    engine = get_engine()
    with Session(engine) as session:
        # Sort by request_id descending so new rides are at the top
        stmt = select(RideRequest).order_by(RideRequest.request_id.desc())
        rides = session.execute(stmt).scalars().all()
        return rides
    
@app.post("/rides", tags=["Rides"])
def create_ride(ride_data: RideCreate):
    """
    Simulates a Passenger requesting a ride.
    In the PWA, this is what the 'Request Ride' button calls.
    """
    engine = get_engine()
    with Session(engine) as session:
        try:
            new_ride = RideRequest(
                passenger_id=ride_data.passenger_id,
                pickup_client_location_id=ride_data.pickup_location_id,
                dropoff_client_location_id=ride_data.dropoff_location_id,
                ride_date=date.today(),
                pickup_window_start=datetime.utcnow(),
                pickup_window_end=datetime.utcnow() + timedelta(hours=1),
                dropoff_window_start=datetime.utcnow() + timedelta(hours=1),
                dropoff_window_end=datetime.utcnow() + timedelta(hours=2),
                status="requested",
                api_shipment_label=f"PWA_{datetime.utcnow().strftime('%H%M%S')}"
            )
            session.add(new_ride)
            session.commit()
            return {"status": "success", "ride_id": new_ride.request_id}
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

@app.post("/optimize", tags=["Optimization"])
def trigger_optimization():
    """
    The 'Dispatcher' button. Processes all requested rides into routes.
    """
    try:
        result = GoogleOptimizer.run_optimization_sync()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/routes", tags=["Routes"])
def get_optimized_routes():
    """
    The 'Driver' View. Returns all routes and their polylines for the map.
    """
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(OptimizedRoute).order_by(OptimizedRoute.route_id.desc())
        routes = session.execute(stmt).scalars().all()
        return routes

@app.get("/healthcheck", tags=["System"])
def health_check():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "details": str(e)}