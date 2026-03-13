from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
# Import the models that match your SQL Server tables
from server.models.user import User as ClientModel  # In your schema, Clients are usually Users
from server.models.client_location import ClientLocation as LocationModel

def create_client(data: dict) -> dict:
    engine = get_engine()
    try:
        with Session(engine) as session:
            new_client = ClientModel(
                full_name=data.get("full_name"),
                email=data.get("email"),
                phone_number=data.get("phone"),
                role="client",  # Assuming a 'role' column exists
                created_at=datetime.utcnow()
            )
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            
            return {
                "message": "Client created in database",
                "client": {"id": str(new_client.user_id), "full_name": new_client.full_name}
            }
    except Exception as e:
        return {"error": f"DB Error: {str(e)}", "code": "db_failure"}

def list_clients() -> dict:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(ClientModel).where(ClientModel.role == "client")
        results = session.execute(stmt).scalars().all()
        return {
            "clients": [
                {"id": str(c.user_id), "full_name": c.full_name, "email": c.email} 
                for c in results
            ]
        }

def add_permanent_location(client_id: str, data: dict) -> dict:
    engine = get_engine()
    try:
        with Session(engine) as session:
            new_loc = LocationModel(
                user_id=int(client_id),
                location_name=data.get("label"),
                address=data.get("address"),
                is_active=True
            )
            session.add(new_loc)
            session.commit()
            session.refresh(new_loc)
            
            return {
                "message": "Location saved to SQL Server",
                "location": {"id": str(new_loc.location_id), "address": new_loc.address}
            }
    except Exception as e:
        return {"error": str(e), "code": "db_failure"}

def list_permanent_locations(client_id: str) -> dict:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(LocationModel).where(LocationModel.user_id == int(client_id))
        results = session.execute(stmt).scalars().all()
        return {
            "locations": [
                {"id": str(l.location_id), "label": l.location_name, "address": l.address}
                for l in results
            ]
        }