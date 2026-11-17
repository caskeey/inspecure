from flask import render_template, request, redirect, url_for, flash, session

from db import db_cursor, log_activity
from auth_utils import login_required, admin_required
from error_utils import pesan_aman, PesanUser
from . import alat_bp
from .helpers import hitung_tgl_expired, hitung_status, safe_int, build_dokumen_key
from storage_r2 import upload_file, get_url


@alat_bp.route('/daftar_resertifikasi')
@login_required
@admin_required
def daftar_resertifikasi():
    return render_template('daftar_resertifikasi.html', active_page='resertifikasi_alat')


@alat_bp.route('/resertifikasi_alat/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def resertifikasi_alat(id):
    if request.method == 'POST':
        try:
            # 1. Cek alatnya ada + ambil rfid_uid (buat nama file dokumen). Koneksi langsung dilepas
            #    sebelum upload ke R2, karena upload bisa lama.
            with db_cursor() as cursor:
                cursor.execute("SELECT rfid_uid FROM tbl_alat WHERE id_alat=%s", (id,))
                ada = cursor.fetchone()
            if not ada:
                flash("Alat tidak ditemukan.", "error")
                return redirect(url_for('alat.data_master'))

            # 2. Hitung data sertifikasi BARU dari form
            tgl_sertif_str = request.form.get('tgl_sertifikasi')
            durasi = safe_int(request.form.get('durasi_angka')) or 0
            satuan = request.form.get('durasi_satuan')

            tgl_expired_str = hitung_tgl_expired(tgl_sertif_str, durasi, satuan)
            status = hitung_status(tgl_expired_str)

            dokumen_baru = None
            file = request.files.get('dokumen_pendukung')
            if file and file.filename != '':
                key = build_dokumen_key(ada['rfid_uid'], file.filename)
                ok, pesan = upload_file(file, key, content_type=file.mimetype)
                if not ok:
                    raise PesanUser(pesan)
                dokumen_baru = key

            # 3. Arsipkan data lama lalu timpa dengan yang baru, dalam SATU transaksi.
            #    FOR UPDATE mengunci barisnya, jadi yang diarsipkan pasti persis yang ditimpa.
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    "SELECT tgl_sertifikasi, tgl_expired, status_sertifikasi, dokumen_path "
                    "FROM tbl_alat WHERE id_alat=%s FOR UPDATE", (id,)
                )
                lama = cursor.fetchone()
                if not lama:
                    flash("Alat tidak ditemukan.", "error")
                    return redirect(url_for('alat.data_master'))

                cursor.execute("""
                    INSERT INTO tbl_riwayat_sertifikasi
                    (id_alat, tgl_sertifikasi_lama, tgl_expired_lama, status_lama, dokumen_lama, dicatat_oleh)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id, lama['tgl_sertifikasi'], lama['tgl_expired'], lama['status_sertifikasi'],
                      lama['dokumen_path'], session['user']))

                cursor.execute("""
                    UPDATE tbl_alat SET tgl_sertifikasi=%s, durasi_angka=%s, durasi_satuan=%s,
                    tgl_expired=%s, status_sertifikasi=%s, dokumen_path=%s WHERE id_alat=%s
                """, (tgl_sertif_str, durasi, satuan, tgl_expired_str, status,
                      dokumen_baru or lama['dokumen_path'], id))

            log_activity(session['user'], 'RESERTIFIKASI', f"Resertifikasi ulang alat ID {id}")
            flash("Resertifikasi berhasil! Data sertifikasi lama sudah diarsipkan ke riwayat.", "success")
            return redirect(url_for('alat.detail_alat', id=id))
        except Exception as e:
            flash(pesan_aman(e), "error")

    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM tbl_alat WHERE id_alat=%s", (id,))
        alat = cursor.fetchone()
    if alat:
        alat['id'] = alat['id_alat']
        if alat.get('dokumen_path'):
            alat['dokumen_url'] = get_url(alat['dokumen_path'])
    return render_template('resertifikasi_alat.html', alat=alat, active_page='resertifikasi_alat')