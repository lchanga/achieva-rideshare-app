import sys
import os

# PATHING INSURANCE: This ensures Docker finds the 'server' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from server.db import get_engine

# IMPORT ALL MODELS HERE
from server.models.base import Base
from server.models.user import User
from server.models.ride_request import RideRequest
from server.models.client_location import ClientLocation
# Updated to match your actual filenames and class names
from server.models.optimized_route import OptimizedRoute
from server.models.route_stop import RouteStop

def initialize_database():
    load_dotenv()
    
    print("--- AchievaPath Database Initializer ---")
    try:
        engine = get_engine()
        db_server = os.getenv('DB_SERVER')
        print(f"Connecting to: {db_server}...")
        
        # This command creates all tables defined in your models
        print("Creating tables in SQL Server...")
        Base.metadata.create_all(bind=engine)
        
        print("\nSUCCESS: Database schema is synchronized!")
        print("Tables created/verified: Users, RideRequests, ClientLocations, OptimizedRoutes, RouteStops")
        
    except Exception as e:
        print(f"\nERROR: Could not initialize database.")
        print(f"Details: {e}")

if __name__ == "__main__":
    initialize_database()