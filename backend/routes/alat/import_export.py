import os
import uuid
from datetime import date, datetime

import mysql.connector
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, send_from_directory

from db import db_connection, db_cursor
from auth_utils import login_required, admin_required
from error_utils import pesan_aman, PesanUser
from . import alat_bp
from .helpers import hitung_tgl_expired, hitung_status, get_or_create_perusahaan, get_master_data


KOLOM_IMPORT = ['rfid_uid', 'nomor_serial', 'nama_alat', 'id_pekerjaan', 'id_peralatan', 'nama_perusahaan',
                'email_inspektur', 'tgl_sertifikasi', 'durasi_angka', 'durasi_satuan']
MAKS_PESAN_GAGAL = 5   # berapa baris gagal yang ditampilkan di layar (sisanya cukup dihitung)


@alat_bp.route('/import_excel', methods=['POST'])
@login_required
@admin_required
def import_excel():
    file = request.files.get('file_excel')
    if not file: return redirect(url_for('alat.data_master'))

    try:
        df = pd.read_excel(file)
        df.columns = [str(k).strip().lower() for k in df.columns]
        kurang = [k for k in KOLOM_IMPORT if k not in df.columns]
        if kurang:
            flash("Kolom wajib tidak ada di file: " + ", ".join(kurang) + ". Gunakan template import.", "error")
            return redirect(url_for('alat.data_master'))

        sukses, gagal = 0, []
        with db_connection() as conn:
            cursor = conn.cursor()
            for idx, row in df.iterrows():
                baris = idx + 2  # +1 karena baris 1 adalah judul kolom, +1 karena indeks mulai dari 0
                try:
                    rfid_val = _teks(row['rfid_uid'])
                    nama = _teks(row['nama_alat'])
                    nama_pt = _teks(row['nama_perusahaan'])
                    if not nama:
                        raise PesanUser("nama_alat kosong")
                    if not nama_pt:
                        raise PesanUser("nama_perusahaan kosong")

                    durasi = _angka(row['durasi_angka'], 'durasi_angka')
                    if durasi <= 0:
                        raise PesanUser("durasi_angka harus lebih dari 0")
                    satuan = (_teks(row['durasi_satuan']) or '').capitalize()
                    if satuan not in ('Tahun', 'Bulan'):
                        raise PesanUser("durasi_satuan harus 'Tahun' atau 'Bulan'")
                    tgl_sertif = _tanggal(row['tgl_sertifikasi'])

                    # Rumus yang sama dengan tambah/edit/resertifikasi (helpers.hitung_tgl_expired)
                    tgl_expired = hitung_tgl_expired(tgl_sertif, durasi, satuan)

                    if rfid_val is None or rfid_val.lower() in ('nan', 'kosongkan'):
                        rfid_final = f"PENDING-{uuid.uuid4().hex[:8].upper()}"
                        status = "Belum Aktivasi"          # kartu RFID belum dipasang
                    else:
                        rfid_final = rfid_val
                        status = hitung_status(tgl_expired)

                    pt_id = get_or_create_perusahaan(nama_pt)

                    cursor.execute("""
                        INSERT INTO tbl_alat
                        (rfid_uid, nomor_serial, nama_alat, id_pekerjaan, id_peralatan,
                         id_perusahaan, email_inspektur, tgl_sertifikasi, durasi_angka, durasi_satuan,
                         tgl_expired, status_sertifikasi)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        rfid_final, _teks(row['nomor_serial']), nama,
                        _angka(row['id_pekerjaan'], 'id_pekerjaan'), _angka(row['id_peralatan'], 'id_peralatan'),
                        pt_id, _teks(row['email_inspektur']),
                        tgl_sertif, durasi, satuan, tgl_expired, status
                    ))
                    conn.commit()  # per baris: satu baris gagal tidak membatalkan baris lain
                    sukses += 1
                except Exception as e:
                    conn.rollback()
                    gagal.append(f"baris {baris}: {_pesan_baris(e)}")

        if sukses:
            flash(f"Import {sukses} data sukses.", "success")
        if gagal:
            tampil = "; ".join(gagal[:MAKS_PESAN_GAGAL])
            sisa = len(gagal) - MAKS_PESAN_GAGAL
            flash(f"{len(gagal)} baris gagal diimport. {tampil}" + (f"; dan {sisa} baris lainnya." if sisa > 0 else "."), "error")
        if not sukses and not gagal:
            flash("File Excel kosong, tidak ada data yang diimport.", "error")
    except Exception as e:
        flash(pesan_aman(e), "error")
    return redirect(url_for('alat.data_master'))


@alat_bp.route('/input_ocr')
@login_required
@admin_required(redirect_to='main.dashboard')
def input_ocr():
    pek, per, pt = get_master_data()
    return render_template('input_ocr.html', active_page='input_ocr', pekerjaan=pek, peralatan=per, perusahaan=pt)


@alat_bp.route('/download_template')
@login_required
def download_template():
    data = {
        'rfid_uid': ['E123456'], 'nomor_serial': ['SN-001'], 'nama_alat': ['Helm'],
        'id_pekerjaan': ['1'], 'id_peralatan': ['1'], 'nama_perusahaan': ['PT Test'],
        'email_inspektur': ['a@b.com'], 'tgl_sertifikasi': ['2025-01-01'],
        'durasi_angka': [1], 'durasi_satuan': ['Tahun']
    }
    df = pd.DataFrame(data)
    filename = 'template_import.xlsx'
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    df.to_excel(path, index=False)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@alat_bp.route('/input_cepat_page')
@login_required
@admin_required
def input_cepat_page():
    pek, per, pt = get_master_data()
    return render_template('input_cepat.html', active_page='tambah', pekerjaan=pek, peralatan=per, perusahaan=pt)


@alat_bp.route('/api/simpan_cepat', methods=['POST'])
@login_required(json=True)
@admin_required(json=True)
def api_simpan_cepat():
    try:
        data = request.form

        pt_id = get_or_create_perusahaan(data.get('perusahaan') or data.get('nama_perusahaan'))
        durasi = int(data['durasi_angka'])
        tgl_exp_str = hitung_tgl_expired(data['tgl_sertifikasi'], durasi, data['durasi_satuan'])
        status = hitung_status(tgl_exp_str)

        query = """
            INSERT INTO tbl_alat 
            (rfid_uid, nomor_serial, nama_alat, id_pekerjaan, id_peralatan, 
             id_perusahaan, email_inspektur, tgl_sertifikasi, durasi_angka, durasi_satuan, 
             tgl_expired, status_sertifikasi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with db_cursor(dictionary=False, commit=True) as cursor:
            cursor.execute(query, (
                data['rfid_uid'], data['nomor_serial'], data['nama_alat'],
                data['jenis_pekerjaan'], data['jenis_peralatan_select'], pt_id, data['email_inspektur'],
                data['tgl_sertifikasi'], durasi, data['durasi_satuan'], tgl_exp_str, status
            ))
        return jsonify({"status": "success", "msg": f"OK: {data['nama_alat']}"})
    except Exception as e:
        return jsonify({"status": "error", "msg": pesan_aman(e)})
from .import_helpers import _teks, _angka, _tanggal, _pesan_baris
