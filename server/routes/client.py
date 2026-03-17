from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.client import (
    ClientLocationsListResponseSchema,
    RideRequestCreateResponseSchema,
    RideRequestCreateSchema,
    RideRequestDeleteResponseSchema,
    RideRequestGetResponseSchema,
    RideRequestListResponseSchema,
    RideRequestUpdateResponseSchema,
    RideRequestUpdateSchema,
)
from server.schemas.common import ErrorSchema
from server.services.client_service import (
    create_ride_request,
    delete_ride_request,
    get_ride_request,
    list_client_permanent_locations,
    list_ride_requests_for_client,
    update_ride_request,
)

client_blp = Blueprint(
    "client",
    __name__,
    url_prefix="/api/client",
    description="Client-facing operations",
)


@client_blp.route("/ride-requests")
class RideRequestsResource(MethodView):
    @client_blp.arguments(RideRequestCreateSchema)
    @client_blp.response(201, RideRequestCreateResponseSchema)
    @client_blp.alt_response(400, schema=ErrorSchema)
    def post(self, data: dict):
        result = create_ride_request(data)
        if "error" in result:
            abort(400, **result)
        return result


@client_blp.route("/ride-requests/<string:ride_id>")
class RideRequestResource(MethodView):
    @client_blp.response(200, RideRequestGetResponseSchema)
    @client_blp.alt_response(404, schema=ErrorSchema)
    def get(self, ride_id: str):
        result = get_ride_request(ride_id)
        if "error" in result:
            abort(404, **result)
        return result

    @client_blp.response(200, RideRequestDeleteResponseSchema)
    @client_blp.alt_response(400, schema=ErrorSchema)
    @client_blp.alt_response(404, schema=ErrorSchema)
    def delete(self, ride_id: str):
        result = delete_ride_request(ride_id)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result


    @client_blp.arguments(RideRequestUpdateSchema(partial=True))
    @client_blp.response(200, RideRequestUpdateResponseSchema)
    @client_blp.alt_response(400, schema=ErrorSchema)
    @client_blp.alt_response(404, schema=ErrorSchema)
    def put(self, data: dict, ride_id: str):
        result = update_ride_request(ride_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result


@client_blp.route("/<string:client_id>/ride-requests")
class ClientRideRequestsResource(MethodView):
    @client_blp.response(200, RideRequestListResponseSchema)
    @client_blp.alt_response(404, schema=ErrorSchema)
    def get(self, client_id: str):
        result = list_ride_requests_for_client(client_id)
        if "error" in result:
            abort(404, **result)
        return result


@client_blp.route("/<string:client_id>/permanent-locations")
class ClientPermanentLocationsResource(MethodView):
    @client_blp.response(200, ClientLocationsListResponseSchema)
    @client_blp.alt_response(404, schema=ErrorSchema)
    def get(self, client_id: str):
        result = list_client_permanent_locations(client_id)
        if "error" in result:
            abort(404, **result)
        return result


