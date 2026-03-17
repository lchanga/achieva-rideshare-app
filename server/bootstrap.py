from __future__ import annotations

import time
from datetime import datetime, timedelta

from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import Session

import server.models  # noqa: F401 - registers all models with Base metadata
from server.db import get_engine
from server.models.base import Base
from server.models.client_location import ClientLocation
from server.models.driver_availability import DriverAvailability
from server.models.location import Location
from server.models.ride_request import RideRequest
from server.models.user import User


def seed_data() -> None:
    """
    Insert a small set of demo data when the database is empty.

    The seed is idempotent enough for local/dev startup: each group is only
    created when the corresponding table is empty.
    """
    engine = get_engine()
    with Session(engine) as session:
        demo_locations = [
            {
                "name": "Achieva HQ",
                "address": "711 Bingham St",
                "city": "Pittsburgh",
                "zip": "15203",
                "latitude": 40.4297,
                "longitude": -79.9926,
            },
            {
                "name": "Giant Eagle",
                "address": "4200 Fifth Ave",
                "city": "Pittsburgh",
                "zip": "15213",
                "latitude": 40.4433,
                "longitude": -79.9558,
            },
            {
                "name": "Community Center",
                "address": "123 Market St",
                "city": "Pittsburgh",
                "zip": "15222",
                "latitude": 40.4418,
                "longitude": -80.0003,
            },
        ]
        for location_data in demo_locations:
            existing_location = session.query(Location).filter(Location.name == location_data["name"]).first()
            if not existing_location:
                session.add(Location(**location_data))
        session.commit()

        demo_users = [
            {"first_name": "Ryan", "last_name": "Jackson", "email": "rjackson@achieva.info", "role": "staff"},
            {"first_name": "Kira", "last_name": "Gabridge", "email": "kgabridge@achieva.info", "role": "staff"},
            {"first_name": "Lisa", "last_name": "Stroup", "email": "lstroup@achieva.info", "role": "staff"},
            {"first_name": "Kayla", "last_name": "Edwards", "email": "kaylae@andrew.cmu.edu", "role": "staff"},
            {"first_name": "Ashley", "last_name": "Liu", "email": "ashleyl4@andrew.cmu.edu", "role": "staff"},
            {"first_name": "Victoria", "last_name": "Solsky", "email": "vsolsky@andrew.cmu.edu", "role": "staff"},
            {"first_name": "Bob", "last_name": "Driver", "email": "bob@achieva.info", "role": "driver"},
            {"first_name": "Donna", "last_name": "Driver", "email": "donna@achieva.info", "role": "driver"},
            {"first_name": "Miguel", "last_name": "Driver", "email": "miguel@achieva.info", "role": "driver"},
            {"first_name": "Alice", "last_name": "Client", "email": "alice06@gmail.com", "role": "client"},
        ]
        for user_data in demo_users:
            existing_user = session.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                session.add(User(**user_data))
        session.commit()

        alice = session.query(User).filter(User.email == "alice06@gmail.com").first()
        achieva_hq = session.query(Location).filter(Location.name == "Achieva HQ").first()
        giant_eagle = session.query(Location).filter(Location.name == "Giant Eagle").first()
        community_center = session.query(Location).filter(Location.name == "Community Center").first()

        if alice and achieva_hq and not session.query(ClientLocation).filter(
            ClientLocation.client_id == alice.user_id,
            ClientLocation.location_id == achieva_hq.location_id,
        ).first():
            session.add(
                ClientLocation(
                    client_id=alice.user_id,
                    location_id=achieva_hq.location_id,
                    location_type="home",
                    is_verified=True,
                )
            )

        if alice and giant_eagle and not session.query(ClientLocation).filter(
            ClientLocation.client_id == alice.user_id,
            ClientLocation.location_id == giant_eagle.location_id,
        ).first():
            session.add(
                ClientLocation(
                    client_id=alice.user_id,
                    location_id=giant_eagle.location_id,
                    location_type="work",
                    is_verified=True,
                )
            )

        if alice and community_center and not session.query(ClientLocation).filter(
            ClientLocation.client_id == alice.user_id,
            ClientLocation.location_id == community_center.location_id,
        ).first():
            session.add(
                ClientLocation(
                    client_id=alice.user_id,
                    location_id=community_center.location_id,
                    location_type="volunteer",
                    is_verified=True,
                )
            )
        session.commit()

        available_drivers = session.query(User).filter(User.role == "driver", User.is_active == True).all()
        for driver in available_drivers:
            existing_availability = session.query(DriverAvailability).filter(
                DriverAvailability.driver_id == driver.user_id
            ).first()
            if not existing_availability:
                session.add(DriverAvailability(driver_id=driver.user_id, is_available=True))
        session.commit()

        if alice:
            client_locations = session.query(ClientLocation).filter(
                ClientLocation.client_id == alice.user_id
            ).order_by(ClientLocation.client_location_id.asc()).all()
            by_type = {client_location.location_type: client_location for client_location in client_locations}
            home_location = by_type.get("home")
            work_location = by_type.get("work")
            volunteer_location = by_type.get("volunteer")
            tomorrow = datetime.utcnow().date() + timedelta(days=1)

            demo_rides = [
                ("DEMO_TOMORROW_1", home_location, work_location, 8, 0),
                ("DEMO_TOMORROW_2", work_location, home_location, 9, 0),
                ("DEMO_TOMORROW_3", home_location, volunteer_location, 10, 30),
                ("DEMO_TOMORROW_4", volunteer_location, home_location, 13, 0),
            ]

            for label, pickup_client_location, dropoff_client_location, hour, minute in demo_rides:
                if not pickup_client_location or not dropoff_client_location:
                    continue
                existing_ride = session.query(RideRequest).filter(
                    RideRequest.api_shipment_label == label
                ).first()
                if existing_ride:
                    continue

                pickup_start = datetime.combine(tomorrow, datetime.min.time()).replace(
                    hour=hour,
                    minute=minute,
                )
                pickup_end = pickup_start + timedelta(minutes=45)
                dropoff_start = pickup_end + timedelta(minutes=30)
                dropoff_end = dropoff_start + timedelta(minutes=45)

                session.add(
                    RideRequest(
                        passenger_id=alice.user_id,
                        pickup_client_location_id=pickup_client_location.client_location_id,
                        dropoff_client_location_id=dropoff_client_location.client_location_id,
                        ride_date=tomorrow,
                        pickup_window_start=pickup_start,
                        pickup_window_end=pickup_end,
                        dropoff_window_start=dropoff_start,
                        dropoff_window_end=dropoff_end,
                        status="requested",
                        api_shipment_label=label,
                    )
                )
            session.commit()


def ensure_database_ready(retries: int = 10, delay_seconds: int = 5) -> None:
    """
    Ensure tables exist and seed demo data, retrying while SQL Server starts.
    """
    engine = get_engine()
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            seed_data()
            print("Application connected to DB and tables ensured.")
            return
        except (InterfaceError, OperationalError) as exc:
            last_error = exc
            retries_left = retries - attempt - 1
            if retries_left <= 0:
                break
            print(f"Waiting for SQL Server... {retries_left} retries left.")
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error
