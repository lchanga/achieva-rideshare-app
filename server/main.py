from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import List
import os
import time

# --- SHARED BASE & MODELS ---
from server.models.base import Base
from server.models.user import User
from server.models.location import Location
from server.models.client_location import ClientLocation
from server.models.ride_request import RideRequest
from server.models.optimized_route import OptimizedRoute

from server.optimizer.google import GoogleOptimizer
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import InterfaceError, OperationalError

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://sa:nxFpdQpyEEz33B@db:1433/master?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC SCHEMAS ---
class UserResponse(BaseModel):
    user_id: int
    email: str
    role: str
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str 

class ApprovedLocation(BaseModel):
    location_id: int
    name: str
    address: str
    city: str
    zip: str
    latitude: float
    longitude: float
    class Config:
        from_attributes = True

class RideCreate(BaseModel):
    passenger_id: int
    pickup_location_id: int 
    dropoff_location_id: int

# --- FASTAPI APP ---
app = FastAPI(title="Achieva Rideshare API", version="1.0.0")

# --- DATABASE INIT & SEEDING ---
def seed_data():
    db = SessionLocal()
    try:
        if db.query(Location).count() == 0:
            hq = Location(name="Achieva HQ", address="711 Bingham St", city="Pittsburgh", zip="15203", latitude=40.4297, longitude=-79.9926)
            ge = Location(name="Giant Eagle", address="4200 Fifth Ave", city="Pittsburgh", zip="15213", latitude=40.4433, longitude=-79.9558)
            db.add_all([hq, ge])
            db.commit()

        if db.query(User).count() == 0:
            db.add_all([
                User(first_name="Ryan", last_name="Jackson", email="rjackson@achieva.info", role="staff"),
                User(first_name="Kira", last_name="Gabridge", email="kgabridge@achieva.info", role="staff"),
                User(first_name="Lisa", last_name="Stroup", email="lstroup@achieva.info", role="staff"),
                User(first_name="Kayla", last_name="Edwards", email="kaylae@andrew.cmu.edu", role="staff"),
                User(first_name="Ashley", last_name="Liu", email="ashleyl4@andrew.cmu.edu", role="staff"),
                User(first_name="Victoria", last_name="Solsky", email="vsolsky@andrew.cmu.edu", role="staff"),
                User(first_name="Bob", last_name="Driver", email="bob@achieva.info", role="driver"),
                User(first_name="Alice", last_name="Client", email="alice06@gmail.com", role="client")
            ])
            db.commit()

            alice = db.query(User).filter(User.email == "alice06@gmail.com").first()
            loc = db.query(Location).first()
            if alice and loc and db.query(ClientLocation).count() == 0:
                db.add(ClientLocation(client_id=alice.user_id, location_id=loc.location_id, location_type="home"))
                db.commit()
            print("Database Seeded Successfully!")
    finally:
        db.close()

def init_db():
    retries = 10
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            seed_data()
            print("Application connected to DB and tables ensured.")
            break
        except (InterfaceError, OperationalError) as e:
            print(f"Waiting for SQL Server... {retries} retries left.")
            retries -= 1
            time.sleep(5)

init_db()

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "message": "Achieva Routing Engine Active"}

@app.get("/healthcheck", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}

@app.post("/login", response_model=UserResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = request.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email.")
    return user

@app.get("/locations/approved", response_model=List[ApprovedLocation])
async def get_approved_locations(db: Session = Depends(get_db)):
    return db.query(Location).all()

@app.post("/rides", tags=["Rides"])
def create_ride(ride_data: RideCreate, db: Session = Depends(get_db)):
    try:
        new_ride = RideRequest(
            passenger_id=ride_data.passenger_id,
            pickup_client_location_id=ride_data.pickup_location_id,
            dropoff_client_location_id=ride_data.dropoff_location_id,
            ride_date=date.today(),
            pickup_window_start=datetime.utcnow(),
            pickup_window_end=datetime.utcnow() + timedelta(hours=1),
            dropoff_window_start=datetime.utcnow() + timedelta(hours=1),
            dropoff_window_end=datetime.utcnow() + timedelta(hours=2),
            status="requested",
            api_shipment_label=f"PWA_{datetime.utcnow().strftime('%H%M%S')}"
        )
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)
        return {"status": "success", "ride_id": new_ride.request_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rides", tags=["Rides"])
def get_all_rides(db: Session = Depends(get_db)):
    return db.execute(select(RideRequest)).scalars().all()


@app.post("/optimize", tags=["Optimization"])
def run_optimization(db: Session = Depends(get_db)):
    """
    Trigger for Ashley's '8pm lock function'. 
    This should call the GoogleOptimizer and update Optimized_routes.
    """
    try:
        return {"status": "pending", "message": "Optimizer logic hook ready for Ashley."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))