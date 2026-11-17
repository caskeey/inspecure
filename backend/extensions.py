"""Objek extension Flask yang dipakai bersama (dipisah supaya tidak circular import)."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Batas request per IP. Storage di memori sudah cukup karena gunicorn memakai 1 worker
# (lihat Dockerfile). Kalau suatu hari worker > 1, ganti storage_uri ke Redis.
# Di belakang reverse proxy, IP asli terbaca benar kalau BEHIND_PROXY=true (ProxyFix di app.py).
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")