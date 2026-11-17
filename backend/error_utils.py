"""Penanganan error yang aman: detail teknis hanya masuk log server, user cuma lihat pesan umum."""
import logging

import mysql.connector

logger = logging.getLogger('inspecure')

PESAN_UMUM = 'Terjadi kesalahan pada server. Silakan coba lagi atau hubungi Admin.'


class PesanUser(Exception):
    """Exception yang isi pesannya SUDAH aman ditampilkan ke user (tidak ada detail teknis)."""


def pesan_aman(e, konteks=None):
    """Catat error lengkap (beserta traceback) ke log server, lalu kembalikan pesan yang aman
    ditampilkan ke user. Panggil di dalam blok `except Exception as e:`."""
    if konteks is None:
        try:
            from flask import request, has_request_context
            konteks = request.path if has_request_context() else 'di luar request'
        except Exception:
            konteks = '-'
    logger.error("Error di %s: %s", konteks, e, exc_info=e)

    if isinstance(e, PesanUser):
        return str(e)
    if isinstance(e, mysql.connector.IntegrityError) and e.errno == 1062:  # data duplikat
        msg = str(e.msg or '')
        if 'rfid_uid' in msg:
            return 'RFID UID sudah terdaftar.'
        if 'username' in msg:
            return 'Username sudah dipakai.'
        return 'Data duplikat: nilai tersebut sudah terdaftar.'
    if isinstance(e, ValueError):
        return 'Data yang dimasukkan tidak valid. Periksa kembali isian form.'
    return PESAN_UMUM