"""Backup database otomatis: mysqldump → gzip → upload ke R2.

Dipanggil oleh scheduler.py setiap hari. Kalau R2 belum dikonfigurasi,
backup disimpan ke folder lokal (static/backups/) sebagai fallback.

Prerequisites:
  - mysqldump harus tersedia di PATH (sudah terinstal di image Docker mysql:8.4).
  - Untuk Docker: backup dijalankan dari container `app`, tapi mengakses DB di container `db`
    lewat hostname `db` (sesuai docker-compose.yml). mysqldump diinstal di Dockerfile.
"""
import gzip
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timedelta

import config

logger = logging.getLogger(__name__)

# Folder fallback lokal kalau R2 belum aktif
_BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'backups'
)


def _run_mysqldump():
    """Jalankan mysqldump dan kembalikan path file .sql.gz sementara."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = os.environ.get('MYSQLDATABASE', 'db_inspecure')
    host = os.environ.get('MYSQLHOST', 'localhost')
    port = os.environ.get('MYSQLPORT', '3306')
    user = os.environ.get('MYSQLUSER', 'root')
    password = os.environ.get('MYSQLPASSWORD', '')

    def option_value(value):
        # Escape nilai option-file MySQL/MariaDB, supaya password khusus tidak
        # merusak sintaks dan tidak tampil di daftar argumen proses.
        value = str(value).replace('\\', '\\\\').replace('"', '\\"')
        value = value.replace('\n', '\\n').replace('\r', '\\r')
        return f'"{value}"'
    
    # File sementara untuk hasil dump
    fd, tmp_sql = tempfile.mkstemp(suffix='.sql')
    os.close(fd)
    fd, tmp_defaults = tempfile.mkstemp(prefix='mysqldump-', suffix='.cnf')
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as defaults_file:
            defaults_file.write(
                '[client]\n'
                f'host={option_value(host)}\n'
                f'port={option_value(port)}\n'
                f'user={option_value(user)}\n'
                f'password={option_value(password)}\n'
            )
        if os.name != 'nt':
            os.chmod(tmp_defaults, 0o600)

        cmd = [
            'mysqldump',
            f'--defaults-extra-file={tmp_defaults}',
            '--single-transaction',   # konsisten tanpa mengunci tabel
            '--no-tablespaces',       # tidak perlu grant global PROCESS pada MySQL
            '--routines',
            '--triggers',
            '--result-file', tmp_sql,
            db_name,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            logger.error("mysqldump gagal (exit %d): %s", result.returncode, result.stderr)
            return None, None
        
        # Kompres dengan gzip
        gz_path = tmp_sql + '.gz'
        with open(tmp_sql, 'rb') as f_in:
            with gzip.open(gz_path, 'wb', compresslevel=6) as f_out:
                while True:
                    chunk = f_in.read(1024 * 1024)  # 1 MB chunks
                    if not chunk:
                        break
                    f_out.write(chunk)
        
        key = f"backups/{db_name}_{timestamp}.sql.gz"
        return gz_path, key
        
    finally:
        # Hapus file SQL mentah (yang disimpan cuma .gz)
        if os.path.exists(tmp_sql):
            os.remove(tmp_sql)
        if os.path.exists(tmp_defaults):
            os.remove(tmp_defaults)


def jalankan_backup():
    """Jalankan backup lengkap: mysqldump → gzip → upload ke R2 (atau simpan lokal).
    Return: (berhasil: bool, pesan: str)"""
    logger.info("Memulai backup database...")
    
    gz_path, key = _run_mysqldump()
    if not gz_path:
        return False, "mysqldump gagal. Periksa log server."
    
    try:
        size_mb = os.path.getsize(gz_path) / (1024 * 1024)
        logger.info("Dump selesai: %s (%.1f MB)", key, size_mb)
        
        if config.R2_ENABLED:
            from storage_r2 import upload_local_file
            ok, pesan = upload_local_file(gz_path, key, content_type='application/gzip')
            if ok:
                logger.info("Backup berhasil diupload ke R2: %s", key)
                return True, f"Backup berhasil: {key} ({size_mb:.1f} MB) → R2"
            else:
                logger.error("Gagal upload backup ke R2: %s", pesan)
                # Fallback: simpan lokal
                return _simpan_lokal(gz_path, key)
        else:
            return _simpan_lokal(gz_path, key)
    finally:
        # Hapus file temp setelah diupload
        if os.path.exists(gz_path):
            os.remove(gz_path)


def _simpan_lokal(gz_path, key):
    """Simpan backup ke folder lokal sebagai fallback."""
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    filename = os.path.basename(key)
    dest = os.path.join(_BACKUP_DIR, filename)
    
    import shutil
    shutil.copy2(gz_path, dest)
    
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    logger.info("Backup tersimpan lokal: %s (%.1f MB)", dest, size_mb)
    return True, f"Backup tersimpan lokal: {filename} ({size_mb:.1f} MB)"


def bersihkan_backup_lama():
    """Hapus backup lokal yang lebih tua dari BACKUP_RETENTION_DAYS."""
    if not os.path.isdir(_BACKUP_DIR):
        return
    
    batas = datetime.now() - timedelta(days=config.BACKUP_RETENTION_DAYS)
    dihapus = 0
    
    for f in os.listdir(_BACKUP_DIR):
        if not f.endswith('.sql.gz'):
            continue
        path = os.path.join(_BACKUP_DIR, f)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime < batas:
                os.remove(path)
                dihapus += 1
        except OSError:
            pass
    
    if dihapus:
        logger.info("Membersihkan %d backup lama (> %d hari).", dihapus, config.BACKUP_RETENTION_DAYS)
