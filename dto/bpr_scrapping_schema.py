from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class BprScrappingSchema(Schema):
    id = fields.Int(dump_only=True)
    waktu_diambil = fields.DateTime(required=False, load_default=datetime.now)
    tahun = fields.Int(required=True, validate=validate.Range(min=2000, max=9999))
    bulan = fields.Str(required=True, validate=validate.OneOf(
        ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    ))
    nama_provinsi = fields.Str(required=True)
    nama_kota = fields.Str(required=True)
    sandi = fields.Str(required=True)
    nama = fields.Str(required=True) 
    asset_saat_ini = fields.Float(required=True)
    asset_tahun_lalu = fields.Float(required=True)
    kyd_saat_ini = fields.Float(required=True)
    kyd_tahun_lalu = fields.Float(required=True)
    hutang_saat_ini = fields.Float(required=True)
    hutang_tahun_lalu = fields.Float(required=True)
    laba_tahun_tahun_lalu_saat_ini = fields.Float(required=True)
    laba_tahun_tahun_lalu_sebelumnya = fields.Float(required=True)
    laba_saat_ini = fields.Float(required=True) # Dari 'Laba (Rugi) Tahun Berjalan Saat Ini'
    laba_tahun_lalu = fields.Float(required=True) # Dari 'Laba (Rugi) Tahun Berjalan Tahun Sebelumnya'
    tabungan_saat_ini = fields.Float(required=True)
    tabungan_tahun_lalu = fields.Float(required=True)
    deposito_saat_ini = fields.Float(required=True)
    deposito_tahun_lalu = fields.Float(required=True)
    penempatan_pada_bank_lain_saat_ini = fields.Float(required=True) # Ini harusnya 'penempatan_pada_bank_lain_saat_ini' jika ada yang lama
    penempatan_pada_bank_lain_tahun_lalu = fields.Float(required=False, allow_none=True) # TAMBAHAN
    total_ekuitas = fields.Float(required=True) # Ini harusnya 'total_ekuitas_saat_ini' jika ada yang lama
    total_ekuitas_tahun_lalu = fields.Float(required=False, allow_none=True) # TAMBAHAN
    simpanan_dari_bank_lain_saat_ini = fields.Float(required=True)
    simpanan_dari_bank_lain_tahun_lalu = fields.Float(required=False)
    laba_desember_tahun_sebelum = fields.Float(required=True)
    npl_net = fields.Float(required=True, places=2)
    kpmm = fields.Float(required=True, places=2)
    ldr = fields.Float(required=True, places=2)
    roa = fields.Float(required=True, places=2)
    kap = fields.Float(required=True, places=2)
    ppap = fields.Float(required=True, places=2)
    bopo = fields.Float(required=True, places=2)
    nim = fields.Float(required=True, places=2)
    cr = fields.Float(required=True, places=2)
    direksi = fields.Str(required=False, allow_none=True)
    dewan_komisaris = fields.Str(required=False,allow_none=True)

    class Meta:
        ordered = True
