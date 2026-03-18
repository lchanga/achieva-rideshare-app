from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.api_core.client_options import ClientOptions
from google.cloud import optimization_v1
from google.protobuf import duration_pb2, timestamp_pb2
from google.type import latlng_pb2
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from server.db import get_engine
from server.models.client_location import ClientLocation
from server.models.driver_availability import DriverAvailability
from server.models.location import Location
from server.models.optimization_run import OptimizationRun
from server.models.optimized_route import OptimizedRoute
from server.models.ride_request import RideRequest
from server.models.route_stop import RouteStop
from server.models.user import User


class GoogleOptimizer:
    """
    Google Route Optimization API-backed persisted route generation.
    """

    VEHICLE_CAPACITY = 5
    DEFAULT_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    LOAD_KEY = "passenger_count"
    VISIT_DURATION_SECONDS = 120
    APP_TIMEZONE = ZoneInfo("America/New_York")

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _timestamp(dt: datetime) -> timestamp_pb2.Timestamp:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(GoogleOptimizer._to_utc(dt))
        return ts

    @staticmethod
    def _duration(seconds: int) -> duration_pb2.Duration:
        return duration_pb2.Duration(seconds=seconds)

    @staticmethod
    def _latlng(location: Location) -> latlng_pb2.LatLng:
        return latlng_pb2.LatLng(
            latitude=float(location.latitude),
            longitude=float(location.longitude),
        )

    @staticmethod
    def _to_naive_utc(ts: timestamp_pb2.Timestamp | None, fallback: datetime) -> datetime:
        if ts is None or (ts.seconds == 0 and ts.nanos == 0):
            return fallback
        return ts.ToDatetime().astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _target_ride_date():
        return datetime.now(GoogleOptimizer.APP_TIMEZONE).date() + timedelta(days=1)

    @staticmethod
    def _hq_location(session: Session) -> Location | None:
        return session.execute(
            select(Location)
            .where(Location.name == "Achieva HQ")
            .order_by(Location.location_id.asc())
        ).scalar_one_or_none() or session.execute(
            select(Location).order_by(Location.location_id.asc())
        ).scalar_one_or_none()

    @staticmethod
    def _available_drivers(session: Session) -> list[tuple[DriverAvailability, User]]:
        return session.execute(
            select(DriverAvailability, User)
            .join(User, User.user_id == DriverAvailability.driver_id)
            .where(
                DriverAvailability.is_available == True,
                User.role == "driver",
                User.is_active == True,
            )
            .order_by(User.user_id.asc())
        ).all()

    @staticmethod
    def _build_shipment(ride: RideRequest) -> optimization_v1.Shipment | None:
        pickup_location = ride.pickup_location.location if ride.pickup_location else None
        dropoff_location = ride.dropoff_location.location if ride.dropoff_location else None
        if not pickup_location or not dropoff_location:
            return None

        pickup = optimization_v1.Shipment.VisitRequest(
            arrival_waypoint=optimization_v1.Waypoint(
                location=optimization_v1.Location(lat_lng=GoogleOptimizer._latlng(pickup_location))
            ),
            time_windows=[
                optimization_v1.TimeWindow(
                    start_time=GoogleOptimizer._timestamp(ride.pickup_window_start),
                    end_time=GoogleOptimizer._timestamp(ride.pickup_window_end),
                )
            ],
            duration=GoogleOptimizer._duration(GoogleOptimizer.VISIT_DURATION_SECONDS),
        )
        delivery = optimization_v1.Shipment.VisitRequest(
            arrival_waypoint=optimization_v1.Waypoint(
                location=optimization_v1.Location(lat_lng=GoogleOptimizer._latlng(dropoff_location))
            ),
            time_windows=[
                optimization_v1.TimeWindow(
                    start_time=GoogleOptimizer._timestamp(ride.dropoff_window_start),
                    end_time=GoogleOptimizer._timestamp(ride.dropoff_window_end),
                )
            ],
            duration=GoogleOptimizer._duration(GoogleOptimizer.VISIT_DURATION_SECONDS),
        )
        return optimization_v1.Shipment(
            label=str(ride.request_id),
            pickups=[pickup],
            deliveries=[delivery],
            load_demands={
                GoogleOptimizer.LOAD_KEY: optimization_v1.Shipment.Load(amount=1),
            },
        )

    @staticmethod
    def _build_vehicle(driver: User, hq_location: Location, start_dt: datetime, end_dt: datetime) -> optimization_v1.Vehicle:
        waypoint = optimization_v1.Waypoint(
            location=optimization_v1.Location(lat_lng=GoogleOptimizer._latlng(hq_location))
        )
        return optimization_v1.Vehicle(
            label=str(driver.user_id),
            start_waypoint=waypoint,
            end_waypoint=waypoint,
            start_time_windows=[
                optimization_v1.TimeWindow(
                    start_time=GoogleOptimizer._timestamp(start_dt),
                    end_time=GoogleOptimizer._timestamp(end_dt),
                )
            ],
            end_time_windows=[
                optimization_v1.TimeWindow(
                    start_time=GoogleOptimizer._timestamp(start_dt),
                    end_time=GoogleOptimizer._timestamp(end_dt),
                )
            ],
            load_limits={
                GoogleOptimizer.LOAD_KEY: optimization_v1.Vehicle.LoadLimit(
                    max_load=GoogleOptimizer.VEHICLE_CAPACITY
                )
            },
        )

    @staticmethod
    def run_optimization_sync() -> dict:
        api_key = os.getenv("GOOGLE_ROUTE_OPTIMIZATION_API_KEY")
        if not api_key:
            return {"message": "GOOGLE_ROUTE_OPTIMIZATION_API_KEY is not configured."}

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            return {"message": "GOOGLE_CLOUD_PROJECT is not configured."}

        
        client = optimization_v1.FleetRoutingClient(
            client_options=ClientOptions(api_key=api_key)
        )
        
        parent = f"projects/{project_id}/locations/{GoogleOptimizer.DEFAULT_LOCATION}"

        with Session(get_engine()) as session:
            now = datetime.utcnow()
            target_ride_date = GoogleOptimizer._target_ride_date()
            new_run = OptimizationRun(
                ride_date=target_ride_date,
                started_at=now,
                success=False,
            )
            session.add(new_run)
            session.flush()

            rides = session.execute(
                select(RideRequest)
                .options(joinedload(RideRequest.pickup_location).joinedload(ClientLocation.location))
                .options(joinedload(RideRequest.dropoff_location).joinedload(ClientLocation.location))
                .where(
                    RideRequest.status == "requested",
                    RideRequest.ride_date == target_ride_date,
                )
                .order_by(RideRequest.request_id.asc())
            ).scalars().all()

            if not rides:
                new_run.success = True
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": f"No requested rides to optimize for {target_ride_date.isoformat()}"}

            available_drivers = GoogleOptimizer._available_drivers(session)
            if not available_drivers:
                new_run.error_message = "No available drivers configured."
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": "No available drivers configured."}
            random.shuffle(available_drivers)

            hq_location = GoogleOptimizer._hq_location(session)
            if not hq_location:
                new_run.error_message = "No HQ location available for vehicle start/end."
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": "No HQ location available for vehicle start/end."}

            shipments: list[optimization_v1.Shipment] = []
            ride_by_shipment_index: dict[int, RideRequest] = {}
            for ride in rides:
                shipment = GoogleOptimizer._build_shipment(ride)
                if shipment is None:
                    continue
                shipment_index = len(shipments)
                shipments.append(shipment)
                ride_by_shipment_index[shipment_index] = ride

            if not shipments:
                new_run.error_message = "Requested rides are missing pickup or dropoff locations."
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": "Requested rides are missing pickup or dropoff locations."}

            
            global_start = min(ride.pickup_window_start for ride in ride_by_shipment_index.values()) - timedelta(hours=1)
            global_end = max(ride.dropoff_window_end for ride in ride_by_shipment_index.values()) + timedelta(hours=1)

            vehicles = [
                GoogleOptimizer._build_vehicle(driver, hq_location, global_start, global_end)
                for _, driver in available_drivers
            ]

            request = optimization_v1.OptimizeToursRequest(
                parent=parent,
                model=optimization_v1.ShipmentModel(
                    global_start_time=GoogleOptimizer._timestamp(global_start),
                    global_end_time=GoogleOptimizer._timestamp(global_end),
                    shipments=shipments,
                    vehicles=vehicles,
                ),
                consider_road_traffic=True,
                populate_polylines=True,
            )

            try:
                response = client.optimize_tours(request=request)
            except Exception as exc:
                new_run.error_message = str(exc)
                new_run.ended_at = datetime.utcnow()
                session.commit()
  
                return {"message": f"Google API Error: {str(exc)}"}

            scheduled_request_ids: set[int] = set()
            created_route_count = 0

            for route in response.routes:
                if not route.visits:
                    continue

                driver = available_drivers[route.vehicle_index][1]
                optimized_route = OptimizedRoute(
                    driver_id=driver.user_id,
                    route_date=new_run.ride_date,
                    status="assigned",
                    run_id=new_run.run_id,
                    polyline=(route.route_polyline.points if route.route_polyline else None),
                )
                session.add(optimized_route)
                session.flush()
                created_route_count += 1

                for stop_sequence, visit in enumerate(route.visits, start=1):
                    ride = ride_by_shipment_index.get(visit.shipment_index)
                    if ride is None:
                        continue

                    is_pickup = bool(visit.is_pickup)
                    client_location = ride.pickup_location if is_pickup else ride.dropoff_location
                    location = client_location.location if client_location else None
                    planned_arrival = GoogleOptimizer._to_naive_utc(
                        visit.start_time,
                        ride.pickup_window_start if is_pickup else ride.dropoff_window_start,
                    )
                    if location is None:
                        continue

                    session.add(
                        RouteStop(
                            route_id=optimized_route.route_id,
                            request_id=ride.request_id,
                            location_id=location.location_id,
                            stop_sequence=stop_sequence,
                            stop_type="pickup" if is_pickup else "dropoff",
                            planned_arrival=planned_arrival,
                            status="pending",
                        )
                    )
                    scheduled_request_ids.add(ride.request_id)

            for ride in rides:
                if ride.request_id in scheduled_request_ids:
                    ride.status = "scheduled"

            skipped_count = len(response.skipped_shipments)
            if skipped_count:
                new_run.error_message = f"{skipped_count} shipment(s) were skipped by the optimizer."

            new_run.success = True
            new_run.ended_at = datetime.utcnow()
            session.commit()
            return {
                "message": (
                    f"Successfully optimized {len(scheduled_request_ids)} ride(s) "
                    f"into {created_route_count} route(s) on Run #{new_run.run_id}."
                )
            }