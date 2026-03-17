from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.optimizer import get_optimizer
from server.schemas.common import ErrorSchema
from server.schemas.common import MessageSchema

optimizer_blp = Blueprint(
    "optimizer",
    __name__,
    url_prefix="/api/optimizer",
    description="Database-backed route optimization",
)


@optimizer_blp.route("/run")
class RunOptimizationResource(MethodView):
    @optimizer_blp.response(200, MessageSchema)
    @optimizer_blp.alt_response(500, schema=ErrorSchema)
    def post(self):
        try:
            return get_optimizer().run_optimization_sync()
        except Exception as e:
            abort(500, error=str(e))

