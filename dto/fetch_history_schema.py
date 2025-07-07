from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class FetchHistorySchema(Schema):
    id = fields.Int(dump_only=True)
    start_time = fields.DateTime(required=False, load_default=datetime.now())
    end_time = fields.DateTime(required=False, allow_none=True)
    periode = fields.Str(required=True)
    status = fields.Str(required=True)
    user = fields.Str(required=True)

    class Meta:
        ordered = True
