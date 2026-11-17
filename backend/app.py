import os
import secrets
import logging
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()  
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('inspecure')

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix
from routes.auth import auth_bp
from routes.dashboard import main_bp
from routes.settings import settings_bp
from routes.alat import alat_bp
from routes.resertifikasi.routes import resertifikasi_bp
from scheduler import init_scheduler
from error_handlers import register_error_handlers

def _load_secret_key():
    """Ambil SECRET_KEY dari .env. Kalau belum ada, buat sekali lalu simpan ke
    backend/.secret_key (di-gitignore) supaya sesi login tidak hilang tiap restart."""
    key = os.environ.get('SECRET_KEY', '').strip()
    if key:
        return key
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret_key')
    try:
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                saved = f.read().strip()
            if saved:
                return saved
        key = secrets.token_hex(32)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(key)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        logger.warning('SECRET_KEY belum diset di .env -> dibuat otomatis di backend/.secret_key. '
                       'Sebaiknya pindahkan ke .env (lihat .env.example).')
        return key
    except OSError:
        logger.warning('SECRET_KEY tidak bisa disimpan ke backend/.secret_key (folder tidak bisa ditulis). '
                       'Memakai kunci acak sementara: semua user akan logout setiap app di-restart. '
                       'Isi SECRET_KEY di .env supaya tetap.')
        return secrets.token_hex(32)

WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(WEB_ROOT, 'templates'),
    static_folder=os.path.join(WEB_ROOT, 'static')
)
app.secret_key = _load_secret_key()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

if os.environ.get('BEHIND_PROXY', 'false').lower() == 'true':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'


if os.environ.get('BEHIND_PROXY', 'false').lower() == 'true' and not app.config['SESSION_COOKIE_SECURE']:
    logger.warning(
        'SESSION_COOKIE_SECURE=false. Setelah HTTPS lewat reverse proxy berjalan, ubah jadi true di .env.')

app.config['WTF_CSRF_TIME_LIMIT'] = None
csrf = CSRFProtect(app)

register_error_handlers(app)

_TIPE_BERISIKO = ('.html', '.htm', '.xhtml', '.shtml', '.svg', '.xml', '.js', '.mjs')

@app.after_request
def amankan_file_upload(resp):
    if request.path.startswith('/static/uploads/'):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        if request.path.lower().endswith(_TIPE_BERISIKO):
            resp.headers['Content-Disposition'] = 'attachment'
    return resp

Compress(app)
_STATIC_TANPA_CACHE = ('uploads/', 'docs/')


@app.url_defaults
def tambah_versi_static(endpoint, values):
    if endpoint != 'static':
        return
    filename = values.get('filename')
    if not filename or filename.startswith(_STATIC_TANPA_CACHE):
        return
    try:
        values['v'] = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
    except OSError:
        pass  


@app.after_request
def cache_static_berversi(resp):
    if (request.endpoint == 'static' and 'v' in request.args and resp.status_code == 200
            and not request.path.startswith(('/static/uploads/', '/static/docs/'))):
        resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp

UPLOAD_FOLDER = os.path.join(WEB_ROOT, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(alat_bp)
app.register_blueprint(resertifikasi_bp)

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    init_scheduler(app)

if __name__ == '__main__':
    app.run(
        debug=os.environ.get('FLASK_DEBUG', '0') == '1',
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
    )

