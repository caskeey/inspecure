import os
from flask import render_template, request, redirect, url_for, flash, current_app

from db import db_cursor
from auth_utils import login_required, admin_required
from . import alat_bp
from .helpers import build_dokumen_key
from storage_r2 import upload_file, delete_file, get_url
from error_utils import pesan_aman


@alat_bp.route('/aktivasi-rfid')
def aktivasi_rfid_alamat_lama():
    """Alamat lama (pakai tanda strip) -> diarahkan ke halaman yang sebenarnya, supaya bookmark lama tetap jalan."""
    return redirect(url_for('alat.aktivasi_rfid'), code=301)


@alat_bp.route('/aktivasi_rfid')
@login_required
def aktivasi_rfid():
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT a.*, mp.nama_perusahaan 
            FROM tbl_alat a
            LEFT JOIN tbl_master_perusahaan mp ON a.id_perusahaan = mp.id_perusahaan 
            ORDER BY id_alat DESC
        """)
        items = cursor.fetchall()
    for i in items: i['id'] = i['id_alat']
    return render_template('aktivasi_rfid.html', active_page='aktivasi', items=items)


@alat_bp.route('/detail/<int:id>')
@login_required
def detail_alat(id):

    # QUERY: Hanya ambil kolom yang ADA di database
    query = """
        SELECT 
            a.id_alat as id, 
            a.rfid_uid, 
            a.nomor_serial, 
            a.nama_alat, 
            mpk.nama_pekerjaan as jenis_pekerjaan, 
            mpl.nama_peralatan as jenis_alat, 
            mpr.nama_perusahaan, 
            mpr.email_perusahaan, 
            mpr.kontak_person, -- Kita ambil ini untuk info kontak
            a.tgl_expired, 
            a.tgl_sertifikasi, 
            a.status_sertifikasi, 
            a.durasi_angka, 
            a.durasi_satuan, 
            a.email_inspektur, 
            a.dokumen_path as foto
        FROM tbl_alat a
        LEFT JOIN tbl_master_perusahaan mpr ON a.id_perusahaan = mpr.id_perusahaan
        LEFT JOIN tbl_master_pekerjaan mpk ON a.id_pekerjaan = mpk.id_pekerjaan
        LEFT JOIN tbl_master_peralatan mpl ON a.id_peralatan = mpl.id_peralatan
        WHERE a.id_alat = %s
    """
    riwayat_rows = []
    with db_cursor() as cursor:
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        if data:
            # RIWAYAT RESERTIFIKASI (dari tbl_riwayat_sertifikasi) -- pakai koneksi yang sama
            cursor.execute("""
                SELECT * FROM tbl_riwayat_sertifikasi 
                WHERE id_alat = %s 
                ORDER BY dicatat_pada DESC
            """, (id,))
            riwayat_rows = cursor.fetchall()

    if not data:
        flash('Data tidak ditemukan', 'danger')
        return redirect(url_for('alat.data_master'))

    # DOKUMEN LOGIC
    data['dokumen'] = []
    if data.get('foto'):
        data['dokumen'].append({
            'nama_dokumen': 'Dokumen Utama',
            'filename': data['foto'],
            'url': get_url(data['foto']),
            'tgl_upload': str(data['tgl_sertifikasi']),
            'id': id
        })

    data['riwayat'] = []
    for r in riwayat_rows:
        data['riwayat'].append({
            'tanggal': str(r['dicatat_pada']),
            'aktivitas': f"Resertifikasi ulang — sertifikasi lama ({r['tgl_sertifikasi_lama']} s/d {r['tgl_expired_lama']}) diarsipkan",
            'user': r['dicatat_oleh'],
            'dokumen_lama': r['dokumen_lama'],
            'dokumen_lama_url': get_url(r['dokumen_lama']) if r['dokumen_lama'] else None
        })

    return render_template('detail.html', aset=data, active_page='master')


@alat_bp.route('/upload_dokumen/<int:id>', methods=['POST'])
@login_required
@admin_required(redirect_to='alat.detail_alat', with_args=True)
def upload_dokumen(id):

    file = request.files.get('file_dokumen')

    if file and file.filename != '':
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT rfid_uid FROM tbl_alat WHERE id_alat = %s", (id,))
                res = cursor.fetchone()

            if res:
                # Upload ke R2 bisa lama -> dikerjakan di luar blok `with` supaya koneksi DB tidak ditahan.
                key = build_dokumen_key(res['rfid_uid'], file.filename)
                ok, pesan = upload_file(file, key, content_type=file.mimetype)

                if not ok:
                    flash(f"Gagal upload: {pesan}", "error")
                else:
                    with db_cursor(dictionary=False, commit=True) as cursor:
                        cursor.execute("UPDATE tbl_alat SET dokumen_path = %s WHERE id_alat = %s", (key, id))
                    flash("Dokumen berhasil diupload!", "success")
        except Exception as e:
            flash(pesan_aman(e), "error")

    return redirect(url_for('alat.detail_alat', id=id))


@alat_bp.route('/hapus_dokumen/<int:id>', methods=['POST'])
@login_required
@admin_required(redirect_to='alat.detail_alat', with_args=True)
def hapus_dokumen(id):

    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT dokumen_path FROM tbl_alat WHERE id_alat = %s", (id,))
            res = cursor.fetchone()
            key = res['dokumen_path'] if res else None
            cursor.execute("UPDATE tbl_alat SET dokumen_path = NULL WHERE id_alat = %s", (id,))

        if key:
            delete_file(key)  # gagal hapus file fisik tidak menggagalkan penghapusan record

        flash("Dokumen berhasil dihapus.", "success")
    except Exception as e:
        flash(pesan_aman(e), "error")

    return redirect(url_for('alat.detail_alat', id=id))