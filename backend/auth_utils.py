"""Decorator akses terpusat: @login_required dan @admin_required.

Urutan pemakaian (route paling luar, lalu login, lalu admin):

    @bp.route('/tambah_alat')
    @login_required
    @admin_required
    def tambah_alat(): ...

Endpoint API yang membalas JSON:

    @login_required(json=True)
    @admin_required(json=True)

Halaman HTML yang butuh redirect khusus saat bukan Admin:

    @admin_required(redirect_to='main.dashboard')
    @admin_required(redirect_to='alat.detail_alat', with_args=True)  # teruskan view_args (mis. id)
"""
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for

LOGIN_ENDPOINT = 'auth.login'
ROLE_ADMIN = 'Admin'
DEFAULT_ADMIN_REDIRECT = 'alat.data_master'

MSG_LOGIN_JSON = 'Sesi habis. Silakan login kembali.'
MSG_ADMIN = 'Akses ditolak! Fitur ini khusus Admin.'


def _decorator(check):
    """Bikin decorator yang bisa dipakai polos (@x) maupun dengan argumen (@x(json=True))."""
    def factory(func=None, **opts):
        def decorate(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                denied = check(opts)
                if denied is not None:
                    return denied
                return f(*args, **kwargs)
            return wrapper
        return decorate(func) if callable(func) else decorate
    return factory


def _check_login(opts):
    if 'user' in session:
        return None
    if opts.get('json'):
        return jsonify({'status': 'error', 'msg': MSG_LOGIN_JSON}), 401
    return redirect(url_for(LOGIN_ENDPOINT))


def _check_admin(opts):
    if 'user' not in session:  # aman dipakai sendirian tanpa @login_required
        return _check_login(opts)
    if session.get('role') == ROLE_ADMIN:
        return None
    if opts.get('json'):
        return jsonify({'status': 'error', 'msg': MSG_ADMIN}), 403
    flash(MSG_ADMIN, 'error')
    target = opts.get('redirect_to', DEFAULT_ADMIN_REDIRECT)
    args = (request.view_args or {}) if opts.get('with_args') else {}
    return redirect(url_for(target, **args))


login_required = _decorator(_check_login)
admin_required = _decorator(_check_admin)