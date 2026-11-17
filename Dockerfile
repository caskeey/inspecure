FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Jakarta

WORKDIR /app

# Install mysql-client untuk backup database otomatis (mysqldump)
RUN apt-get update && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Cek tiap 30 detik apakah web masih merespons (status terlihat di Container Manager)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login', timeout=4)" || exit 1

# workers=1 SENGAJA: scheduler rekap otomatis (APScheduler) hidup di dalam proses app,
# kalau worker > 1 email rekap terkirim dobel. Konkurensi diatur lewat --threads.
# timeout 120: export Excel / generate PDF bisa lebih lama dari default 30 detik.
CMD ["gunicorn", "--chdir", "backend", "app:app", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-"]