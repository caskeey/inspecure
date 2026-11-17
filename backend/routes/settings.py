"""Halaman Pengaturan: profil sendiri, ganti password, dan manajemen user (khusus Admin)."""
from flask import Blueprint, render_template, session, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import db_cursor, DatabaseUnavailable
from auth_utils import login_required, admin_required
from error_utils import pesan_aman

settings_bp = Blueprint('settings', __name__)

# =========================================================
# SETTINGS & USER MANAGEMENT
# =========================================================

@settings_bp.route('/settings', methods=['GET'])
@login_required
def index():
    with db_cursor() as cursor:
        # Ambil Data Diri
        cursor.execute("SELECT * FROM tbl_users WHERE username = %s", (session['user'],))
        user_data = cursor.fetchone()

        # Ambil Semua User (Khusus Admin)
        all_users = []
        if session.get('role') == 'Admin':
            cursor.execute("SELECT * FROM tbl_users ORDER BY role ASC, username ASC")
            all_users = cursor.fetchall()

    # all_users hanya terisi untuk Admin (untuk tabel kelola user).
    return render_template('settings.html', 
                           active_page='settings', 
                           user=session['user'],
                           user_data=user_data, 
                           all_users=all_users)

@settings_bp.route('/settings/update_profile', methods=['POST'])
@admin_required(json=True)
def update_profile():
    data, err = _cek_data_user(request.form)
    if err: return jsonify({'status': 'error', 'msg': err})
    try:
        with db_cursor(commit=True) as cursor:
            err = _sudah_dipakai(cursor, data['username'], data['email_user'], session.get('uid'))
            if err:
                return jsonify({'status': 'error', 'msg': err})
            cursor.execute("UPDATE tbl_users SET nama_lengkap=%s, email_user=%s, username=%s WHERE username=%s", 
                           (data['nama_lengkap'], data['email_user'], data['username'], session['user']))
        session['user'] = data['username'] # Update session jika username ganti
        return jsonify({'status':'success'})
    except Exception as e: return jsonify({'status':'error', 'msg': pesan_aman(e)})

@settings_bp.route('/settings/change_password', methods=['POST'])
@login_required(json=True)
def change_password():

    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    if len(new_password) < 8:
        return jsonify({'status': 'error', 'msg': 'Password baru minimal 8 karakter.'})

    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("SELECT password FROM tbl_users WHERE username=%s", (session['user'],))
            user = cursor.fetchone()

            if not (user and check_password_hash(user['password'], old_password)):
                return jsonify({'status': 'error', 'msg': 'Password lama salah'})
            cursor.execute("UPDATE tbl_users SET password=%s WHERE username=%s",
                           (generate_password_hash(new_password), session['user']))
        return jsonify({'status': 'success'})
    except DatabaseUnavailable:
        return jsonify({'status': 'error', 'msg': 'Koneksi database gagal. Coba lagi nanti.'})

from .settings_users import _cek_data_user, _sudah_dipakai  # noqa: E402,F401
