from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from server.db import get_engine
from server.models.client_location import ClientLocation
from server.models.driver_availability import DriverAvailability
from server.models.location import Location
from server.models.optimized_route import OptimizedRoute
from server.models.ride_request import RideRequest as RideRequestModel
from server.models.route_stop import RouteStop
from server.models.user import User


def _coerce_id(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in (full_name or "").strip().split() if part]
    if not parts:
        return "Unknown", "Client"
    if len(parts) == 1:
        return parts[0], "Client"
    return parts[0], " ".join(parts[1:])


def _format_full_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip()


def _serialize_location(client_location: ClientLocation) -> dict:
    location = client_location.location
    return {
        "id": str(client_location.client_location_id),
        "label": location.name if location else client_location.location_type.title(),
        "address": location.address if location else "",
    }


def _serialize_client(user: User, client_locations: list[ClientLocation]) -> dict:
    return {
        "id": str(user.user_id),
        "full_name": _format_full_name(user),
        "phone": user.phone,
        "email": user.email,
        "created_at": None,
        "permanent_locations": [_serialize_location(client_location) for client_location in client_locations],
    }


def _serialize_driver_availability(driver_availability: DriverAvailability, driver: User) -> dict:
    return {
        "availability_id": driver_availability.availability_id,
        "driver_id": driver.user_id,
        "full_name": _format_full_name(driver),
        "email": driver.email,
        "is_available": driver_availability.is_available,
    }


def create_client(data: dict) -> dict:
    first_name, last_name = _split_full_name(data.get("full_name", ""))

    try:
        with Session(get_engine()) as session:
            new_client = User(
                first_name=first_name,
                last_name=last_name,
                email=data.get("email"),
                phone=data.get("phone"),
                role="client",
            )
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            return {
                "message": "Client created in database",
                "client": _serialize_client(new_client, []),
            }
    except Exception as e:
        return {"error": f"DB Error: {str(e)}", "code": "db_failure"}


def list_clients() -> dict:
    with Session(get_engine()) as session:
        clients = session.execute(select(User).where(User.role == "client").order_by(User.user_id.asc())).scalars().all()
        client_ids = [client.user_id for client in clients]
        locations = (
            session.execute(
                select(ClientLocation)
                .options(joinedload(ClientLocation.location))
                .where(ClientLocation.client_id.in_(client_ids))
            ).scalars().all()
            if client_ids
            else []
        )

        by_client_id: dict[int, list[ClientLocation]] = {}
        for client_location in locations:
            by_client_id.setdefault(client_location.client_id, []).append(client_location)

        return {
            "clients": [
                _serialize_client(client, by_client_id.get(client.user_id, []))
                for client in clients
            ]
        }


def get_client(client_id: str) -> dict:
    client_pk = _coerce_id(client_id)
    if client_pk is None:
        return {"error": "Client not found", "code": "not_found"}

    with Session(get_engine()) as session:
        client = session.get(User, client_pk)
        if not client or client.role != "client":
            return {"error": "Client not found", "code": "not_found"}

        client_locations = session.execute(
            select(ClientLocation)
            .options(joinedload(ClientLocation.location))
            .where(ClientLocation.client_id == client_pk)
            .order_by(ClientLocation.client_location_id.asc())
        ).scalars().all()
        return {"client": _serialize_client(client, client_locations)}


def delete_client(client_id: str) -> dict:
    client_pk = _coerce_id(client_id)
    if client_pk is None:
        return {"error": "Client not found", "code": "not_found"}

    with Session(get_engine()) as session:
        client = session.get(User, client_pk)
        if not client or client.role != "client":
            return {"error": "Client not found", "code": "not_found"}

        # Optionally, cascade delete associated locations if needed.
        client_locations = session.execute(
            select(ClientLocation).where(ClientLocation.client_id == client_pk)
        ).scalars().all()
        for client_location in client_locations:
            location = session.get(Location, client_location.location_id)
            session.delete(client_location)
            if location is not None:
                session.delete(location)

        session.delete(client)
        session.commit()
        return {"message": "Client deleted", "client_id": str(client_pk)}


def update_client(client_id: str, data: dict) -> dict:
    client_pk = _coerce_id(client_id)
    if client_pk is None:
        return {"error": "Client not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            client = session.get(User, client_pk)
            if not client or client.role != "client":
                return {"error": "Client not found", "code": "not_found"}

            if "full_name" in data:
                client.first_name, client.last_name = _split_full_name(data.get("full_name", ""))
            if "phone" in data:
                client.phone = data.get("phone")
            if "email" in data:
                client.email = data.get("email")

            session.commit()

            client_locations = session.execute(
                select(ClientLocation)
                .options(joinedload(ClientLocation.location))
                .where(ClientLocation.client_id == client_pk)
                .order_by(ClientLocation.client_location_id.asc())
            ).scalars().all()
            return {"message": "Client updated", "client": _serialize_client(client, client_locations)}
    except Exception as e:
        return {"error": f"DB Error: {str(e)}", "code": "db_failure"}


def add_permanent_location(client_id: str, data: dict) -> dict:
    client_pk = _coerce_id(client_id)
    if client_pk is None:
        return {"error": "Client not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            client = session.get(User, client_pk)
            if not client or client.role != "client":
                return {"error": "Client not found", "code": "not_found"}

            location = Location(
                name=data.get("label") or "Saved location",
                address=data.get("address") or "",
                city="Pittsburgh",
                zip="00000",
                latitude=0.0,
                longitude=0.0,
            )
            session.add(location)
            session.flush()

            client_location = ClientLocation(
                client_id=client_pk,
                location_id=location.location_id,
                location_type="home",
                is_verified=False,
            )
            session.add(client_location)
            session.commit()
            session.refresh(client_location)
            session.refresh(location)
            return {"message": "Location saved to SQL Server", "location": _serialize_location(client_location)}
    except Exception as e:
        return {"error": str(e), "code": "db_failure"}


def list_permanent_locations(client_id: str) -> dict:
    client_pk = _coerce_id(client_id)
    if client_pk is None:
        return {"error": "Client not found", "code": "not_found"}

    with Session(get_engine()) as session:
        client = session.get(User, client_pk)
        if not client or client.role != "client":
            return {"error": "Client not found", "code": "not_found"}

        results = session.execute(
            select(ClientLocation)
            .options(joinedload(ClientLocation.location))
            .where(ClientLocation.client_id == client_pk)
            .order_by(ClientLocation.client_location_id.asc())
        ).scalars().all()
        return {"locations": [_serialize_location(client_location) for client_location in results]}


def update_permanent_location(client_id: str, location_id: str, data: dict) -> dict:
    client_pk = _coerce_id(client_id)
    location_pk = _coerce_id(location_id)
    if client_pk is None or location_pk is None:
        return {"error": "Location not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            client_location = session.execute(
                select(ClientLocation)
                .options(joinedload(ClientLocation.location))
                .where(
                    ClientLocation.client_id == client_pk,
                    ClientLocation.client_location_id == location_pk,
                )
            ).scalar_one_or_none()
            if not client_location:
                return {"error": "Location not found", "code": "not_found"}

            if "label" in data and client_location.location:
                client_location.location.name = data.get("label") or client_location.location.name
            if "address" in data and client_location.location:
                client_location.location.address = data.get("address") or client_location.location.address

            session.commit()
            return {"message": "Location updated", "location": _serialize_location(client_location)}
    except Exception as e:
        return {"error": str(e), "code": "db_failure"}


def delete_permanent_location(client_id: str, location_id: str) -> dict:
    client_pk = _coerce_id(client_id)
    location_pk = _coerce_id(location_id)
    if client_pk is None or location_pk is None:
        return {"error": "Location not found", "code": "not_found"}

    with Session(get_engine()) as session:
        client_location = session.execute(
            select(ClientLocation)
            .where(
                ClientLocation.client_id == client_pk,
                ClientLocation.client_location_id == location_pk,
            )
        ).scalar_one_or_none()
        if not client_location:
            return {"error": "Location not found", "code": "not_found"}

        location = session.get(Location, client_location.location_id)
        session.delete(client_location)
        if location is not None:
            session.delete(location)
        session.commit()
        return {"message": "Location deleted", "location_id": location_id}


def list_driver_availability() -> dict:
    with Session(get_engine()) as session:
        availabilities = session.execute(
            select(DriverAvailability, User)
            .join(User, User.user_id == DriverAvailability.driver_id)
            .where(User.role == "driver")
            .order_by(User.user_id.asc())
        ).all()
        return {
            "drivers": [
                _serialize_driver_availability(driver_availability, driver)
                for driver_availability, driver in availabilities
            ]
        }


def create_driver_availability(data: dict) -> dict:
    driver_pk = data.get("driver_id")
    try:
        with Session(get_engine()) as session:
            driver = session.get(User, driver_pk)
            if not driver or driver.role != "driver":
                return {"error": "Driver not found", "code": "not_found"}

            existing = session.execute(
                select(DriverAvailability).where(DriverAvailability.driver_id == driver_pk)
            ).scalar_one_or_none()
            if existing:
                return {"error": "Driver availability already exists", "code": "already_exists"}

            availability = DriverAvailability(
                driver_id=driver_pk,
                is_available=data.get("is_available", True),
            )
            session.add(availability)
            session.commit()
            session.refresh(availability)
            return {
                "message": "Driver availability created",
                "driver": _serialize_driver_availability(availability, driver),
            }
    except Exception as e:
        return {"error": f"DB Error: {str(e)}", "code": "db_failure"}


def update_driver_availability(driver_id: str, data: dict) -> dict:
    driver_pk = _coerce_id(driver_id)
    if driver_pk is None:
        return {"error": "Driver not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            availability = session.execute(
                select(DriverAvailability).where(DriverAvailability.driver_id == driver_pk)
            ).scalar_one_or_none()
            driver = session.get(User, driver_pk)
            if not availability or not driver or driver.role != "driver":
                return {"error": "Driver availability not found", "code": "not_found"}

            availability.is_available = data["is_available"]
            session.commit()
            return {
                "message": "Driver availability updated",
                "driver": _serialize_driver_availability(availability, driver),
            }
    except Exception as e:
        return {"error": f"DB Error: {str(e)}", "code": "db_failure"}

def list_routes() -> dict:
    with Session(get_engine()) as session:
        routes = (
            session.execute(
                select(OptimizedRoute).order_by(
                    OptimizedRoute.route_date.desc(), OptimizedRoute.route_id.desc()
                )
            )
            .scalars()
            .all()
        )

        route_ids = [route.route_id for route in routes]
        stops = (
            session.execute(
                select(RouteStop)
                .where(RouteStop.route_id.in_(route_ids))
                .order_by(RouteStop.route_id.asc(), RouteStop.stop_sequence.asc())
            )
            .scalars()
            .all()
            if route_ids
            else []
        )
        by_route: dict[int, list[RouteStop]] = {}
        for stop in stops:
            by_route.setdefault(stop.route_id, []).append(stop)

        return {
            "routes": [
                {
                    "id": str(route.route_id),
                    "status": route.status,
                    "driver_id": str(route.driver_id) if route.driver_id is not None else None,
                    "route_date": route.route_date.isoformat() if route.route_date else None,
                    "accepted_at": route.accepted_at.isoformat() if route.accepted_at else None,
                    "stop_count": len(by_route.get(route.route_id, [])),
                }
                for route in routes
            ]
        }


def list_ride_requests_admin() -> dict:
    with Session(get_engine()) as session:
        stmt = select(RideRequestModel).order_by(
            RideRequestModel.ride_date.desc(), RideRequestModel.request_id.desc()
        )
        results = session.execute(stmt).scalars().all()
        return {
            "rides": [
                {
                    "id": str(ride.request_id),
                    "passenger_id": ride.passenger_id,
                    "pickup_location_id": ride.pickup_client_location_id,
                    "dropoff_location_id": ride.dropoff_client_location_id,
                    "date": ride.ride_date.isoformat() if ride.ride_date else None,
                    "pickup_window_start": ride.pickup_window_start.isoformat() if ride.pickup_window_start else None,
                    "pickup_window_end": ride.pickup_window_end.isoformat() if ride.pickup_window_end else None,
                    "dropoff_window_start": ride.dropoff_window_start.isoformat() if ride.dropoff_window_start else None,
                    "dropoff_window_end": ride.dropoff_window_end.isoformat() if ride.dropoff_window_end else None,
                    "status": ride.status,
                    "created_at": ride.created_at.isoformat() if ride.created_at else None,
                    "api_shipment_label": ride.api_shipment_label,
                }
                for ride in results
            ]
        }


def get_ride_request_admin(ride_id: str) -> dict:
    try:
        ride_pk = int(ride_id)
    except (TypeError, ValueError):
        return {"error": "Ride request not found", "code": "not_found"}

    with Session(get_engine()) as session:
        ride = session.get(RideRequestModel, ride_pk)
        if not ride:
            return {"error": "Ride request not found", "code": "not_found"}

        return {
            "ride": {
                "id": str(ride.request_id),
                "passenger_id": ride.passenger_id,
                "pickup_location_id": ride.pickup_client_location_id,
                "dropoff_location_id": ride.dropoff_client_location_id,
                "date": ride.ride_date.isoformat() if ride.ride_date else None,
                "pickup_window_start": ride.pickup_window_start.isoformat() if ride.pickup_window_start else None,
                "pickup_window_end": ride.pickup_window_end.isoformat() if ride.pickup_window_end else None,
                "dropoff_window_start": ride.dropoff_window_start.isoformat() if ride.dropoff_window_start else None,
                "dropoff_window_end": ride.dropoff_window_end.isoformat() if ride.dropoff_window_end else None,
                "status": ride.status,
                "created_at": ride.created_at.isoformat() if ride.created_at else None,
                "api_shipment_label": ride.api_shipment_label,
            }
        }