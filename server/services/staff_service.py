"""
Staff service layer.

Bare-minimum in-memory persistence while we iterate quickly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class PermanentLocation:
    id: str
    label: str
    address: str


@dataclass
class Client:
    id: str
    full_name: str
    phone: str | None = None
    email: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z")
    permanent_locations: list[PermanentLocation] = field(default_factory=list)


# In-memory store (temporary). Replace with SQL Server persistence later.
_CLIENTS: dict[str, Client] = {}


def create_client(data: dict) -> dict:
    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    email = (data.get("email") or "").strip() or None

    client_id = str(uuid4())
    client = Client(id=client_id, full_name=full_name, phone=phone, email=email)
    _CLIENTS[client_id] = client

    return {"message": "Client created", "client": asdict(client)}


def list_clients() -> dict:
    clients = [asdict(c) for c in _CLIENTS.values()]
    clients.sort(key=lambda c: c["created_at"])
    return {"clients": clients}


def get_client(client_id: str) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}
    return {"client": asdict(client)}


def update_client(client_id: str, data: dict) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}

    if "full_name" in data:
        client.full_name = (data.get("full_name") or "").strip()
    if "phone" in data:
        client.phone = (data.get("phone") or "").strip() or None
    if "email" in data:
        client.email = (data.get("email") or "").strip() or None

    return {"message": "Client updated", "client": asdict(client)}


def add_permanent_location(client_id: str, data: dict) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}

    label = (data.get("label") or "").strip()
    address = (data.get("address") or "").strip()

    location = PermanentLocation(id=str(uuid4()), label=label, address=address)
    client.permanent_locations.append(location)

    return {"message": "Permanent location added", "location": asdict(location)}


def list_permanent_locations(client_id: str) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}
    return {"locations": [asdict(l) for l in client.permanent_locations]}


def update_permanent_location(client_id: str, location_id: str, data: dict) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}

    location = next((l for l in client.permanent_locations if l.id == location_id), None)
    if not location:
        return {"error": "Location not found", "code": "location_not_found"}

    if "label" in data:
        location.label = (data.get("label") or "").strip()

    if "address" in data:
        location.address = (data.get("address") or "").strip()

    return {"message": "Permanent location updated", "location": asdict(location)}


def delete_permanent_location(client_id: str, location_id: str) -> dict:
    client = _CLIENTS.get(client_id)
    if not client:
        return {"error": "Client not found", "code": "not_found"}

    before = len(client.permanent_locations)
    client.permanent_locations = [l for l in client.permanent_locations if l.id != location_id]
    if len(client.permanent_locations) == before:
        return {"error": "Location not found", "code": "location_not_found"}

    return {"message": "Permanent location deleted", "location_id": location_id}

