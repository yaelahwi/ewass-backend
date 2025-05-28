from marshmallow import Schema, fields, validate, ValidationError
import re

def validate_phone(value):
    if not re.match(r'^\d{8,15}$', str(value)):
        raise ValidationError('Invalid phone number format. Must be between 8-15 digits.')

def validate_email(value):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
        raise ValidationError('Invalid email format.')

class BprLainnyaSchema(Schema):
    id = fields.Int(dump_only=True)
    sandi = fields.Str(required=True)
    nama_bpr = fields.Str(required=True)
    alamat_bpr = fields.Str(required=True)
    kota_kabupaten = fields.Str(required=True)
    provinsi = fields.Str(required=True)
    no_telepon = fields.Str(required=True, validate=validate_phone)
    email = fields.Email(required=True, validate=validate_email)
    wilayah_kerja_ojk = fields.Str(required=True)

    class Meta:
        ordered = True
