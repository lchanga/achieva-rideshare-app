from marshmallow import Schema, fields


class ErrorSchema(Schema):
    error = fields.Str(required=True)
    code = fields.Str(required=False)
    cutoff = fields.Str(required=False)


class MessageSchema(Schema):
    message = fields.Str(required=True)


class MessageIdSchema(Schema):
    message = fields.Str(required=True)
    driver_id = fields.Str(required=True)

