from marshmallow import Schema, fields


class AcceptRouteRequestSchema(Schema):
    driver_id = fields.Str(required=False)


class RemoveStopRequestSchema(Schema):
    stop_id = fields.Str(required=False)
    stop_index = fields.Int(required=False)


class RoutesListResponseSchema(Schema):
    routes = fields.List(fields.Dict(), required=True)


class RouteResponseSchema(Schema):
    route = fields.Dict(required=True)


class MessageRouteResponseSchema(Schema):
    message = fields.Str(required=True)
    route = fields.Dict(required=True)

