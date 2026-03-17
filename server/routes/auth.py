from flask.views import MethodView
from flask_smorest import Blueprint, abort

from server.schemas.auth import AuthUserSchema, LoginRequestSchema
from server.schemas.common import ErrorSchema
from server.services.auth_service import login_user

auth_blp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
    description="Authentication operations",
)


@auth_blp.route("/login")
class LoginResource(MethodView):
    @auth_blp.arguments(LoginRequestSchema)
    @auth_blp.response(200, AuthUserSchema)
    @auth_blp.alt_response(400, schema=ErrorSchema)
    @auth_blp.alt_response(401, schema=ErrorSchema)
    def post(self, data: dict):
        result = login_user(data)
        if "error" in result:
            abort(401 if result.get("code") == "invalid_credentials" else 400, **result)
        return result
