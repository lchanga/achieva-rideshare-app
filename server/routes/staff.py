from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.common import ErrorSchema
from server.schemas.common import MessageIdSchema
from server.schemas.driver import RoutesListResponseSchema, RouteResponseSchema
from server.schemas.client import RideRequestListResponseSchema, RideRequestGetResponseSchema
from server.schemas.staff import (
    ClientCreateResponseSchema,
    ClientCreateSchema,
    ClientGetResponseSchema,
    ClientListResponseSchema,
    ClientUpdateSchema,
    DriverAvailabilityCreateSchema,
    DriverAvailabilityListResponseSchema,
    DriverAvailabilityResponseSchema,
    DriverAvailabilityUpdateSchema,
    LocationCreateResponseSchema,
    LocationCreateSchema,
    LocationDeleteResponseSchema,
    LocationsListResponseSchema,
    LocationUpdateResponseSchema,
    LocationUpdateSchema,
)
from server.services.driver_service import get_route
from server.services.staff_service import (
    add_permanent_location,
    create_driver_availability,
    create_client,
    delete_client,
    delete_permanent_location,
    get_client,
    list_driver_availability,
    list_clients,
    list_permanent_locations,
    update_driver_availability,
    update_client,
    list_routes,
    list_ride_requests_admin,
    get_ride_request_admin,
    update_permanent_location,
)

staff_blp = Blueprint(
    "staff",
    __name__,
    url_prefix="/api/staff",
    description="Staff-facing operations",
)


@staff_blp.route("/clients")
class ClientsResource(MethodView):
    @staff_blp.arguments(ClientCreateSchema)
    @staff_blp.response(201, ClientCreateResponseSchema)
    @staff_blp.alt_response(400, schema=ErrorSchema)
    def post(self, data: dict):
        result = create_client(data)
        if "error" in result:
            abort(400, **result)
        return result

    @staff_blp.response(200, ClientListResponseSchema)
    def get(self):
        return list_clients()


@staff_blp.route("/clients/<string:client_id>")
class ClientResource(MethodView):
    @staff_blp.response(200, ClientGetResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def get(self, client_id: str):
        result = get_client(client_id)
        if "error" in result:
            abort(404, **result)
        return result

    @staff_blp.arguments(ClientUpdateSchema(partial=True))
    @staff_blp.response(200, ClientCreateResponseSchema)
    @staff_blp.alt_response(400, schema=ErrorSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def put(self, data: dict, client_id: str):
        result = update_client(client_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result

    @staff_blp.response(200, ClientCreateResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def delete(self, client_id: str):
        result = delete_client(client_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/clients/<string:client_id>/permanent-locations")
class PermanentLocationsResource(MethodView):
    @staff_blp.arguments(LocationCreateSchema)
    @staff_blp.response(201, LocationCreateResponseSchema)
    @staff_blp.alt_response(400, schema=ErrorSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def post(self, data: dict, client_id: str):
        result = add_permanent_location(client_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result

    @staff_blp.response(200, LocationsListResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def get(self, client_id: str):
        result = list_permanent_locations(client_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/clients/<string:client_id>/permanent-locations/<string:location_id>")
class PermanentLocationResource(MethodView):
    @staff_blp.arguments(LocationUpdateSchema(partial=True))
    @staff_blp.response(200, LocationUpdateResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def put(self, data: dict, client_id: str, location_id: str):
        result = update_permanent_location(client_id, location_id, data)
        if "error" in result:
            abort(404, **result)
        return result

    @staff_blp.response(200, LocationDeleteResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def delete(self, client_id: str, location_id: str):
        result = delete_permanent_location(client_id, location_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/driver-availability")
class DriverAvailabilityCollectionResource(MethodView):
    @staff_blp.response(200, DriverAvailabilityListResponseSchema)
    def get(self):
        return list_driver_availability()

    @staff_blp.arguments(DriverAvailabilityCreateSchema)
    @staff_blp.response(201, DriverAvailabilityResponseSchema)
    @staff_blp.alt_response(400, schema=ErrorSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def post(self, data: dict):
        result = create_driver_availability(data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result


@staff_blp.route("/driver-availability/<string:driver_id>")
class DriverAvailabilityResource(MethodView):
    @staff_blp.arguments(DriverAvailabilityUpdateSchema)
    @staff_blp.response(200, DriverAvailabilityResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def put(self, data: dict, driver_id: str):
        result = update_driver_availability(driver_id, data)
        if "error" in result:
            abort(404, **result)
        return result

    @staff_blp.response(200, MessageIdSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def delete(self, driver_id: str):
        from server.services.staff_service import delete_driver_availability

        result = delete_driver_availability(driver_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/routes")
class RoutesCollectionResource(MethodView):
    @staff_blp.response(200, RoutesListResponseSchema)
    def get(self):
        return list_routes()


@staff_blp.route("/routes/<string:route_id>")
class RouteResource(MethodView):
    @staff_blp.response(200, RouteResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def get(self, route_id: str):
        result = get_route(route_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/ride-requests")
class StaffRideRequestsResource(MethodView):
    @staff_blp.response(200, RideRequestListResponseSchema)
    def get(self):
        return list_ride_requests_admin()


@staff_blp.route("/ride-requests/<string:ride_id>")
class StaffRideRequestResource(MethodView):
    @staff_blp.response(200, RideRequestGetResponseSchema)
    @staff_blp.alt_response(404, schema=ErrorSchema)
    def get(self, ride_id: str):
        result = get_ride_request_admin(ride_id)
        if "error" in result:
            abort(404, **result)
        return result
