from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.common import ErrorSchema
from server.schemas.driver import (
    MessageRouteResponseSchema,
    RouteResponseSchema,
    RoutesListResponseSchema,
    TodayRouteResponseSchema,
)
from server.services.driver_service import (
    complete_route,
    get_driver_today_route,
    get_route,
    start_route,
)

driver_blp = Blueprint(
    "driver",
    __name__,
    url_prefix="/api/driver",
    description="Driver-facing operations",
)


@driver_blp.route("/<string:driver_id>/today-route")
class DriverTodayRouteResource(MethodView):
    @driver_blp.response(200, TodayRouteResponseSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def get(self, driver_id: str):
        result = get_driver_today_route(driver_id)
        if "error" in result:
            abort(404, **result)
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


@driver_blp.route("/routes/<string:route_id>/start")
class StartRouteResource(MethodView):
    @driver_blp.response(200, MessageRouteResponseSchema)
    @driver_blp.alt_response(404, schema=ErrorSchema)
    def post(self, route_id: str):
        result = start_route(route_id)
        if "error" in result:
            abort(404, **result)
        return result

