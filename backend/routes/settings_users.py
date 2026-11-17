"""Endpoint manajemen akun (khusus Admin) dan validasinya."""
import re
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
from db import db_cursor
from auth_utils import admin_required
from error_utils import pesan_aman
from .settings import settings_bp

# ---------------------------------------------------------------
# Validasi data user (dipakai create_user, update_user_data, update_profile, reset_user_pass)
# Aturannya disamakan dengan halaman register (routes/auth.py).
# ---------------------------------------------------------------
ROLE_VALID = ('Admin', 'Petugas')
MIN_PASSWORD = 8


def _cek_password(password):
    if len(password or '') < MIN_PASSWORD:
        return f'Password minimal {MIN_PASSWORD} karakter.'
    return None


def _cek_data_user(form, cek_username=True, cek_role=False):
    """Validasi nama, email, username (opsional), role (opsional).
    Return (data_bersih, pesan_error). pesan_error None kalau semua valid."""
    nama = form.get('nama_lengkap', '').strip()
    email = form.get('email_user', '').strip().lower()
    username = form.get('username', '').strip()
    role = form.get('role', '').strip()

    if not nama or not email or not username:
        return None, 'Nama, email, dan username wajib diisi.'
    if len(nama) > 100:
        return None, 'Nama maksimal 100 karakter.'
    if len(email) > 100 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return None, 'Format email tidak valid.'
    if cek_username and not re.fullmatch(r'[A-Za-z0-9_.]{4,30}', username):
        return None, 'Username 4-30 karakter, hanya huruf, angka, titik, atau underscore.'
    if cek_role and role not in ROLE_VALID:
        return None, 'Role tidak valid.'
    return {'nama_lengkap': nama, 'email_user': email, 'username': username, 'role': role}, None


def _sudah_dipakai(cursor, username, email, abaikan_id=None):
    """Cek username/email sudah dipakai user lain. Return pesan error atau None."""
    cursor.execute("SELECT id_users, username, email_user FROM tbl_users "
                   "WHERE username = %s OR email_user = %s", (username, email))
    for row in cursor.fetchall():
        if abaikan_id is not None and row['id_users'] == abaikan_id:
            continue
        return 'Username sudah dipakai.' if row['username'] == username else 'Email sudah terdaftar.'
    return None



def _ada_admin_lain(cursor, user_id):
    """True kalau selain user_id masih ada akun Admin lain (supaya Admin terakhir tidak hilang)."""
    cursor.execute("SELECT COUNT(*) AS n FROM tbl_users WHERE role='Admin' AND id_users <> %s", (user_id,))
    return cursor.fetchone()['n'] > 0


@settings_bp.route('/settings/create_user', methods=['POST'])
@admin_required(json=True)
def create_user():
    data, err = _cek_data_user(request.form, cek_role=True)
    if not err: err = _cek_password(request.form.get('password', ''))
    if err: return jsonify({'status': 'error', 'msg': err})
    try:
        hashed = generate_password_hash(request.form['password'])
        with db_cursor(commit=True) as cursor:
            err = _sudah_dipakai(cursor, data['username'], data['email_user'])
            if err:
                return jsonify({'status': 'error', 'msg': err})
            cursor.execute("INSERT INTO tbl_users (username, password, nama_lengkap, role, email_user) VALUES (%s, %s, %s, %s, %s)", 
                           (data['username'], hashed, data['nama_lengkap'], data['role'], data['email_user']))
        return jsonify({'status':'success'})
    except Exception as e: return jsonify({'status':'error', 'msg': pesan_aman(e)})

@settings_bp.route('/settings/update_user_data', methods=['POST'])
@admin_required(json=True)
def update_user_data():
    try:
        user_id = int(request.form.get('user_id', ''))
    except ValueError:
        return jsonify({'status': 'error', 'msg': 'User tidak valid.'})
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT username, role FROM tbl_users WHERE id_users=%s", (user_id,))
            lama = cursor.fetchone()
            if not lama:
                return jsonify({'status': 'error', 'msg': 'User tidak ditemukan.'})
            # Username lama yang formatnya tidak standar (mis. ada spasi) tetap boleh dipertahankan;
            # aturan format hanya dipaksakan kalau username-nya diganti.
            ganti_username = request.form.get('username', '').strip() != lama['username']
            data, err = _cek_data_user(request.form, cek_username=ganti_username, cek_role=True)
            if not err: err = _sudah_dipakai(cursor, data['username'], data['email_user'], user_id)
            if not err and lama['role'] == 'Admin' and data['role'] != 'Admin':
                if user_id == session.get('uid'):
                    err = 'Tidak bisa menurunkan role akun sendiri.'
                elif not _ada_admin_lain(cursor, user_id):
                    err = 'Tidak bisa menurunkan role Admin terakhir.'
            if err:
                return jsonify({'status': 'error', 'msg': err})
            cursor.execute("UPDATE tbl_users SET nama_lengkap=%s, email_user=%s, username=%s, role=%s WHERE id_users=%s", 
                           (data['nama_lengkap'], data['email_user'], data['username'], data['role'], user_id))
        return jsonify({'status':'success'})
    except Exception as e: return jsonify({'status':'error', 'msg': pesan_aman(e)})

@settings_bp.route('/settings/delete_user', methods=['POST'])
@admin_required(json=True)
def delete_user():
    try:
        user_id = int(request.form.get('user_id', ''))
    except ValueError:
        return jsonify({'status': 'error', 'msg': 'User tidak valid.'})
    if user_id == session.get('uid'):
        return jsonify({'status': 'error', 'msg': 'Tidak bisa menghapus akun sendiri.'})
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT role FROM tbl_users WHERE id_users=%s", (user_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'status': 'error', 'msg': 'User tidak ditemukan.'})
            if target['role'] == 'Admin' and not _ada_admin_lain(cursor, user_id):
                return jsonify({'status': 'error', 'msg': 'Tidak bisa menghapus Admin terakhir.'})
            cursor.execute("DELETE FROM tbl_users WHERE id_users=%s", (user_id,))
        return jsonify({'status':'success'})
    except Exception as e: return jsonify({'status':'error', 'msg': pesan_aman(e)})

@settings_bp.route('/settings/reset_user_pass', methods=['POST'])
@admin_required(json=True)
def reset_user_pass():
    err = _cek_password(request.form.get('new_password', ''))
    if err: return jsonify({'status': 'error', 'msg': err})
    try:
        hashed = generate_password_hash(request.form['new_password'])
        with db_cursor(dictionary=False, commit=True) as cursor:
            cursor.execute("UPDATE tbl_users SET password=%s WHERE id_users=%s", (hashed, request.form['user_id']))
        return jsonify({'status':'success'})
    except Exception as e: return jsonify({'status':'error', 'msg': pesan_aman(e)})
