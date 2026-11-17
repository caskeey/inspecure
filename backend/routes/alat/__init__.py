from flask import Blueprint

# Blueprint ini dipakai bersama oleh semua submodul di folder ini
# (crud.py, resertifikasi.py, import_export.py, detail.py).
# Nama endpoint berawalan 'alat.', contoh: url_for('alat.data_master').
alat_bp = Blueprint('alat', __name__)

# Import submodule di baris paling bawah (setelah alat_bp dibuat), supaya
# setiap @alat_bp.route(...) di dalamnya sempat terdaftar ke blueprint ini.
from . import data_master
from . import crud
from . import resertifikasi
from . import import_export
from . import detail