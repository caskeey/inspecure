"""Pendaftaran halaman error dan respons API yang aman."""
from flask import request, redirect, url_for, jsonify, flash, render_template
from flask_wtf.csrf import CSRFError
from db import DatabaseUnavailable
from extensions import limiter


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.headers.get('X-CSRFToken'):  # request dari fetch/AJAX -> balas JSON
            return jsonify({'status': 'error', 'msg': 'Sesi keamanan habis. Muat ulang halaman lalu coba lagi.'}), 400
        flash('Sesi keamanan habis. Silakan ulangi aksi Anda.', 'error')
        return redirect(request.referrer or url_for('auth.login'))

    # Rate limit (batas percobaan per IP). Aturan per route ada di routes/auth.py.
    limiter.init_app(app)

    @app.errorhandler(DatabaseUnavailable)
    def handle_database_unavailable(e):
        """Database mati / pool habis: balas 503 yang rapi, bukan halaman error 500 mentah."""
        pesan = 'Koneksi database sedang bermasalah. Coba lagi beberapa saat lagi.'
        if request.headers.get('X-CSRFToken') or request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'msg': pesan}), 503
        return render_template('error.html',
                               code=503,
                               title='Layanan Sementara Tidak Tersedia',
                               message=pesan), 503


    @app.errorhandler(429)
    def handle_too_many_requests(e):
        pesan = 'Terlalu banyak percobaan. Tunggu beberapa menit lalu coba lagi.'
        if request.path in ('/login', '/register'):
            flash(pesan, 'error')
            return redirect(request.path)
        return jsonify({'status': 'error', 'msg': pesan}), 429


    @app.errorhandler(404)
    def handle_not_found(e):
        if request.headers.get('X-CSRFToken') or request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'msg': 'Halaman tidak ditemukan.'}), 404
        return render_template('error.html',
                               code=404,
                               title='Halaman Tidak Ditemukan',
                               message='Halaman yang Anda cari tidak ada atau sudah dipindahkan. '
                                       'Periksa kembali alamat URL-nya.'), 404


    @app.errorhandler(500)
    def handle_internal_error(e):
        if request.headers.get('X-CSRFToken') or request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'msg': 'Terjadi kesalahan pada server.'}), 500
        return render_template('error.html',
                               code=500,
                               title='Kesalahan Server',
                               message='Terjadi kesalahan internal pada server. '
                                       'Tim teknis sudah diberitahu. Silakan coba lagi nanti.'), 500
