import os
from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify

from db import db_connection, db_cursor, log_activity
from auth_utils import login_required, admin_required
from . import alat_bp
from .helpers import hitung_tgl_expired, hitung_status, get_or_create_perusahaan, get_or_create_peralatan, get_master_data, safe_int, build_dokumen_key
from storage_r2 import upload_file, delete_file
from error_utils import pesan_aman, PesanUser


@alat_bp.route('/tambah_alat', methods=['GET', 'POST'])
@login_required
@admin_required
def tambah_alat():
    if request.method == 'POST':
        try:
            uid = request.form.get('rfid_uid')
            serial = request.form.get('nomor_serial')
            nama = request.form.get('nama_alat')
            email_inspektur = request.form.get('email_inspektur')

            nama_pt_input = request.form.get('nama_perusahaan')
            email_pt_input = request.form.get('email_perusahaan')
            pt_id = get_or_create_perusahaan(nama_pt_input, email_pt_input)

            id_pekerjaan = safe_int(request.form.get('jenis_pekerjaan'))
            # Baik dari dropdown (K3/Laik Operasi) maupun input teks manual (LAINNYA/Laik Fungsi),
            # sama-sama diproses lewat get_or_create_peralatan: kalau nama sudah ada di master
            # (untuk id_pekerjaan yang sama) dipakai id yang sudah ada, kalau belum ada dibikinkan
            # baru otomatis.
            peralatan_input = request.form.get('jenis_peralatan_select') or request.form.get('jenis_peralatan_text')
            id_peralatan = get_or_create_peralatan(peralatan_input, id_pekerjaan)

            tgl_sertif_str = request.form.get('tgl_sertifikasi')
            durasi = safe_int(request.form.get('durasi_angka')) or 0
            satuan = request.form.get('durasi_satuan')

            tgl_expired_str = hitung_tgl_expired(tgl_sertif_str, durasi, satuan)
            status = hitung_status(tgl_expired_str)

            dokumen_filename = None
            if 'dokumen_pendukung' in request.files:
                file = request.files['dokumen_pendukung']
                if file.filename != '':
                    key = build_dokumen_key(uid, file.filename)
                    ok, pesan = upload_file(file, key, content_type=file.mimetype)
                    if not ok:
                        raise PesanUser(pesan)
                    dokumen_filename = key

            query = """
                INSERT INTO tbl_alat 
                (rfid_uid, nomor_serial, nama_alat, id_pekerjaan, id_peralatan, 
                 id_perusahaan, email_inspektur, tgl_sertifikasi, durasi_angka, durasi_satuan, 
                 tgl_expired, status_sertifikasi, dokumen_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            with db_cursor(dictionary=False, commit=True) as cursor:
                cursor.execute(query, (uid, serial, nama, id_pekerjaan, id_peralatan,
                                       pt_id, email_inspektur, tgl_sertif_str,
                                       durasi, satuan, tgl_expired_str, status, dokumen_filename))
            log_activity(session['user'], 'TAMBAH_ALAT', f"Menambah alat: {nama}")
            flash(f"Sukses! Alat {nama} berhasil disimpan.", "success")
            return redirect(url_for('alat.data_master'))

        except Exception as e:
            flash(pesan_aman(e), "error")

    pek, per, pt = get_master_data()
    prefill_uid = request.args.get('uid', '')
    return render_template('tambah_alat.html', active_page='tambah', pekerjaan=pek, peralatan=per, perusahaan=pt, prefill_uid=prefill_uid)


@alat_bp.route('/edit_alat/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_alat(id):
    with db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        if request.method == 'POST':
            try:
                # Ambil data lama dulu, buat dibandingkan & (kalau perlu) diarsipkan
                cursor.execute(
                    "SELECT rfid_uid, tgl_sertifikasi, tgl_expired, status_sertifikasi, dokumen_path "
                    "FROM tbl_alat WHERE id_alat=%s", (id,)
                )
                lama = cursor.fetchone()

                serial = request.form.get('nomor_serial')
                nama = request.form.get('nama_alat')
                email_inspektur = request.form.get('email_inspektur')

                pt_id = request.form.get('perusahaan')
                email_pt_input = request.form.get('email_perusahaan')
                if pt_id and email_pt_input:
                    cursor.execute("UPDATE tbl_master_perusahaan SET email_perusahaan=%s WHERE id_perusahaan=%s", (email_pt_input, pt_id))

                id_pekerjaan = safe_int(request.form.get('jenis_pekerjaan'))
                # Sama seperti tambah_alat: unifikasi dropdown & input manual lewat get_or_create_peralatan.
                peralatan_input = request.form.get('jenis_peralatan_select') or request.form.get('jenis_peralatan_text')
                id_peralatan = get_or_create_peralatan(peralatan_input, id_pekerjaan)

                tgl_sertif_str = request.form.get('tgl_sertifikasi')
                durasi = safe_int(request.form.get('durasi_angka')) or 0
                satuan = request.form.get('durasi_satuan')

                tgl_expired_str = hitung_tgl_expired(tgl_sertif_str, durasi, satuan)
                status = hitung_status(tgl_expired_str)

                dokumen_filename = request.form.get('old_dokumen')
                if 'dokumen_pendukung' in request.files:
                    file = request.files['dokumen_pendukung']
                    if file.filename != '':
                        uid_lama = request.form.get('rfid_uid') or (lama['rfid_uid'] if lama else '')
                        key = build_dokumen_key(uid_lama, file.filename)
                        ok, pesan = upload_file(file, key, content_type=file.mimetype)
                        if not ok:
                            raise PesanUser(pesan)
                        dokumen_filename = key

                # Kalau tanggal sertifikasi/expired beneran berubah dari sebelumnya,
                # arsipkan data lama ke tbl_riwayat_sertifikasi dulu sebelum ditimpa.
                cert_berubah = lama and (
                    str(lama['tgl_sertifikasi']) != tgl_sertif_str or
                    str(lama['tgl_expired']) != tgl_expired_str
                )
                if cert_berubah:
                    cursor.execute("""
                        INSERT INTO tbl_riwayat_sertifikasi
                        (id_alat, tgl_sertifikasi_lama, tgl_expired_lama, status_lama, dokumen_lama, dicatat_oleh)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id, lama['tgl_sertifikasi'], lama['tgl_expired'], lama['status_sertifikasi'],
                          lama['dokumen_path'], session['user']))

                query = """
                    UPDATE tbl_alat SET 
                    nomor_serial=%s, nama_alat=%s, id_pekerjaan=%s, id_peralatan=%s, id_perusahaan=%s, 
                    email_inspektur=%s, tgl_sertifikasi=%s, durasi_angka=%s, durasi_satuan=%s, 
                    tgl_expired=%s, status_sertifikasi=%s, dokumen_path=%s
                    WHERE id_alat=%s
                """
                cursor.execute(query, (serial, nama, id_pekerjaan, id_peralatan, pt_id, email_inspektur,
                                       tgl_sertif_str, durasi, satuan, tgl_expired_str, status, dokumen_filename, id))
                conn.commit()
                log_activity(session['user'], 'EDIT_ALAT', f"Update alat ID: {id}" + (" (sertifikasi diperbarui)" if cert_berubah else ""))
                flash("Data berhasil diperbarui!", "success")
                return redirect(url_for('alat.data_master'))
            except Exception as e:
                conn.rollback()  # buang perubahan setengah jadi sebelum halaman form ditampilkan lagi
                flash(pesan_aman(e), "error")

        cursor.execute("""
            SELECT a.*,
                mpk.nama_pekerjaan as jenis_pekerjaan,
                mpl.nama_peralatan as jenis_alat,
                a.id_perusahaan as perusahaan_id,
                mpr.email_perusahaan as email_perusahaan
            FROM tbl_alat a
            LEFT JOIN tbl_master_pekerjaan mpk ON a.id_pekerjaan = mpk.id_pekerjaan
            LEFT JOIN tbl_master_peralatan mpl ON a.id_peralatan = mpl.id_peralatan
            LEFT JOIN tbl_master_perusahaan mpr ON a.id_perusahaan = mpr.id_perusahaan
            WHERE a.id_alat=%s
        """, (id,))
        alat = cursor.fetchone()
        if alat:
            alat['id'] = alat['id_alat']
            if alat.get('dokumen_path'):
                from storage_r2 import get_url
                alat['dokumen_url'] = get_url(alat['dokumen_path'])

    pek, per, pt = get_master_data()
    return render_template('edit_alat.html', alat=alat, pekerjaan=pek, peralatan=per, perusahaan=pt)


@alat_bp.route('/hapus_alat/<int:id>', methods=['POST'])
@login_required
@admin_required
def hapus_alat(id):
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT dokumen_path FROM tbl_alat WHERE id_alat = %s", (id,))
            row = cursor.fetchone()
            dokumen_path = row['dokumen_path'] if row else None
            cursor.execute("DELETE FROM tbl_alat WHERE id_alat = %s", (id,))

        if dokumen_path:
            delete_file(dokumen_path)  # gagal hapus file fisik tidak menggagalkan penghapusan record

        log_activity(session['user'], 'HAPUS_ALAT', f"Hapus alat ID {id}")
        flash("Data dihapus.", "success")
    except Exception as e:
        flash(pesan_aman(e), "error")
    return redirect(url_for('alat.data_master'))
