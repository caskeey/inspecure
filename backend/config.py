import os

# =========================================================
# KONFIGURASI EMAIL (SMTP)
# =========================================================
# Isi lewat environment variable supaya kredensial tidak ke-commit ke git.
# Kalau pakai Gmail: aktifkan "App Password" (bukan password akun biasa),
# lalu isi SMTP_USER = alamat gmail, SMTP_PASS = app password 16 digit itu.
#
# Cara set di Windows (PowerShell), sebelum jalanin app.py:
#   $env:SMTP_USER="rekap.sucofindo@gmail.com"
#   $env:SMTP_PASS="xxxxxxxxxxxxxxxx"
#
# Atau bikin file .env di folder utama project (salin dari .env.example). File itu otomatis
# dibaca lewat python-dotenv saat app dijalankan.

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'

EMAIL_SENDER_NAME = os.environ.get('EMAIL_SENDER_NAME', 'PT SUCOFINDO (Persero)')
EMAIL_FROM = os.environ.get('EMAIL_FROM', SMTP_USER)
APP_PUBLIC_URL = os.environ.get('APP_PUBLIC_URL', '').strip().rstrip('/')
# Alamat dasar publik untuk tautan reset (mis. https://inspecure.example.com).
# Kosong berarti memakai host yang sedang membuka halaman permintaan reset.
PASSWORD_RESET_URL_BASE = os.environ.get('PASSWORD_RESET_URL_BASE', '').strip().rstrip('/')

# Alamat cadangan yang selalu di-BCC setiap pengiriman rekap (opsional, boleh dikosongkan)
EMAIL_BCC_DEFAULT = [e.strip() for e in os.environ.get('EMAIL_BCC_DEFAULT', '').split(',') if e.strip()]

# =========================================================
# KONFIGURASI JADWAL REKAP RESERTIFIKASI
# =========================================================
REKAP_HARI = int(os.environ.get('REKAP_HARI', 28))     # tanggal berapa job jalan tiap bulan
REKAP_JAM = int(os.environ.get('REKAP_JAM', 10))        # jam (24h) job jalan
REKAP_MENIT = int(os.environ.get('REKAP_MENIT', 0))
REKAP_BULAN_KEDEPAN = int(os.environ.get('REKAP_BULAN_KEDEPAN', 3))  # H-3 bulan sebelum resertifikasi

# Aktif/nonaktifkan scheduler otomatis (misal dimatikan saat development)
SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'

# =========================================================
# KONFIGURASI OBJECT STORAGE (Cloudflare R2)
# =========================================================
# R2 itu S3-compatible, jadi dipakai lewat boto3 biasa, cuma endpoint-nya beda.
# Isi 4 variabel ini di .env:
#   R2_ACCOUNT_ID          -> dari dashboard Cloudflare > R2
#   R2_ACCESS_KEY_ID       -> dari API Token yang dibuat khusus utk R2
#   R2_SECRET_ACCESS_KEY   -> pasangan dari Access Key ID (cuma muncul sekali pas dibuat)
#   R2_BUCKET_NAME         -> nama bucket, misal "inssp-documents"
#
# Kalau R2_ACCOUNT_ID kosong, semua fungsi storage_r2.py otomatis fallback
# ke penyimpanan lokal (static/uploads) supaya app tetap jalan normal di
# development / sebelum kredensial R2 disiapkan.
R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID', '')
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', '')
R2_ENDPOINT_URL = (
    f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ''
)
# Presigned URL (link sementara buat lihat/download dokumen) berlaku berapa lama
R2_PRESIGNED_EXPIRY_SECONDS = int(os.environ.get('R2_PRESIGNED_EXPIRY_SECONDS', 3600))  # 1 jam

R2_ENABLED = bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME)

# =========================================================
# KONFIGURASI BACKUP DATABASE OTOMATIS
# =========================================================
# Backup dijalankan tiap hari pada jam yang ditentukan (WIB).
# File .sql.gz hasil mysqldump diupload ke R2 (kalau aktif).
# Backup fallback lokal dihapus otomatis setelah BACKUP_RETENTION_DAYS hari.
# Backup di R2 mengikuti lifecycle policy bucket (bila diaktifkan).
BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
BACKUP_JAM = int(os.environ.get('BACKUP_JAM', 3))       # jam (24h) backup jalan (default: 03:00 WIB)
BACKUP_MENIT = int(os.environ.get('BACKUP_MENIT', 0))
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))  # simpan backup selama 30 hari