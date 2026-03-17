from __future__ import annotations

import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from server.db import get_engine
from server.models.client_location import ClientLocation
from server.models.driver_availability import DriverAvailability
from server.models.optimization_run import OptimizationRun
from server.models.optimized_route import OptimizedRoute
from server.models.ride_request import RideRequest
from server.models.route_stop import RouteStop
from server.models.user import User
from server.optimizer.base import BaseOptimizer


class FakeOptimizer(BaseOptimizer):
    APP_TIMEZONE = ZoneInfo("America/New_York")

    @staticmethod
    def _target_ride_date():
        return datetime.now(FakeOptimizer.APP_TIMEZONE).date() + timedelta(days=1)

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
    def run_optimization_sync() -> dict:
        with Session(get_engine()) as session:
            now = datetime.utcnow()
            target_ride_date = FakeOptimizer._target_ride_date()
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
                .order_by(RideRequest.pickup_window_start.asc(), RideRequest.request_id.asc())
            ).scalars().all()

            if not rides:
                new_run.success = True
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": f"No requested rides to optimize for {target_ride_date.isoformat()}"}

            available_drivers = FakeOptimizer._available_drivers(session)
            if not available_drivers:
                new_run.error_message = "No available drivers configured."
                new_run.ended_at = datetime.utcnow()
                session.commit()
                return {"message": "No available drivers configured."}

            random.shuffle(available_drivers)

            routes_by_driver: dict[int, OptimizedRoute] = {}
            stop_sequence_by_driver: dict[int, int] = {}
            scheduled_request_ids: set[int] = set()

            for index, ride in enumerate(rides):
                driver = available_drivers[index % len(available_drivers)][1]
                route = routes_by_driver.get(driver.user_id)
                if route is None:
                    route = OptimizedRoute(
                        driver_id=driver.user_id,
                        route_date=target_ride_date,
                        status="assigned",
                        run_id=new_run.run_id,
                        polyline=None,
                    )
                    session.add(route)
                    session.flush()
                    routes_by_driver[driver.user_id] = route
                    stop_sequence_by_driver[driver.user_id] = 1

                pickup_location = ride.pickup_location.location if ride.pickup_location else None
                dropoff_location = ride.dropoff_location.location if ride.dropoff_location else None
                if not pickup_location or not dropoff_location:
                    continue

                next_sequence = stop_sequence_by_driver[driver.user_id]
                session.add(
                    RouteStop(
                        route_id=route.route_id,
                        request_id=ride.request_id,
                        location_id=pickup_location.location_id,
                        stop_sequence=next_sequence,
                        stop_type="pickup",
                        planned_arrival=ride.pickup_window_start,
                        status="pending",
                    )
                )
                session.add(
                    RouteStop(
                        route_id=route.route_id,
                        request_id=ride.request_id,
                        location_id=dropoff_location.location_id,
                        stop_sequence=next_sequence + 1,
                        stop_type="dropoff",
                        planned_arrival=ride.dropoff_window_start,
                        status="pending",
                    )
                )
                stop_sequence_by_driver[driver.user_id] = next_sequence + 2
                ride.status = "scheduled"
                scheduled_request_ids.add(ride.request_id)

            new_run.success = True
            new_run.ended_at = datetime.utcnow()
            session.commit()
            return {
                "message": (
                    f"Fake optimizer assigned {len(scheduled_request_ids)} ride(s) "
                    f"into {len(routes_by_driver)} route(s) on Run #{new_run.run_id}."
                )
            }
