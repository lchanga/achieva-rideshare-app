-- 1. Locations
CREATE TABLE Locations (
    location_id int IDENTITY(1,1) NOT NULL,
    name nvarchar(max) NOT NULL,
    address nvarchar(max) NOT NULL,
    city nvarchar(255) NOT NULL,
    zip nvarchar(20) NOT NULL,
    latitude decimal(9,6) NOT NULL,
    longitude decimal(9,6) NOT NULL,
    CONSTRAINT Locations_pk PRIMARY KEY (location_id)
);

-- 2. Users (Role_type Enum)
CREATE TABLE Users (
    user_id int IDENTITY(1,1) NOT NULL,
    role nvarchar(20) NOT NULL, 
    first_name nvarchar(255) NOT NULL,
    last_name nvarchar(255) NOT NULL,
    email nvarchar(255) NULL,
    phone nvarchar(50) NULL,
    sso_id nvarchar(255) NULL,
    username nvarchar(255) NULL,
    password_hash nvarchar(max) NULL,
    needs_ramp bit NOT NULL DEFAULT 0,
    is_active bit NOT NULL DEFAULT 1,
    CONSTRAINT Users_pk PRIMARY KEY (user_id),
    CONSTRAINT CHK_UserRole CHECK (role IN ('client', 'driver', 'staff'))
);

-- 3. Client_locations (Location_type Enum)
CREATE TABLE Client_locations (
    client_location_id int IDENTITY(1,1) NOT NULL,
    client_id int NOT NULL,
    location_id int NOT NULL,
    location_type nvarchar(20) NOT NULL, 
    is_verified bit NOT NULL DEFAULT 0,
    CONSTRAINT Client_locations_pk PRIMARY KEY (client_location_id),
    CONSTRAINT FK_ClientLoc_User FOREIGN KEY (client_id) REFERENCES Users(user_id),
    CONSTRAINT FK_ClientLoc_Loc FOREIGN KEY (location_id) REFERENCES Locations(location_id),
    CONSTRAINT CHK_LocationType CHECK (location_type IN ('home', 'work', 'volunteer'))
);

-- 4. Optimization_runs
CREATE TABLE Optimization_runs (
    run_id int IDENTITY(1,1) NOT NULL,
    started_at datetime NOT NULL DEFAULT GETDATE(),
    ended_at datetime NULL,
    success bit NOT NULL DEFAULT 0,
    error_message nvarchar(max) NULL,
    ride_date date NOT NULL,
    CONSTRAINT Optimization_runs_pk PRIMARY KEY (run_id)
);

-- 5. Driver_availability
CREATE TABLE Driver_availability (
    availability_id int IDENTITY(1,1) NOT NULL,
    driver_id int NOT NULL,
    is_available bit NOT NULL DEFAULT 1,
    CONSTRAINT Driver_availability_pk PRIMARY KEY (availability_id),
    CONSTRAINT UQ_DriverAvailability_driver_id UNIQUE (driver_id),
    CONSTRAINT FK_DriverAvailability_User FOREIGN KEY (driver_id) REFERENCES Users(user_id)
);

-- 6. Ride_requests (Request_status Enum)
CREATE TABLE Ride_requests (
    request_id int IDENTITY(1,1) NOT NULL,
    passenger_id int NOT NULL,
    pickup_client_location_id int NOT NULL,
    dropoff_client_location_id int NOT NULL,
    ride_date date NOT NULL,
    pickup_window_start datetime NOT NULL,
    pickup_window_end datetime NOT NULL,
    dropoff_window_start datetime NOT NULL,
    dropoff_window_end datetime NOT NULL,
    created_at datetime NOT NULL DEFAULT GETDATE(),
    status nvarchar(30) NOT NULL DEFAULT 'requested',
    api_shipment_label nvarchar(255) NOT NULL,
    CONSTRAINT Ride_requests_pk PRIMARY KEY (request_id),
    CONSTRAINT FK_Ride_User FOREIGN KEY (passenger_id) REFERENCES Users(user_id),
    CONSTRAINT FK_Ride_Pickup FOREIGN KEY (pickup_client_location_id) REFERENCES Client_locations(client_location_id),
    CONSTRAINT FK_Ride_Dropoff FOREIGN KEY (dropoff_client_location_id) REFERENCES Client_locations(client_location_id),
    CONSTRAINT CHK_RequestStatus CHECK (status IN ('requested', 'scheduled', 'cancelled_by_passenger', 'cancelled_by_driver', 'completed'))
);

-- 7. Optimized_routes (Route_status Enum)
CREATE TABLE Optimized_routes (
    route_id int IDENTITY(1,1) NOT NULL,
    driver_id int NULL,
    route_date date NOT NULL,
    status nvarchar(20) NOT NULL DEFAULT 'available',
    polyline nvarchar(max) NULL,
    accepted_at datetime NULL,
    run_id int NOT NULL, 
    CONSTRAINT Optimized_routes_pk PRIMARY KEY (route_id),
    CONSTRAINT FK_Route_Driver FOREIGN KEY (driver_id) REFERENCES Users(user_id),
    CONSTRAINT FK_Route_Run FOREIGN KEY (run_id) REFERENCES Optimization_runs(run_id),
    CONSTRAINT CHK_RouteStatus CHECK (status IN ('available', 'assigned', 'in_progress', 'completed'))
);

-- 8. Route_stops (Stop_type & Stop_status Enums)
CREATE TABLE Route_stops (
    stop_id int IDENTITY(1,1) NOT NULL,
    route_id int NOT NULL,
    request_id int NOT NULL,
    location_id int NOT NULL,
    stop_sequence int NOT NULL,
    stop_type nvarchar(20) NOT NULL, 
    actual_arrival datetime NULL,
    planned_arrival datetime NOT NULL,
    status nvarchar(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT Route_stops_pk PRIMARY KEY (stop_id),
    CONSTRAINT FK_Stop_Route FOREIGN KEY (route_id) REFERENCES Optimized_routes(route_id),
    CONSTRAINT FK_Stop_Request FOREIGN KEY (request_id) REFERENCES Ride_requests(request_id),
    CONSTRAINT FK_Stop_Loc FOREIGN KEY (location_id) REFERENCES Locations(location_id),
    CONSTRAINT CHK_StopType CHECK (stop_type IN ('pickup', 'dropoff')),
    CONSTRAINT CHK_StopStatus CHECK (status IN ('pending', 'completed', 'skipped')),
    CONSTRAINT UQ_RouteSequence UNIQUE (route_id, stop_sequence)
);