"""Koneksi database MySQL: connection pool + context manager.

Cara pakai (koneksi OTOMATIS kembali ke pool, walau terjadi error / return di tengah):

    # 1 cursor, baca saja
    with db_cursor() as cursor:
        cursor.execute("SELECT ...")
        rows = cursor.fetchall()

    # tulis data -> commit otomatis saat blok selesai tanpa error
    with db_cursor(commit=True) as cursor:
        cursor.execute("INSERT ...")

    # butuh kontrol manual (commit di tengah, banyak cursor)
    with db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        ...
        conn.commit()

Aturan:
- Kalau blok keluar karena error, transaksi yang belum di-commit di-ROLLBACK.
- Jangan panggil conn.close() sendiri; context manager yang mengurus.
- Jangan menahan koneksi saat melakukan pekerjaan lambat (upload R2, kirim email, hash password):
  ambil data dulu, keluar dari blok `with`, baru kerjakan.
- Kalau DB tidak bisa dihubungi, dilempar DatabaseUnavailable.

Env (opsional):
  DB_POOL_SIZE  jumlah koneksi di pool (default 10, maks 32). Gunicorn memakai 4 thread dan
                satu request kadang butuh 2 koneksi sekaligus, jadi jangan di bawah 10.
  DB_POOL_WAIT  detik menunggu koneksi kosong sebelum menyerah (default 5).
"""
import logging
import os
import threading
import time
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

logger = logging.getLogger('inspecure')

# Password database WAJIB diisi lewat environment (tanpa nilai bawaan), supaya tidak ada
# password tebakan yang tertinggal di kode. Docker: diisi otomatis dari DB_PASSWORD (docker-compose.yml).
# Development lokal: tambahkan MYSQLPASSWORD=... di file .env.
_db_password = os.environ.get('MYSQLPASSWORD', '')
if not _db_password:
    raise RuntimeError(
        "MYSQLPASSWORD belum diisi. Isi di .env (development lokal) atau pastikan "
        "DB_PASSWORD terisi di .env (Docker)."
    )

db_config = {
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'port': int(os.environ.get('MYSQLPORT', 3306)),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': _db_password,
    'database': os.environ.get('MYSQLDATABASE', 'db_inspecure'),
}

POOL_SIZE = max(1, min(int(os.environ.get('DB_POOL_SIZE', 10)), 32))  # 32 = batas connector
POOL_WAIT_SECONDS = float(os.environ.get('DB_POOL_WAIT', 5))


class DatabaseUnavailable(Exception):
    """Database tidak bisa dihubungi (mati, salah kredensial, atau pool habis)."""


_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """Bikin pool saat pertama dipakai (bukan saat import), supaya app tetap bisa start
    walau MySQL belum siap. Kalau gagal, percobaan berikutnya mencoba lagi."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pooling.MySQLConnectionPool(
                    pool_name='inspecure',
                    pool_size=POOL_SIZE,
                    pool_reset_session=True,   # bersihkan state sesi tiap koneksi dikembalikan
                    buffered=True,             # cursor di-buffer: tidak ada "Unread result found"
                    connection_timeout=10,
                    **db_config,
                )
    return _pool


def _acquire():
    """Ambil koneksi dari pool. Kalau pool penuh, tunggu sebentar (maks DB_POOL_WAIT detik).
    Koneksi yang sudah mati (MySQL restart / idle timeout) disambung ulang otomatis oleh pool."""
    deadline = time.monotonic() + POOL_WAIT_SECONDS
    while True:
        try:
            return _get_pool().get_connection()
        except pooling.PoolError as err:
            if 'exhausted' in str(err) and time.monotonic() < deadline:
                time.sleep(0.05)
                continue
            logger.error("Pool koneksi database bermasalah: %s", err)
            raise DatabaseUnavailable("Koneksi database gagal") from err
        except mysql.connector.Error as err:
            logger.error("Koneksi database gagal: %s", err)
            raise DatabaseUnavailable("Koneksi database gagal") from err


def _release(conn):
    """Rollback kalau masih ada transaksi menggantung, lalu kembalikan koneksi ke pool."""
    try:
        if conn.in_transaction:
            conn.rollback()
    except Exception:
        logger.warning("Rollback sebelum melepas koneksi gagal", exc_info=True)
    finally:
        try:
            conn.close()  # untuk koneksi dari pool: dikembalikan ke pool, bukan ditutup
        except Exception:
            logger.warning("Gagal mengembalikan koneksi ke pool", exc_info=True)


@contextmanager
def db_connection():
    """Pinjam satu koneksi dari pool. Selalu dikembalikan, apa pun yang terjadi di dalam blok."""
    conn = _acquire()
    try:
        yield conn
    finally:
        _release(conn)


@contextmanager
def db_cursor(dictionary=True, commit=False):
    """Pinjam koneksi + cursor sekaligus. commit=True -> commit otomatis kalau blok selesai
    tanpa error (kalau error, di-rollback)."""
    with db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()


def get_db_connection():
    """LEGACY: dipertahankan supaya kode lama tidak patah. Pakai db_connection()/db_cursor().
    Koneksi dari sini WAJIB di-close() manual; kalau gagal konek mengembalikan None."""
    try:
        return _acquire()
    except DatabaseUnavailable:
        return None


def log_activity(username, action, details):
    """Mencatat aktivitas user ke tabel tbl_activity_logs. Gagal mencatat tidak boleh
    menggagalkan request, jadi semua error hanya dicatat ke log server."""
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT id_users FROM tbl_users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    "INSERT INTO tbl_activity_logs (id_users, action, details) VALUES (%s, %s, %s)",
                    (user['id_users'], action, details))
    except Exception:
        logger.exception("Gagal mencatat log aktivitas")