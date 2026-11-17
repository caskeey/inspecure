import base64
import mimetypes
import os
from datetime import datetime

from flask import render_template, redirect, url_for, session, flash, send_from_directory, request, jsonify

import config
from db import log_activity
from auth_utils import login_required, admin_required
from . import resertifikasi_bp
from .constants import (REKAP_DIR, LOGO_DANANTARA_PATH, LOGO_IDSURVEY_PATH,
                        LOGO_SUCOFINDO_PATH, BULAN_ID)
from .data import get_rekap_data
from .pdf import generate_pdf_rekap
from .mailer import (send_email_rekap, build_email_rekap_content,
                     get_email_rekap_recipients)
from .jobs import jalankan_rekap_resertifikasi


# =========================================================
# 5. ROUTES (halaman web + trigger manual)
# =========================================================
@resertifikasi_bp.route('/resertifikasi')
@login_required
def resertifikasi_page():
    grouped = get_rekap_data()
    grouped_otomatis = get_rekap_data(hanya_belum_terkirim=True)
    daftar = list(grouped.values())
    total_alat = sum(len(g['alat']) for g in daftar)
    return render_template(
        'resertifikasi.html', active_page='resertifikasi',
        daftar_perusahaan=daftar, total_perusahaan=len(daftar), total_alat=total_alat,
        perusahaan_menunggu_otomatis=set(grouped_otomatis.keys()),
        bulan_kedepan=config.REKAP_BULAN_KEDEPAN,
        jadwal_hari=config.REKAP_HARI, jadwal_jam=config.REKAP_JAM, jadwal_menit=config.REKAP_MENIT
    )


@resertifikasi_bp.route('/resertifikasi/download/<int:id_perusahaan>')
@login_required
def download_rekap(id_perusahaan):
    grouped = get_rekap_data()
    g = grouped.get(id_perusahaan)
    if not g:
        flash("Tidak ada data resertifikasi untuk perusahaan ini.", "error")
        return redirect(url_for('resertifikasi.resertifikasi_page'))
    pdf_path, pdf_filename = generate_pdf_rekap(g['nama_perusahaan'], g['alat'])
    return send_from_directory(REKAP_DIR, pdf_filename, as_attachment=True)


@resertifikasi_bp.route('/resertifikasi/preview/<int:id_perusahaan>')
@login_required
def preview_rekap(id_perusahaan):
    """Sama seperti download, tapi dibuka langsung di tab browser (bukan
    dipaksa download) supaya bisa dilihat dulu sebelum diputuskan dikirim."""
    grouped = get_rekap_data()
    g = grouped.get(id_perusahaan)
    if not g:
        flash("Tidak ada data resertifikasi untuk perusahaan ini.", "error")
        return redirect(url_for('resertifikasi.resertifikasi_page'))
    pdf_path, pdf_filename = generate_pdf_rekap(g['nama_perusahaan'], g['alat'])
    return send_from_directory(REKAP_DIR, pdf_filename, as_attachment=False)


@resertifikasi_bp.route('/resertifikasi/preview-otomatis/<int:id_perusahaan>')
@login_required
def preview_email_otomatis(id_perusahaan):
    """Pratinjau email+PDF dengan filter dan penerima yang dipakai scheduler."""
    grouped = get_rekap_data(hanya_belum_terkirim=True)
    g = grouped.get(id_perusahaan)
    if not g:
        flash("Perusahaan ini tidak memiliki rekap yang menunggu pengiriman otomatis.", "error")
        return redirect(url_for('resertifikasi.resertifikasi_page'))

    bulan_label = BULAN_ID[datetime.now().month]
    tahun_label = datetime.now().year
    pdf_path, pdf_filename = generate_pdf_rekap(g['nama_perusahaan'], g['alat'], bulan_label, tahun_label)
    subject, email_html, email_text = build_email_rekap_content(g['nama_perusahaan'], bulan_label, tahun_label)
    penerima = get_email_rekap_recipients(g['email_perusahaan'], g['emails_inspektur'], 'both')
    bcc = list(config.EMAIL_BCC_DEFAULT)

    # Tampilkan logo inline di browser dengan data URI, sama seperti CID pada email.
    for cid, path in [('logo_danantara', LOGO_DANANTARA_PATH),
                      ('logo_idsurvey', LOGO_IDSURVEY_PATH),
                      ('logo_sucofindo', LOGO_SUCOFINDO_PATH)]:
        if os.path.exists(path):
            mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            with open(path, 'rb') as logo_file:
                data_uri = f"data:{mime};base64,{base64.b64encode(logo_file.read()).decode('ascii')}"
            email_html = email_html.replace(f'src="cid:{cid}"', f'src="{data_uri}"')

    return render_template(
        'resertifikasi_preview_email.html', active_page='resertifikasi',
        nama_perusahaan=g['nama_perusahaan'], subject=subject, email_html=email_html,
        email_text=email_text, penerima=penerima, bcc=bcc, pdf_filename=pdf_filename,
        pdf_url=url_for('resertifikasi.preview_pdf_otomatis', id_perusahaan=id_perusahaan),
        bulan_label=bulan_label, tahun_label=tahun_label,
        jumlah_alat=len(g['alat']), jadwal_hari=config.REKAP_HARI,
        jadwal_jam=config.REKAP_JAM, jadwal_menit=config.REKAP_MENIT
    )


@resertifikasi_bp.route('/resertifikasi/preview-otomatis/<int:id_perusahaan>/lampiran')
@login_required
def preview_pdf_otomatis(id_perusahaan):
    grouped = get_rekap_data(hanya_belum_terkirim=True)
    g = grouped.get(id_perusahaan)
    if not g:
        flash("Lampiran otomatis tidak tersedia karena data sudah berubah.", "error")
        return redirect(url_for('resertifikasi.resertifikasi_page'))
    bulan_label = BULAN_ID[datetime.now().month]
    tahun_label = datetime.now().year
    _, pdf_filename = generate_pdf_rekap(g['nama_perusahaan'], g['alat'], bulan_label, tahun_label)
    return send_from_directory(REKAP_DIR, pdf_filename, as_attachment=False)


@resertifikasi_bp.route('/resertifikasi/kirim/<int:id_perusahaan>', methods=['POST'])
@login_required(json=True)
@admin_required(json=True)
def kirim_rekap_manual(id_perusahaan):

    target = request.form.get('target') or request.args.get('target') or 'both'
    if target not in ('both', 'perusahaan', 'inspektur'):
        target = 'both'

    grouped = get_rekap_data()
    g = grouped.get(id_perusahaan)
    if not g:
        return jsonify({'status': 'error', 'msg': 'Tidak ada data resertifikasi untuk perusahaan ini'})

    pdf_path, pdf_filename = generate_pdf_rekap(g['nama_perusahaan'], g['alat'])
    ok, pesan = send_email_rekap(
        g['nama_perusahaan'], g['email_perusahaan'], g['emails_inspektur'], pdf_path, pdf_filename,
        target=target
    )
    label_target = {'both': 'perusahaan+inspektur', 'perusahaan': 'perusahaan', 'inspektur': 'inspektur'}[target]
    log_activity(session['user'], 'KIRIM_REKAP_MANUAL', f"{g['nama_perusahaan']} ({label_target}): {pesan}")
    return jsonify({'status': 'success' if ok else 'error', 'msg': pesan})


@resertifikasi_bp.route('/resertifikasi/jalankan_semua', methods=['POST'])
@login_required(json=True)
@admin_required(json=True)
def jalankan_semua_manual():

    hasil = jalankan_rekap_resertifikasi(kirim_email=True, username_trigger=session['user'])
    return jsonify({'status': 'success', 'hasil': hasil})
