from __future__ import annotations

from typing import Any

from server.optimizer.base import Optimizer

def _get_start_time(visit_request: dict[str, Any]) -> str:
    """
    Pull a displayable time from the first time window (if present).
    """
    tw = (visit_request.get("timeWindows") or [None])[0] or {}
    start = tw.get("startTime")
    return start if isinstance(start, str) else ""


class FakeOptimizer(Optimizer):
    """
    Minimal fake optimizer.

    It returns only what our frontend needs:
    - routes[0].visits[] with shipmentIndex/isPickup/startTime (and shipmentLabel if present)
    """

    def optimize_tours(self, request_json: dict) -> dict:
        model = request_json.get("model") or {}
        shipments = model.get("shipments") or []
        vehicles = model.get("vehicles") or []

        routes: list[dict[str, Any]] = []
        if vehicles:
            v0 = vehicles[0] or {}
            v0_label = v0.get("label") if isinstance(v0.get("label"), str) else None

            visits: list[dict[str, Any]] = []
            for s_idx, shipment in enumerate(shipments):
                shipment = shipment or {}
                shipment_label = shipment.get("label") if isinstance(shipment.get("label"), str) else None

                pickup_reqs = shipment.get("pickups") or []
                if pickup_reqs:
                    vr = pickup_reqs[0] or {}
                    visit = {
                        "shipmentIndex": s_idx,
                        "isPickup": True,
                        "startTime": _get_start_time(vr),
                    }
                    if shipment_label:
                        visit["shipmentLabel"] = shipment_label
                    visits.append(visit)

                delivery_reqs = shipment.get("deliveries") or []
                if delivery_reqs:
                    vr = delivery_reqs[0] or {}
                    visit = {
                        "shipmentIndex": s_idx,
                        "isPickup": False,
                        "startTime": _get_start_time(vr),
                    }
                    if shipment_label:
                        visit["shipmentLabel"] = shipment_label
                    visits.append(visit)

            route0: dict[str, Any] = {"visits": visits}
            if v0_label:
                route0["vehicleLabel"] = v0_label
            routes.append(route0)

            # Stub out remaining vehicles so the response shape is stable.
            for v_idx, vehicle in enumerate(vehicles[1:], start=1):
                vehicle = vehicle or {}
                v_label = vehicle.get("label") if isinstance(vehicle.get("label"), str) else None
                r: dict[str, Any] = {"vehicleIndex": v_idx, "visits": []}
                if v_label:
                    r["vehicleLabel"] = v_label
                routes.append(r)

        response: dict[str, Any] = {"routes": routes}
        label = request_json.get("label")
        if isinstance(label, str) and label:
            response["requestLabel"] = label
        return response

