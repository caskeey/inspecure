from collections import OrderedDict
from datetime import date

import config
from db import db_cursor, DatabaseUnavailable


# =========================================================
# 1. AMBIL & KELOMPOKKAN DATA (alat yang akan memasuki masa resertifikasi, dikelompokkan per perusahaan)
# =========================================================
def get_rekap_data(bulan_kedepan=None, hanya_belum_terkirim=False):
    """
    Ambil semua alat yang tgl_expired-nya jatuh dalam window BULAN KALENDER
    PENUH, mulai dari awal bulan DEPAN sampai akhir bulan ke-(N+1) dari
    sekarang, lalu dikelompokkan per perusahaan.

    Contoh dengan bulan_kedepan=3, dijalankan tanggal 28 Juni:
        window = 1 Juli s.d. 31 Oktober (4 bulan kalender: Jul, Agu, Sep, Okt)
        -> alat expired 9 Oktober otomatis kena di run 28 Juni ini.

    hanya_belum_terkirim:
        False (default) -> tampilkan SEMUA alat dalam window, dipakai untuk
                            halaman web & tombol kirim MANUAL (boleh kirim
                            ulang kapan saja, walau sudah pernah dikirim
                            otomatis sebelumnya).
        True            -> hanya alat yang tgl_email_terkirim masih NULL,
                            dipakai KHUSUS oleh job scheduler OTOMATIS supaya
                            1 alat tidak dikirimi email berulang tiap bulan.

    Return: OrderedDict{ id_perusahaan: {..., 'alat': [...] } }
    """
    if bulan_kedepan is None:
        bulan_kedepan = config.REKAP_BULAN_KEDEPAN

    query = """
        SELECT a.id_alat, a.nama_alat, a.nomor_serial, a.durasi_angka, a.durasi_satuan,
               a.tgl_expired, a.email_inspektur,
               mp.id_perusahaan, mp.nama_perusahaan, mp.email_perusahaan
        FROM tbl_alat a
        JOIN tbl_master_perusahaan mp ON a.id_perusahaan = mp.id_perusahaan
        WHERE a.tgl_expired IS NOT NULL
          AND a.tgl_expired BETWEEN
              DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 1 MONTH), '%%Y-%%m-01')
              AND LAST_DAY(DATE_ADD(CURDATE(), INTERVAL %s MONTH))
    """
    if hanya_belum_terkirim:
        query += " AND a.tgl_email_terkirim IS NULL"
    query += " ORDER BY mp.nama_perusahaan ASC, a.tgl_expired ASC"
    try:
        with db_cursor() as cursor:
            cursor.execute(query, (bulan_kedepan + 1,))
            rows = cursor.fetchall()
    except DatabaseUnavailable:
        return OrderedDict()

    grouped = OrderedDict()
    hari_ini = date.today()
    for r in rows:
        pid = r['id_perusahaan']
        if pid not in grouped:
            grouped[pid] = {
                'id_perusahaan': pid,
                'nama_perusahaan': r['nama_perusahaan'],
                'email_perusahaan': r['email_perusahaan'],
                'emails_inspektur': set(),
                'alat': []
            }
        if r.get('email_inspektur'):
            email_insp = r['email_inspektur'].strip()
            email_pt = (r.get('email_perusahaan') or '').strip()
            # Jangan masukin ke daftar "inspektur" kalau kebetulan sama persis
            # dengan email perusahaan -- itu udah ditampilin sendiri di sebelah
            # ikon amplop, gak perlu diulang lagi di daftar inspektur.
            if email_insp.lower() != email_pt.lower():
                grouped[pid]['emails_inspektur'].add(email_insp)
        tgl_exp = r.get('tgl_expired')
        r['hari_tersisa'] = (tgl_exp - hari_ini).days if tgl_exp else None
        grouped[pid]['alat'].append(r)
    return grouped


def safe_filename(text):
    keep = "".join(c if c.isalnum() or c in (' ', '_', '-') else '' for c in text)
    return "_".join(keep.split())