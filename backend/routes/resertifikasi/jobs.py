import logging
from datetime import datetime

from db import db_cursor, log_activity, DatabaseUnavailable
from .constants import BULAN_ID
from .data import get_rekap_data
from .pdf import generate_pdf_rekap
from .mailer import send_email_rekap


def _tandai_terkirim(id_alat_list):
    """Set tgl_email_terkirim = hari ini untuk alat-alat yang barusan berhasil
    dikirimi email OTOMATIS. Dipanggil khusus dari jalur scheduler, bukan manual."""
    if not id_alat_list:
        return
    format_placeholder = ",".join(["%s"] * len(id_alat_list))
    try:
        with db_cursor(dictionary=False, commit=True) as cursor:
            cursor.execute(
                f"UPDATE tbl_alat SET tgl_email_terkirim = CURDATE() WHERE id_alat IN ({format_placeholder})",
                tuple(id_alat_list)
            )
    except DatabaseUnavailable:
        return


# =========================================================
# 4. JOB UTAMA (dipanggil scheduler sesuai jadwal di config.py, lihat scheduler.py,
#    dan juga bisa dipanggil manual dari tombol di halaman web)
# =========================================================
def jalankan_rekap_resertifikasi(bulan_kedepan=None, kirim_email=True, username_trigger='system',
                                  hanya_belum_terkirim=False):
    grouped = get_rekap_data(bulan_kedepan, hanya_belum_terkirim=hanya_belum_terkirim)
    bulan_label = BULAN_ID[datetime.now().month]
    tahun_label = datetime.now().year

    hasil = []
    if not grouped:
        log_activity(username_trigger, 'REKAP_RESERTIFIKASI',
                     'Tidak ada alat yang memasuki masa resertifikasi bulan ini.')
        return hasil

    for pid, g in grouped.items():
        try:
            pdf_path, pdf_filename = generate_pdf_rekap(
                g['nama_perusahaan'], g['alat'], bulan_label, tahun_label
            )
            status_kirim, pesan_kirim = (None, None)
            if kirim_email:
                status_kirim, pesan_kirim = send_email_rekap(
                    g['nama_perusahaan'], g['email_perusahaan'], g['emails_inspektur'],
                    pdf_path, pdf_filename, bulan_label, tahun_label
                )
                if status_kirim and hanya_belum_terkirim:
                    _tandai_terkirim([a['id_alat'] for a in g['alat']])
            hasil.append({
                'nama_perusahaan': g['nama_perusahaan'],
                'jumlah_alat': len(g['alat']),
                'pdf_filename': pdf_filename,
                'terkirim': status_kirim,
                'pesan': pesan_kirim
            })
            log_activity(
                username_trigger, 'REKAP_RESERTIFIKASI',
                f"Rekap {g['nama_perusahaan']} ({len(g['alat'])} alat) - "
                f"{'Email terkirim' if status_kirim else ('Email gagal: ' + str(pesan_kirim) if kirim_email else 'PDF dibuat, tidak dikirim')}"
            )
        except Exception:
            hasil.append({
                'nama_perusahaan': g['nama_perusahaan'],
                'jumlah_alat': len(g['alat']),
                'pdf_filename': None,
                'terkirim': False,
                'pesan': 'Gagal memproses perusahaan ini (detail ada di log server).'
            })
            logging.getLogger(__name__).exception("Gagal proses rekap %s", g['nama_perusahaan'])
            log_activity(username_trigger, 'REKAP_RESERTIFIKASI', f"Gagal proses {g['nama_perusahaan']}")
    return hasil