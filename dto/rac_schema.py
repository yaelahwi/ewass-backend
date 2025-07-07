from marshmallow import Schema, fields, validate, ValidationError

class RACSchema(Schema):
    id = fields.Int(dump_only=True)
    npl_net = fields.Float(required=True, validate=validate.Range(min=0))
    laba_sebelum = fields.Float(required=True)
    laba_sekarang = fields.Float(required=True)
    kap = fields.Float(required=True, validate=validate.Range(min=0), places=2)
    kpmm = fields.Float(required=True, validate=validate.Range(min=0), places=2)
    asset = fields.Float(required=True, validate=validate.Range(min=0), places=2)
    roa = fields.Float(required=True, places=2)
    bopo = fields.Float(required=True, validate=validate.Range(min=0), places=2)

    class Meta:
        ordered = True
