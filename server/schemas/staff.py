from marshmallow import Schema, fields


class PermanentLocationSchema(Schema):
    id = fields.Str(dump_only=True)
    label = fields.Str(required=True)
    address = fields.Str(required=True)


class ClientSchema(Schema):
    id = fields.Str(dump_only=True)
    full_name = fields.Str(required=True)
    phone = fields.Str(required=False, allow_none=True)
    email = fields.Str(required=False, allow_none=True)
    created_at = fields.Str(dump_only=True)
    permanent_locations = fields.List(fields.Nested(PermanentLocationSchema), required=True)


class ClientCreateSchema(Schema):
    full_name = fields.Str(required=True)
    phone = fields.Str(required=False)
    email = fields.Str(required=False)


class ClientUpdateSchema(Schema):
    full_name = fields.Str(required=False)
    phone = fields.Str(required=False, allow_none=True)
    email = fields.Str(required=False, allow_none=True)


class LocationCreateSchema(Schema):
    label = fields.Str(required=True)
    address = fields.Str(required=True)


class LocationUpdateSchema(Schema):
    label = fields.Str(required=False)
    address = fields.Str(required=False)


class ClientCreateResponseSchema(Schema):
    message = fields.Str(required=True)
    client = fields.Nested(ClientSchema, required=True)


class ClientGetResponseSchema(Schema):
    client = fields.Nested(ClientSchema, required=True)


class ClientListResponseSchema(Schema):
    clients = fields.List(fields.Nested(ClientSchema), required=True)


class LocationCreateResponseSchema(Schema):
    message = fields.Str(required=True)
    location = fields.Nested(PermanentLocationSchema, required=True)


class LocationsListResponseSchema(Schema):
    locations = fields.List(fields.Nested(PermanentLocationSchema), required=True)


class LocationUpdateResponseSchema(Schema):
    message = fields.Str(required=True)
    location = fields.Nested(PermanentLocationSchema, required=True)


class LocationDeleteResponseSchema(Schema):
    message = fields.Str(required=True)
    location_id = fields.Str(required=True)

