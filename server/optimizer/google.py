import os
import googlemaps
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from server.db import get_engine
from server.models.ride_request import RideRequest
from server.models.optimized_route import OptimizedRoute
from server.models.optimization_run import OptimizationRun # Add this import
from server.models.client_location import ClientLocation
from server.models.location import Location

class GoogleOptimizer:
    @staticmethod
    def run_optimization_sync():
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        gmaps = googlemaps.Client(key=api_key)
        engine = get_engine()
        
        with Session(engine) as session:
            # 1. Start an Optimization Run (Required by your Schema)
            new_run = OptimizationRun(
                ride_date=datetime.utcnow().date(),
                started_at=datetime.utcnow(),
                success=False # Will flip to True if we finish
            )
            session.add(new_run)
            session.flush() # This generates the run_id

            # 2. Get the rides
            stmt = (
                select(RideRequest)
                .options(joinedload(RideRequest.pickup_location).joinedload(ClientLocation.location))
                .where(RideRequest.status == "requested")
            )
            rides = session.execute(stmt).scalars().all()
            
            if not rides:
                return {"message": "No requested rides to optimize"}

            # 3. Call Google (This part is already working!)
            first_ride_loc = rides[0].pickup_location.location
            origin = (first_ride_loc.latitude, first_ride_loc.longitude)
            waypoints = [(r.pickup_location.location.latitude, r.pickup_location.location.longitude) for r in rides[1:]]

            directions_result = gmaps.directions(
                origin=origin, destination=origin, waypoints=waypoints,
                optimize_waypoints=True, mode="driving"
            )
            
            # 4. Save the Route linked to our new run_id
            new_route = OptimizedRoute(
                route_date=datetime.utcnow().date(),
                status="available",
                run_id=new_run.run_id, # Use the dynamic ID
                polyline=directions_result[0]['overview_polyline']['points'] # Store the map line!
            )
            session.add(new_route)
            
            for ride in rides:
                ride.status = "scheduled"
            
            # 5. Mark run as successful
            new_run.success = True
            new_run.ended_at = datetime.utcnow()
                
            session.commit()
            return {"message": f"Successfully optimized {len(rides)} ride(s) on Run #{new_run.run_id}!"}