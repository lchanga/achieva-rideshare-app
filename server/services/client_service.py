from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
from server.models.ride_request import RideRequest as RideRequestModel


APP_TIMEZONE = ZoneInfo("America/New_York")
CUTOFF_HOUR = 20


def _parse_ts(ts_str: str | None) -> datetime | None:
    """Convert ISO-like strings to datetimes, tolerating Z suffixes."""
    if not ts_str:
        return None

    clean_ts = ts_str.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(clean_ts)
    except ValueError:
        try:
            return datetime.strptime(clean_ts[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str[:10])
    except ValueError:
        return None


def _coerce_ride_id(ride_id: str) -> int | None:
    try:
        return int(ride_id)
    except (TypeError, ValueError):
        return None


def _default_windows(data: dict) -> tuple[date, datetime, datetime, datetime, datetime]:
    pickup_start = _parse_ts(data.get("pickup_window_start")) or datetime.utcnow()
    pickup_end = _parse_ts(data.get("pickup_window_end")) or pickup_start + timedelta(hours=1)
    dropoff_start = _parse_ts(data.get("dropoff_window_start")) or pickup_end
    dropoff_end = _parse_ts(data.get("dropoff_window_end")) or dropoff_start + timedelta(hours=1)
    ride_date = _parse_date(data.get("date")) or pickup_start.date()
    return ride_date, pickup_start, pickup_end, dropoff_start, dropoff_end


def _serialize_ride(ride: RideRequestModel) -> dict:
    return {
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


def _validate_submission_cutoff(ride_date: date) -> dict | None:
    now_local = datetime.now(APP_TIMEZONE)
    cutoff_local = datetime.combine(
        ride_date - timedelta(days=1),
        datetime.min.time().replace(hour=CUTOFF_HOUR),
        tzinfo=APP_TIMEZONE,
    )
    if now_local > cutoff_local:
        return {
            "error": "Ride requests must be submitted by 8:00 PM America/New_York on the night before the ride.",
            "code": "cutoff_passed",
            "cutoff": cutoff_local.isoformat(),
        }
    return None


def create_ride_request(data: dict) -> dict:
    ride_date, pickup_start, pickup_end, dropoff_start, dropoff_end = _default_windows(data)
    cutoff_error = _validate_submission_cutoff(ride_date)
    if cutoff_error:
        return cutoff_error

    try:
        with Session(get_engine()) as session:
            new_ride = RideRequestModel(
                passenger_id=data["passenger_id"],
                pickup_client_location_id=data["pickup_location_id"],
                dropoff_client_location_id=data["dropoff_location_id"],
                ride_date=ride_date,
                pickup_window_start=pickup_start,
                pickup_window_end=pickup_end,
                dropoff_window_start=dropoff_start,
                dropoff_window_end=dropoff_end,
                status="requested",
                api_shipment_label=f"PWA_{datetime.utcnow().strftime('%H%M%S')}",
            )
            session.add(new_ride)
            session.commit()
            session.refresh(new_ride)
            return {"message": "Ride request created", "ride": _serialize_ride(new_ride)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "code": "db_failure"}


def list_ride_requests_for_client(client_id: str) -> dict:
    try:
        passenger_id = int(client_id)
    except (TypeError, ValueError):
        return {"error": "Client not found", "code": "not_found"}

    with Session(get_engine()) as session:
        stmt = (
            select(RideRequestModel)
            .where(RideRequestModel.passenger_id == passenger_id)
            .order_by(RideRequestModel.ride_date.desc(), RideRequestModel.request_id.desc())
        )
        results = session.execute(stmt).scalars().all()
        return {"rides": [_serialize_ride(ride) for ride in results]}


def get_ride_request(ride_id: str) -> dict:
    ride_pk = _coerce_ride_id(ride_id)
    if ride_pk is None:
        return {"error": "Ride request not found", "code": "not_found"}

    with Session(get_engine()) as session:
        ride = session.get(RideRequestModel, ride_pk)
        if not ride:
            return {"error": "Ride request not found", "code": "not_found"}
        return {"ride": _serialize_ride(ride)}


def update_ride_request(ride_id: str, data: dict) -> dict:
    ride_pk = _coerce_ride_id(ride_id)
    if ride_pk is None:
        return {"error": "Ride request not found", "code": "not_found"}

    try:
        with Session(get_engine()) as session:
            ride = session.get(RideRequestModel, ride_pk)
            if not ride:
                return {"error": "Ride request not found", "code": "not_found"}

            target_ride_date = ride.ride_date

            if "passenger_id" in data:
                ride.passenger_id = data["passenger_id"]
            if "pickup_location_id" in data:
                ride.pickup_client_location_id = data["pickup_location_id"]
            if "dropoff_location_id" in data:
                ride.dropoff_client_location_id = data["dropoff_location_id"]
            if "date" in data:
                parsed_date = _parse_date(data.get("date"))
                if parsed_date is None:
                    return {"error": "Invalid date format.", "code": "invalid_request"}
                target_ride_date = parsed_date

            cutoff_error = _validate_submission_cutoff(target_ride_date)
            if cutoff_error:
                return cutoff_error

            ride.ride_date = target_ride_date

            for field_name in (
                "pickup_window_start",
                "pickup_window_end",
                "dropoff_window_start",
                "dropoff_window_end",
            ):
                if field_name in data:
                    parsed_ts = _parse_ts(data.get(field_name))
                    if parsed_ts is None:
                        return {"error": f"Invalid timestamp for {field_name}.", "code": "invalid_request"}
                    setattr(ride, field_name, parsed_ts)

            session.commit()
            session.refresh(ride)
            return {"message": "Ride request updated", "ride": _serialize_ride(ride)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "code": "db_failure"}


def list_client_permanent_locations(client_id: str) -> dict:
    from server.services.staff_service import list_permanent_locations

    return list_permanent_locations(client_id)


def delete_ride_request(ride_id: str) -> dict:
    ride_pk = _coerce_ride_id(ride_id)
    if ride_pk is None:
        return {"error": "Ride request not found", "code": "not_found"}

    with Session(get_engine()) as session:
        ride = session.get(RideRequestModel, ride_pk)
        if not ride:
            return {"error": "Ride request not found", "code": "not_found"}

        if ride.status != "requested":
            return {
                "error": "Ride request can only be cancelled before it is scheduled.",
                "code": "cannot_cancel_scheduled_ride",
            }

        ride.status = "cancelled_by_passenger"
        session.commit()
        return {"message": "Ride request cancelled", "ride_id": ride_id}