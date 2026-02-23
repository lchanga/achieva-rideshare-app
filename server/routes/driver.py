from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.common import ErrorSchema
from server.schemas.driver import (
    AcceptRouteRequestSchema,
    MessageRouteResponseSchema,
    RemoveStopRequestSchema,
    RouteResponseSchema,
    RoutesListResponseSchema,
)
from server.services.driver_service import (
    accept_route,
    complete_route,
    get_route,
    list_available_routes,
    remove_stop,
)

driver_blp = Blueprint(
    "driver",
    __name__,
    url_prefix="/api/driver",
    description="Driver-facing operations",
)


@driver_blp.route("/routes/available")
class AvailableRoutesResource(MethodView):
    @driver_blp.response(200, RoutesListResponseSchema)
    def get(self):
        return list_available_routes()


@driver_blp.route("/routes/<string:route_id>/accept")
class AcceptRouteResource(MethodView):
    @driver_blp.arguments(AcceptRouteRequestSchema, required=False)
    @driver_blp.response(200, MessageRouteResponseSchema)
    @driver_blp.alt_response(400, schema=ErrorSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def post(self, data: dict, route_id: str):
        result = accept_route(route_id, data or {})
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result


@driver_blp.route("/routes/<string:route_id>")
class RouteDetailsResource(MethodView):
    @driver_blp.response(200, RouteResponseSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def get(self, route_id: str):
        result = get_route(route_id)
        if "error" in result:
            abort(404, **result)
        return result


@driver_blp.route("/routes/<string:route_id>/complete")
class CompleteRouteResource(MethodView):
    @driver_blp.response(200, MessageRouteResponseSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def post(self, route_id: str):
        result = complete_route(route_id)
        if "error" in result:
            abort(404, **result)
        return result


@driver_blp.route("/routes/<string:route_id>/remove-stop")
class RemoveStopResource(MethodView):
    @driver_blp.arguments(RemoveStopRequestSchema)
    @driver_blp.response(200, MessageRouteResponseSchema)
    @driver_blp.alt_response(400, schema=ErrorSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def post(self, data: dict, route_id: str):
        result = remove_stop(route_id, data)
        if "error" in result:
            abort(404 if result.get("code") == "not_found" else 400, **result)
        return result

