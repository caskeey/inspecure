"""Pembersihan dan validasi nilai yang dibaca dari Excel."""
from datetime import date, datetime
import mysql.connector
import pandas as pd
from error_utils import pesan_aman, PesanUser

def _teks(v):
    """Sel Excel -> teks bersih, atau None kalau kosong. Angka bulat (12345.0) jadi '12345'."""
    if v is None or pd.isna(v):
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    v = str(v).strip()
    return v or None


def _angka(v, nama):
    t = _teks(v)
    try:
        return int(float(t))
    except (TypeError, ValueError):
        raise PesanUser(f"{nama} harus berupa angka")


def _tanggal(v):
    """Sel Excel -> 'YYYY-MM-DD'. Sel bertipe tanggal diterima apa adanya; teks harus berformat YYYY-MM-DD."""
    if v is None or pd.isna(v):
        raise PesanUser("tgl_sertifikasi kosong")
    if isinstance(v, date):  # termasuk datetime & pandas Timestamp
        return v.strftime('%Y-%m-%d')
    teks = str(v).strip()[:10]
    try:
        datetime.strptime(teks, '%Y-%m-%d')
    except ValueError:
        raise PesanUser("tgl_sertifikasi harus berformat YYYY-MM-DD (contoh 2025-01-31)")
    return teks


def _pesan_baris(e):
    """Pesan singkat & aman untuk satu baris yang gagal diimport."""
    if isinstance(e, PesanUser):
        return str(e)
    if isinstance(e, mysql.connector.IntegrityError) and e.errno == 1452:  # foreign key tidak cocok
        return "id_pekerjaan / id_peralatan tidak ada di data master"
    return pesan_aman(e).rstrip('.')  # dicatat di log server; user hanya melihat pesan umum
