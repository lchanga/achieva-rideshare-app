from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from server.optimizer.base import Optimizer

# Deterministic constants for the fake schedule.
TRAVEL_TIME = timedelta(minutes=10)
SERVICE_TIME = timedelta(minutes=2)
METERS_PER_LEG = 1000


def _duration(td: timedelta) -> str:
    return f"{int(td.total_seconds())}s"


def _parse_ts(value: str | None) -> datetime | None:
    """
    Parse RFC3339 timestamps to an aware UTC datetime.
    Accepts Z-suffix and fractional seconds (truncated to microseconds).
    """
    if not value or not isinstance(value, str):
        return None
    ts = value.strip()
    if not ts:
        return None

    # datetime.fromisoformat doesn't accept trailing "Z".
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    # Truncate/pad fractional seconds to microseconds.
    if "." in ts:
        head, rest = ts.split(".", 1)
        frac = rest
        offset = ""
        for sign in ("+", "-"):
            if sign in rest:
                frac, offset = rest.split(sign, 1)
                offset = sign + offset
                break
        frac = (frac + "000000")[:6]
        ts = f"{head}.{frac}{offset}"

    try:
        return datetime.fromisoformat(ts).astimezone(timezone.utc)
    except ValueError:
        return None


def _fmt_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _first_time_window(visit_request: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    tw = (visit_request.get("timeWindows") or [None])[0] or {}
    return _parse_ts(tw.get("startTime")), _parse_ts(tw.get("endTime"))


@dataclass(frozen=True)
class _Stop:
    shipment_index: int
    is_pickup: bool
    shipment_label: str | None
    tw_start: datetime | None
    tw_end: datetime | None


def _sort_key(stop: _Stop) -> tuple[int, int, int]:
    # None sorts last; stable by shipment index.
    if stop.tw_start is None:
        return (1, 0, stop.shipment_index)
    return (0, int(stop.tw_start.timestamp()), stop.shipment_index)


class FakeOptimizer(Optimizer):
    """
    Fake optimizer that returns a Google-like OptimizeToursResponse.

    Reference: https://developers.google.com/maps/documentation/route-optimization/interpret-response
    """

    def optimize_tours(self, request_json: dict) -> dict:
        model = request_json.get("model") or {}
        shipments = model.get("shipments") or []
        vehicles = model.get("vehicles") or []

        req_label = request_json.get("label") if isinstance(request_json.get("label"), str) else None

        if not vehicles:
            skipped = []
            for i, s in enumerate(shipments):
                s = s or {}
                skipped.append(
                    {
                        "index": i,
                        "label": (s.get("label") or "") if isinstance(s.get("label"), str) else "",
                        "reasons": [{"code": "NO_VEHICLE"}],
                    }
                )

            resp: dict[str, Any] = {
                "routes": [],
                "skippedShipments": skipped,
                "validationErrors": [
                    {
                        "code": 1,
                        "displayName": "NO_VEHICLE",
                        "errorMessage": "No vehicles provided",
                        "fields": [{"name": "model", "subField": {"name": "vehicles"}}],
                    }
                ],
                "metrics": {
                    "aggregatedRouteMetrics": {
                        "performedShipmentCount": 0,
                        "travelDuration": "0s",
                        "waitDuration": "0s",
                        "delayDuration": "0s",
                        "breakDuration": "0s",
                        "visitDuration": "0s",
                        "totalDuration": "0s",
                        "travelDistanceMeters": 0,
                    },
                    "usedVehicleCount": 0,
                    "skippedMandatoryShipmentCount": 0,
                    "costs": {},
                    "totalCost": 0,
                },
            }
            if req_label:
                resp["requestLabel"] = req_label
            return resp

        v0 = vehicles[0] or {}
        v0_label = v0.get("label") if isinstance(v0.get("label"), str) else None

        start_tw = (v0.get("startTimeWindows") or [None])[0] or {}
        route_start_raw = start_tw.get("startTime") or model.get("globalStartTime")
        route_start = _parse_ts(route_start_raw) or datetime.now(timezone.utc)

        pickups: list[_Stop] = []
        deliveries: list[_Stop] = []
        skipped_shipments: list[dict[str, Any]] = []

        for s_idx, shipment in enumerate(shipments):
            shipment = shipment or {}
            shipment_label = shipment.get("label") if isinstance(shipment.get("label"), str) else None

            pickup_reqs = shipment.get("pickups") or []
            delivery_reqs = shipment.get("deliveries") or []

            if pickup_reqs:
                vr = pickup_reqs[0] or {}
                tw_s, tw_e = _first_time_window(vr)
                pickups.append(_Stop(s_idx, True, shipment_label, tw_s, tw_e))

            if delivery_reqs:
                vr = delivery_reqs[0] or {}
                tw_s, tw_e = _first_time_window(vr)
                deliveries.append(_Stop(s_idx, False, shipment_label, tw_s, tw_e))

            if not pickup_reqs and not delivery_reqs:
                skipped_shipments.append(
                    {"index": s_idx, "label": shipment_label or "", "reasons": [{"code": "NO_VISIT_REQUEST"}]}
                )

        ordered = sorted(pickups, key=_sort_key) + sorted(deliveries, key=_sort_key)

        current = route_start
        visits: list[dict[str, Any]] = []
        transitions: list[dict[str, Any]] = []

        total_travel = timedelta(0)
        total_wait = timedelta(0)
        total_visit = timedelta(0)
        total_distance = 0

        for stop in ordered:
            transition_start = current

            # Travel.
            current += TRAVEL_TIME
            total_travel += TRAVEL_TIME
            total_distance += METERS_PER_LEG

            # Wait until time window opens.
            wait = timedelta(0)
            if stop.tw_start and current < stop.tw_start:
                wait = stop.tw_start - current
                current = stop.tw_start
                total_wait += wait

            transitions.append(
                {
                    "startTime": _fmt_ts(transition_start),
                    "travelDuration": _duration(TRAVEL_TIME),
                    "travelDistanceMeters": METERS_PER_LEG,
                    "waitDuration": _duration(wait),
                    "delayDuration": "0s",
                    "breakDuration": "0s",
                    "totalDuration": _duration(TRAVEL_TIME + wait),
                }
            )

            # Visit.
            visit: dict[str, Any] = {"shipmentIndex": stop.shipment_index, "startTime": _fmt_ts(current)}
            if stop.is_pickup:
                visit["isPickup"] = True  # omit when false to match proto JSON defaults
            if stop.shipment_label:
                visit["shipmentLabel"] = stop.shipment_label
            visits.append(visit)

            current += SERVICE_TIME
            total_visit += SERVICE_TIME

        # Final transition.
        final_start = current
        current += TRAVEL_TIME
        total_travel += TRAVEL_TIME
        total_distance += METERS_PER_LEG if ordered else 0
        transitions.append(
            {
                "startTime": _fmt_ts(final_start),
                "travelDuration": _duration(TRAVEL_TIME),
                "travelDistanceMeters": (METERS_PER_LEG if ordered else 0),
                "waitDuration": "0s",
                "delayDuration": "0s",
                "breakDuration": "0s",
                "totalDuration": _duration(TRAVEL_TIME),
            }
        )

        performed_shipment_count = len({v["shipmentIndex"] for v in visits})
        route_metrics = {
            "performedShipmentCount": performed_shipment_count,
            "travelDuration": _duration(total_travel),
            "waitDuration": _duration(total_wait),
            "delayDuration": "0s",
            "breakDuration": "0s",
            "visitDuration": _duration(total_visit),
            "totalDuration": _duration(current - route_start),
            "travelDistanceMeters": total_distance,
        }

        route0: dict[str, Any] = {
            "vehicleStartTime": _fmt_ts(route_start),
            "vehicleEndTime": _fmt_ts(current),
            "visits": visits,
            "transitions": transitions,
            "metrics": route_metrics,
            "routeCosts": {},
            "routeTotalCost": 0,
            "hasTrafficInfeasibilities": False,
        }
        if v0_label:
            route0["vehicleLabel"] = v0_label

        routes: list[dict[str, Any]] = [route0]

        # Add empty routes for remaining vehicles (keeps response predictable).
        for v_idx, vehicle in enumerate(vehicles[1:], start=1):
            vehicle = vehicle or {}
            v_label = vehicle.get("label") if isinstance(vehicle.get("label"), str) else None
            start_tw_v = (vehicle.get("startTimeWindows") or [None])[0] or {}
            st_raw = start_tw_v.get("startTime") or model.get("globalStartTime")
            st = _parse_ts(st_raw) or route_start

            r: dict[str, Any] = {
                "vehicleIndex": v_idx,
                "vehicleStartTime": _fmt_ts(st),
                "vehicleEndTime": _fmt_ts(st),
                "visits": [],
                "transitions": [
                    {
                        "startTime": _fmt_ts(st),
                        "travelDuration": "0s",
                        "travelDistanceMeters": 0,
                        "waitDuration": "0s",
                        "delayDuration": "0s",
                        "breakDuration": "0s",
                        "totalDuration": "0s",
                    }
                ],
                "metrics": {
                    "performedShipmentCount": 0,
                    "travelDuration": "0s",
                    "waitDuration": "0s",
                    "delayDuration": "0s",
                    "breakDuration": "0s",
                    "visitDuration": "0s",
                    "totalDuration": "0s",
                    "travelDistanceMeters": 0,
                },
                "routeCosts": {},
                "routeTotalCost": 0,
                "hasTrafficInfeasibilities": False,
            }
            if v_label:
                r["vehicleLabel"] = v_label
            routes.append(r)

        top_metrics: dict[str, Any] = {
            "aggregatedRouteMetrics": route_metrics,
            "usedVehicleCount": (1 if visits else 0),
            "skippedMandatoryShipmentCount": 0,
            "costs": {},
            "totalCost": 0,
        }
        if visits:
            top_metrics["earliestVehicleStartTime"] = _fmt_ts(route_start)
            top_metrics["latestVehicleEndTime"] = _fmt_ts(current)

        resp = {
            "routes": routes,
            "skippedShipments": skipped_shipments,
            "validationErrors": [],
            "metrics": top_metrics,
        }
        if req_label:
            resp["requestLabel"] = req_label
        return resp

