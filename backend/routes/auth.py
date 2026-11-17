import hashlib
import hmac
from html import escape
import logging
import smtplib
from email.message import EmailMessage

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import config
from db import db_cursor, log_activity, DatabaseUnavailable
from extensions import limiter

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)
RESET_TOKEN_MAX_AGE = 30 * 60


def _reset_serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='inspecure-password-reset-v1')


def _password_fingerprint(password_hash):
    return hmac.new(str(current_app.secret_key).encode(), password_hash.encode(), hashlib.sha256).hexdigest()


def _kirim_email_reset(email, nama, link):
    if not config.SMTP_USER or not config.SMTP_PASS:
        raise RuntimeError('SMTP_USER/SMTP_PASS belum dikonfigurasi')
    pesan = EmailMessage()
    pesan['Subject'] = 'Permintaan Reset Password INSPECURE'
    pesan['From'] = f'{config.EMAIL_SENDER_NAME} <{config.EMAIL_FROM}>'
    pesan['To'] = email
    pesan.set_content(
        f'Halo {nama or "Pengguna INSPECURE"},\n\n'
        f'Kami menerima permintaan untuk mengatur ulang password akun Anda. '
        f'Buka tautan berikut dalam 30 menit:\n{link}\n\n'
        'Jika Anda tidak meminta reset password, abaikan email ini.'
    )
    nama_html = escape(nama or 'Pengguna INSPECURE')
    link_html = escape(link, quote=True)
    pesan.add_alternative(
        f'<p>Halo {nama_html},</p>'
        '<p>Kami menerima permintaan untuk mengatur ulang password akun Anda.</p>'
        f'<p><a href="{link_html}" style="display:inline-block;padding:10px 16px;'
        'background:#2f2f2f;color:#ffffff;text-decoration:none;border-radius:6px;">'
        'Atur Ulang Password</a></p>'
        '<p>Tautan berlaku selama 30 menit. Jika tombol tidak bisa diklik, salin alamat ini ke browser:</p>'
        f'<p><a href="{link_html}">{link_html}</a></p>'
        '<p>Jika Anda tidak meminta reset password, abaikan email ini.</p>',
        subtype='html'
    )
    if config.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(pesan)
    else:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(pesan)

@auth_bp.route('/')
def landing():
    return render_template('landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 30 per hour", methods=["POST"])  # anti brute-force, hanya POST
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Cek User di Database
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT * FROM tbl_users WHERE username = %s", (username,))
                user = cursor.fetchone()
        except DatabaseUnavailable:
            flash("Koneksi database gagal. Coba lagi nanti.", "error")
            return redirect(url_for('auth.login'))
        
        # Validasi Password: dibandingkan pakai hash (werkzeug), bukan plain text lagi.
        if user and check_password_hash(user['password'], password):
            # Cookie sesi persisten 30 hari hanya jika pengguna memilih "Ingat Saya".
            session.clear()
            session.permanent = request.form.get('remember') == 'on'
            session['user'] = user['username']
            session['role'] = user['role']
            session['uid'] = user['id_users'] 
            
            log_activity(user['username'], 'LOGIN', 'Login berhasil ke sistem')
            return redirect(url_for('main.dashboard'))
        else:
            flash("Login Gagal! Cek username/password.", "error")
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('3 per hour', methods=['POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    'SELECT id_users, email_user, nama_lengkap, password FROM tbl_users '
                    'WHERE LOWER(email_user) = %s LIMIT 1', (email,))
                user = cursor.fetchone() if email else None
        except DatabaseUnavailable:
            flash('Layanan sedang bermasalah. Coba lagi beberapa saat lagi.', 'error')
            return render_template('forgot_password.html', email=email), 503

        if user and user.get('email_user'):
            token = _reset_serializer().dumps({
                'uid': user['id_users'],
                'fp': _password_fingerprint(user['password'])
            })
            base_url = config.PASSWORD_RESET_URL_BASE
            link = (f'{base_url}{url_for("auth.reset_password", token=token)}' if base_url else
                    url_for('auth.reset_password', token=token, _external=True))
            try:
                _kirim_email_reset(user['email_user'], user.get('nama_lengkap'), link)
            except Exception:
                logger.exception('Gagal mengirim email reset password')

        flash('Jika email tersebut terdaftar, instruksi reset password akan dikirim. Periksa inbox dan folder spam.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit('10 per hour', methods=['POST'])
def reset_password(token):
    try:
        payload = _reset_serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
        user_id = int(payload['uid'])
        fingerprint = payload['fp']
    except SignatureExpired:
        flash('Tautan reset sudah kedaluwarsa. Silakan minta tautan baru.', 'error')
        return redirect(url_for('auth.forgot_password'))
    except (BadSignature, KeyError, TypeError, ValueError):
        flash('Tautan reset tidak valid. Silakan minta tautan baru.', 'error')
        return redirect(url_for('auth.forgot_password'))

    try:
        with db_cursor() as cursor:
            cursor.execute('SELECT id_users, password FROM tbl_users WHERE id_users = %s', (user_id,))
            user = cursor.fetchone()
    except DatabaseUnavailable:
        flash('Layanan sedang bermasalah. Coba lagi beberapa saat lagi.', 'error')
        return render_template('reset_password.html', token=token), 503

    if not user or not hmac.compare_digest(fingerprint, _password_fingerprint(user['password'])):
        flash('Tautan reset sudah digunakan atau tidak valid. Silakan minta tautan baru.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirmation = request.form.get('confirm_password', '')
        if len(password) < 8:
            flash('Password baru minimal 8 karakter.', 'error')
        elif password != confirmation:
            flash('Konfirmasi password tidak sama.', 'error')
        else:
            try:
                new_hash = generate_password_hash(password)
                with db_cursor(commit=True) as cursor:
                    cursor.execute('UPDATE tbl_users SET password = %s WHERE id_users = %s AND password = %s',
                                   (new_hash, user_id, user['password']))
                    updated = cursor.rowcount == 1
                if updated:
                    flash('Password berhasil diperbarui. Silakan masuk dengan password baru.', 'success')
                    return redirect(url_for('auth.login'))
                flash('Tautan reset sudah digunakan. Silakan minta tautan baru.', 'error')
            except DatabaseUnavailable:
                flash('Layanan sedang bermasalah. Coba lagi beberapa saat lagi.', 'error')
    return render_template('reset_password.html', token=token)

@auth_bp.route('/logout')
def logout():
    if 'user' in session:
        log_activity(session['user'], 'LOGOUT', 'Logout dari sistem')
    session.clear()
    return redirect(url_for('auth.landing'))

from . import auth_registration  # noqa: E402,F401 - daftarkan route register