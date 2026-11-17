"""
Object storage helper — Cloudflare R2 (S3-compatible lewat boto3), dengan
fallback otomatis ke disk lokal (static/uploads) kalau kredensial R2 belum
diisi di .env. Jadi kode di routes/*.py TIDAK PERLU tahu lagi apakah dia
lagi nyimpen ke R2 atau ke lokal -- cukup panggil fungsi di sini.

Konsep "key": setiap file punya satu string unik, contoh:
    "dokumen/AB1234_sertifikat.pdf"
    "rekap/rekap_PT_Solusi_Bangun_Juni_2026.pdf"
Key inilah yang disimpan di kolom database (dokumen_path, dokumen_lama, dst),
BUKAN URL penuh. URL/link cuma dibangkitkan on-demand pas mau ditampilkan
(lewat get_url), supaya kalau suatu saat pindah bucket/provider lagi,
data di database tidak perlu diubah.
"""
import os
import logging

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy init boto3 client, cuma dibikin kalau R2_ENABLED. Import boto3
    di dalam fungsi (bukan di top-level) supaya app tetap bisa jalan biarpun
    boto3 belum ke-install saat R2 belum dipakai (development lokal)."""
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config as BotoConfig
        _client = boto3.client(
            's3',
            endpoint_url=config.R2_ENDPOINT_URL,
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version='s3v4', region_name='auto'),
        )
    return _client


def _local_path(key):
    """Path fallback di disk lokal untuk sebuah key, di dalam static/uploads
    (dipertahankan sama seperti struktur lama supaya file lama yang belum
    sempat dimigrasi masih ketemu)."""
    from flask import current_app
    return os.path.join(current_app.config['UPLOAD_FOLDER'], key.replace('/', '_'))


def upload_file(file_obj, key, content_type=None):
    """Upload sebuah file (Werkzeug FileStorage, atau file-like object yang
    sudah di-seek(0)) ke R2 dengan nama `key`. Kalau R2 belum dikonfigurasi,
    otomatis simpan ke disk lokal sebagai fallback.
    Return: (ok: bool, pesan: str)
    """
    if config.R2_ENABLED:
        try:
            client = _get_client()
            extra_args = {'ContentType': content_type} if content_type else {}
            client.upload_fileobj(file_obj, config.R2_BUCKET_NAME, key, ExtraArgs=extra_args)
            return True, f"Tersimpan ke R2: {key}"
        except Exception as e:
            logger.exception("Gagal upload ke R2, key=%s", key)
            return False, "Gagal upload ke R2."
    else:
        try:
            path = _local_path(key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            file_obj.seek(0)
            with open(path, 'wb') as f:
                f.write(file_obj.read())
            return True, f"Tersimpan lokal (R2 belum dikonfigurasi): {path}"
        except Exception as e:
            logger.exception("Gagal simpan lokal, key=%s", key)
            return False, "Gagal menyimpan file."


def upload_local_file(local_path, key, content_type=None):
    """Upload file yang SUDAH ADA di disk (misal PDF rekap yang baru selesai
    di-generate reportlab) ke R2. Dipakai buat arsip permanen tanpa
    mengganggu proses lokal (generate PDF, lampirkan ke email) yang sudah
    jalan duluan. Kalau R2 belum dikonfigurasi, fungsi ini no-op (file
    lokalnya kan sudah ada di static/rekap_resertifikasi)."""
    if not config.R2_ENABLED:
        return False, "R2 belum dikonfigurasi, PDF tetap tersimpan lokal saja."
    try:
        client = _get_client()
        extra_args = {'ContentType': content_type} if content_type else {}
        client.upload_file(local_path, config.R2_BUCKET_NAME, key, ExtraArgs=extra_args)
        return True, f"Arsip PDF tersimpan ke R2: {key}"
    except Exception as e:
        logger.exception("Gagal arsip PDF ke R2, key=%s", key)
        return False, "Gagal mengarsipkan PDF ke R2."


def delete_file(key):
    """Hapus file dari R2 (atau lokal kalau fallback). Tidak error keras
    kalau file memang sudah tidak ada -- delete itu sifatnya idempotent."""
    if config.R2_ENABLED:
        try:
            client = _get_client()
            client.delete_object(Bucket=config.R2_BUCKET_NAME, Key=key)
            return True, "Dihapus dari R2"
        except Exception as e:
            logger.exception("Gagal hapus dari R2, key=%s", key)
            return False, "Gagal menghapus dari R2."
    else:
        try:
            path = _local_path(key)
            if os.path.exists(path):
                os.remove(path)
            return True, "Dihapus dari disk lokal"
        except Exception as e:
            logger.exception("Gagal hapus lokal, key=%s", key)
            return False, "Gagal menghapus file."


def get_url(key, expires_in=None, download_filename=None):
    """Bangkitkan URL buat lihat/download sebuah key.
    - Kalau R2 aktif: presigned URL, expired otomatis setelah `expires_in`
      detik (default dari config.R2_PRESIGNED_EXPIRY_SECONDS).
    - Kalau R2 belum aktif: fallback ke url_for('static', ...) lokal.
    """
    if config.R2_ENABLED:
        try:
            client = _get_client()
            params = {'Bucket': config.R2_BUCKET_NAME, 'Key': key}
            if download_filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'
            return client.generate_presigned_url(
                'get_object', Params=params,
                ExpiresIn=expires_in or config.R2_PRESIGNED_EXPIRY_SECONDS,
            )
        except Exception:
            logger.exception("Gagal generate presigned URL, key=%s", key)
            return None
    else:
        from flask import url_for
        return url_for('static', filename=f"uploads/{key.replace('/', '_')}")


def download_to_temp(key, suffix=''):
    """Download isi sebuah key ke file temp lokal, dipakai kalau butuh bytes
    fisiknya (misal mau dilampirkan lagi ke email). Return path temp file,
    atau None kalau gagal. Pemanggil bertanggung jawab hapus temp file-nya
    setelah selesai dipakai."""
    import tempfile
    if config.R2_ENABLED:
        try:
            client = _get_client()
            fd, tmp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            client.download_file(config.R2_BUCKET_NAME, key, tmp_path)
            return tmp_path
        except Exception:
            logger.exception("Gagal download dari R2, key=%s", key)
            return None
    else:
        path = _local_path(key)
        return path if os.path.exists(path) else None