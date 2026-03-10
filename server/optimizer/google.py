import os
import googlemaps
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
from server.models.ride_request import RideRequest
from server.models.optimized_route import OptimizedRoute
from server.models.route_stop import RouteStop

class GoogleOptimizer:
    @staticmethod
    def run_optimization_sync():
        # 1. Setup
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        gmaps = googlemaps.Client(key=api_key)
        engine = get_engine()
        
        with Session(engine) as session:
            # 2. Get pending rides
            stmt = select(RideRequest).where(RideRequest.status == "pending")
            rides = session.execute(stmt).scalars().all()
            
            if not rides:
                return {"message": "No pending rides to optimize"}

            # 3. Optimization Logic (Directions API)
            origin = (rides[0].pickup_latitude, rides[0].pickup_longitude)
            waypoints = [(r.pickup_latitude, r.pickup_longitude) for r in rides[1:]]

            directions_result = gmaps.directions(
                origin=origin,
                destination=origin,
                waypoints=waypoints,
                optimize_waypoints=True,
                mode="driving"
            )
            
            # 4. Save to SQL Server
            new_route = OptimizedRoute(status="available", created_at=datetime.utcnow())
            session.add(new_route)
            session.flush()

            for ride in rides:
                stop = RouteStop(route_id=new_route.route_id, stop_type="pickup")
                ride.status = "scheduled"
                session.add(stop)
                
            session.commit()
            return {"message": f"SUCCESS: Google reordered {len(rides)} stops!"}