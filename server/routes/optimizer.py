from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.optimizer import optimize_tours
from server.schemas.common import ErrorSchema
from server.schemas.optimizer import OptimizeToursAnySchema

optimizer_blp = Blueprint(
    "optimizer",
    __name__,
    url_prefix="/api/optimizer",
    description="Route optimization entrypoint (fake now, Google later)",
)


@optimizer_blp.route("/optimize-tours")
class OptimizeToursResource(MethodView):
    @optimizer_blp.arguments(OptimizeToursAnySchema)
    @optimizer_blp.response(200, None)
    @optimizer_blp.alt_response(400, ErrorSchema)
    def post(self, req_json: dict):
        if not isinstance(req_json, dict):
            abort(400, error="Request body must be a JSON object")

        try:
            return optimize_tours(req_json)
        except Exception as e:
            abort(400, error=str(e))

