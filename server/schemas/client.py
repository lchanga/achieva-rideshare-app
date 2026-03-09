from marshmallow import Schema, fields


class RideRequestSchema(Schema):
    id = fields.Str(dump_only=True)
    pickup_location = fields.Str(required=True)
    dropoff_location = fields.Str(required=True)
    date = fields.Str(required=True)
    pickup_window_start = fields.Str(required=True)
    pickup_window_end = fields.Str(required=True)
    dropoff_window_start = fields.Str(required=True)
    dropoff_window_end = fields.Str(required=True)
    status = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)


class RideRequestCreateSchema(Schema):
    pickup_location = fields.Str(required=True)
    dropoff_location = fields.Str(required=True)
    pickup_window_start = fields.Str(required=True)
    pickup_window_end = fields.Str(required=True)
    dropoff_window_start = fields.Str(required=True)
    dropoff_window_end = fields.Str(required=True)
    timezone = fields.Str(required=False)
    date = fields.Str(required=False)


class RideRequestUpdateSchema(Schema):
    pickup_location = fields.Str(required=False)
    dropoff_location = fields.Str(required=False)
    pickup_window_start = fields.Str(required=False)
    pickup_window_end = fields.Str(required=False)
    dropoff_window_start = fields.Str(required=False)
    dropoff_window_end = fields.Str(required=False)
    timezone = fields.Str(required=False)
    date = fields.Str(required=False)


class RideRequestCreateResponseSchema(Schema):
    message = fields.Str(required=True)
    ride = fields.Nested(RideRequestSchema, required=True)


class RideRequestGetResponseSchema(Schema):
    ride = fields.Nested(RideRequestSchema, required=True)


class RideRequestListResponseSchema(Schema):
    rides = fields.List(fields.Nested(RideRequestSchema), required=True)


class RideRequestDeleteResponseSchema(Schema):
    message = fields.Str(required=True)
    ride_id = fields.Str(required=True)


class RideRequestUpdateResponseSchema(Schema):
    message = fields.Str(required=True)
    ride = fields.Nested(RideRequestSchema, required=True)

