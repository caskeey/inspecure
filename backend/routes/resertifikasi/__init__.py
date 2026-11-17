from flask import Blueprint

resertifikasi_bp = Blueprint('resertifikasi', __name__)

# Import routes di baris paling bawah (setelah resertifikasi_bp dibuat),
# supaya setiap @resertifikasi_bp.route(...) di dalamnya sempat terdaftar.
from . import routes  # noqa: E402

# Re-export jalankan_rekap_resertifikasi supaya
#   from routes.resertifikasi import jalankan_rekap_resertifikasi
# di scheduler.py TETAP JALAN tanpa perlu diubah.
from .jobs import jalankan_rekap_resertifikasi  # noqa: E402,F401