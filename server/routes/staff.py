from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.common import ErrorSchema
from server.schemas.staff import (
    ClientCreateResponseSchema,
    ClientCreateSchema,
    ClientGetResponseSchema,
    ClientListResponseSchema,
    ClientUpdateSchema,
    LocationCreateResponseSchema,
    LocationCreateSchema,
    LocationDeleteResponseSchema,
    LocationsListResponseSchema,
    LocationUpdateResponseSchema,
    LocationUpdateSchema,
)
from server.services.staff_service import (
    add_permanent_location,
    create_client,
    delete_permanent_location,
    get_client,
    list_clients,
    list_permanent_locations,
    update_client,
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
    @staff_blp.alt_response(400, ErrorSchema)
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
    @staff_blp.alt_response(404, ErrorSchema)
    def get(self, client_id: str):
        result = get_client(client_id)
        if "error" in result:
            abort(404, **result)
        return result

    @staff_blp.arguments(ClientUpdateSchema(partial=True))
    @staff_blp.response(200, ClientCreateResponseSchema)
    @staff_blp.alt_response(400, ErrorSchema)
    @staff_blp.alt_response(404, ErrorSchema)
    def put(self, data: dict, client_id: str):
        result = update_client(client_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result


@staff_blp.route("/clients/<string:client_id>/permanent-locations")
class PermanentLocationsResource(MethodView):
    @staff_blp.arguments(LocationCreateSchema)
    @staff_blp.response(201, LocationCreateResponseSchema)
    @staff_blp.alt_response(400, ErrorSchema)
    @staff_blp.alt_response(404, ErrorSchema)
    def post(self, data: dict, client_id: str):
        result = add_permanent_location(client_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result

    @staff_blp.response(200, LocationsListResponseSchema)
    @staff_blp.alt_response(404, ErrorSchema)
    def get(self, client_id: str):
        result = list_permanent_locations(client_id)
        if "error" in result:
            abort(404, **result)
        return result


@staff_blp.route("/clients/<string:client_id>/permanent-locations/<string:location_id>")
class PermanentLocationResource(MethodView):
    @staff_blp.arguments(LocationUpdateSchema(partial=True))
    @staff_blp.response(200, LocationUpdateResponseSchema)
    @staff_blp.alt_response(404, ErrorSchema)
    def put(self, data: dict, client_id: str, location_id: str):
        result = update_permanent_location(client_id, location_id, data)
        if "error" in result:
            abort(404, **result)
        return result

    @staff_blp.response(200, LocationDeleteResponseSchema)
    @staff_blp.alt_response(404, ErrorSchema)
    def delete(self, client_id: str, location_id: str):
        result = delete_permanent_location(client_id, location_id)
        if "error" in result:
            abort(404, **result)
        return result

