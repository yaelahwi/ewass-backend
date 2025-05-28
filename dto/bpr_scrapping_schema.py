from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class BprScrappingSchema(Schema):
    id = fields.Int(dump_only=True)
    waktu_diambil = fields.DateTime(required=False, load_default=datetime.utcnow)
    tahun = fields.Int(required=True, validate=validate.Range(min=2000, max=9999))
    bulan = fields.Str(required=True, validate=validate.OneOf(
        ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    ))
    nama_provinsi = fields.Str(required=True)
    nama_kota = fields.Str(required=True)
    sandi = fields.Str(required=True)
    nama = fields.Str(required=True)
    asset = fields.Float(required=True, validate=validate.Range(min=0))
    kyd = fields.Float(required=True, validate=validate.Range(min=0))
    total_hutang = fields.Float(required=True, validate=validate.Range(min=0))
    laba_tahun_lalu = fields.Float(required=True)
    laba_saat_ini = fields.Float(required=True)
    npl_net = fields.Float(required=True, validate=validate.Range(min=0))
    kpmm = fields.Float(required=True, validate=validate.Range(min=0))
    ldr = fields.Float(required=True, validate=validate.Range(min=0))
    roa = fields.Float(required=True)
    kap = fields.Float(required=True, validate=validate.Range(min=0))
    ppap = fields.Float(required=True, validate=validate.Range(min=0))
    bopo = fields.Float(required=True, validate=validate.Range(min=0))
    cr = fields.Float(required=True, validate=validate.Range(min=0))
    direksi = fields.Str(required=True)
    dewan_komisaris = fields.Str(required=True)

    class Meta:
        ordered = True
