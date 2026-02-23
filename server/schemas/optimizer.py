from marshmallow import INCLUDE, Schema


class OptimizeToursAnySchema(Schema):
    """
    Flexible schema that passes through arbitrary JSON objects.
    """

    class Meta:
        unknown = INCLUDE

