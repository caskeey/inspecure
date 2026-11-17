"""Pendaftaran akun Petugas."""
import re
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from db import db_cursor, log_activity, DatabaseUnavailable
from extensions import limiter
from .auth import auth_bp

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour", methods=["POST"])  # anti spam akun
def register():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        email = request.form.get('email_user', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        konfirmasi = request.form.get('konfirmasi_password', '')

        # Validasi input
        error = None
        if not nama_lengkap or not email or not username or not password:
            error = "Semua kolom wajib diisi."
        elif not re.fullmatch(r'[A-Za-z0-9_.]{4,30}', username):
            error = "Username 4-30 karakter, hanya huruf, angka, titik, atau underscore."
        elif not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            error = "Format email tidak valid."
        elif len(password) < 8:
            error = "Password minimal 8 karakter."
        elif password != konfirmasi:
            error = "Konfirmasi password tidak sama."

        if error:
            flash(error, "error")
            return render_template('register.html', form=request.form)

        hashed = generate_password_hash(password)  # hash dulu, jangan sambil menahan koneksi DB
        try:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    "SELECT username, email_user FROM tbl_users WHERE username = %s OR email_user = %s",
                    (username, email))
                dup = cursor.fetchone()
                if dup:
                    msg = "Username sudah dipakai." if dup['username'] == username else "Email sudah terdaftar."
                    flash(msg, "error")
                    return render_template('register.html', form=request.form)

                # Role selalu 'Petugas' untuk pendaftaran mandiri. Admin hanya bisa dibuat dari menu Settings.
                cursor.execute(
                    "INSERT INTO tbl_users (username, password, nama_lengkap, role, email_user) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (username, hashed, nama_lengkap, 'Petugas', email))
        except DatabaseUnavailable:
            flash("Koneksi database gagal. Coba lagi nanti.", "error")
            return render_template('register.html', form=request.form)

        log_activity(username, 'REGISTER', 'Akun baru dibuat lewat halaman daftar')
        flash("Akun berhasil dibuat. Silakan masuk.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form={})
