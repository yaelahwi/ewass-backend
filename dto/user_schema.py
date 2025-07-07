from marshmallow import Schema, fields, validate, ValidationError
import re

def validate_password(value):
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', value):
        raise ValidationError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', value):
        raise ValidationError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', value):
        raise ValidationError('Password must contain at least one number')

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    uid = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate_password, load_only=True)
    nama = fields.Str(required=True, validate=validate.Length(min=1))

    class Meta:
        ordered = True

class UserResponseSchema(Schema):
    id = fields.Int(required=True)
    uid = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    nama = fields.Str(required=True)

    class Meta:
        ordered = True
