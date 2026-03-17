from marshmallow import Schema, fields, validate


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    role = fields.Str(required=False, validate=validate.OneOf(["client", "driver", "staff"]))


class AuthUserSchema(Schema):
    user_id = fields.Int(required=True)
    email = fields.Email(allow_none=True)
    role = fields.Str(required=True)

