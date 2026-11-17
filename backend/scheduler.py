"""
Scheduler otomatis untuk fitur Rekap Resertifikasi.

Tiap bulan (default: tanggal 28 jam 10:00 WIB, diatur di config.py) job ini memanggil
jalankan_rekap_resertifikasi(), yang:
  1. mengambil alat yang akan memasuki masa resertifikasi,
  2. mengelompokkannya per perusahaan,
  3. membuat rekap PDF per perusahaan, lalu
  4. mengirimkannya lewat email.
Kalau tidak ada alat yang perlu diproses, job selesai tanpa mengirim apa pun.

Memakai CronTrigger (jalan tepat di waktu yang ditentukan), bukan loop yang terus-menerus
mengecek tanggal, supaya tidak boros resource.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from scheduler_notifications import (
    _job_pengingat_pratinjau, _kirim_ringkasan_otomatis_ke_admin,
)

logger = logging.getLogger(__name__)
_scheduler = None


def _job_bulanan():
    # Import di dalam fungsi supaya menghindari circular import saat app start
    from routes.resertifikasi import jalankan_rekap_resertifikasi
    logger.info("Menjalankan rekap resertifikasi otomatis (tanggal %s jam %02d:%02d)...",
                config.REKAP_HARI, config.REKAP_JAM, config.REKAP_MENIT)
    try:
        hasil = jalankan_rekap_resertifikasi(kirim_email=True, username_trigger='scheduler',
                                             hanya_belum_terkirim=True)
    except Exception:
        # Job berjalan di thread latar belakang tanpa ada yang melihat layar -> wajib masuk log.
        logger.exception("Rekap resertifikasi otomatis GAGAL")
        return
    logger.info("Selesai. %d perusahaan diproses.", len(hasil))
    if hasil:
        _kirim_ringkasan_otomatis_ke_admin(hasil)


def _job_backup_harian():
    """Job harian: backup database via mysqldump."""
    from backup import jalankan_backup, bersihkan_backup_lama
    try:
        ok, pesan = jalankan_backup()
        if ok:
            logger.info("Backup database berhasil: %s", pesan)
        else:
            logger.error("Backup database GAGAL: %s", pesan)
    except Exception:
        logger.exception("Backup database GAGAL")
    
    # Bersihkan backup lama
    try:
        bersihkan_backup_lama()
    except Exception:
        logger.exception("Gagal membersihkan backup lama")


def init_scheduler(app):
    """Panggil sekali saat Flask app start (lihat app.py)."""
    global _scheduler
    if not config.SCHEDULER_ENABLED:
        logger.info("SCHEDULER_ENABLED=false, scheduler otomatis tidak diaktifkan.")
        return None

    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Jakarta")
    hari_pengingat = max(1, config.REKAP_HARI - 3)
    _scheduler.add_job(
        _job_pengingat_pratinjau,
        trigger=CronTrigger(day=hari_pengingat, hour=config.REKAP_JAM, minute=config.REKAP_MENIT),
        id='pengingat_pratinjau_rekap',
        replace_existing=True
    )
    _scheduler.add_job(
        _job_bulanan,
        trigger=CronTrigger(day=config.REKAP_HARI, hour=config.REKAP_JAM, minute=config.REKAP_MENIT),
        id='rekap_resertifikasi_bulanan',
        replace_existing=True
    )
    if config.BACKUP_ENABLED:
        _scheduler.add_job(
            _job_backup_harian,
            trigger=CronTrigger(hour=config.BACKUP_JAM, minute=config.BACKUP_MENIT),
            id='backup_database_harian',
            replace_existing=True
        )
        logger.info("Backup database otomatis akan jalan tiap hari jam %02d:%02d WIB.",
                    config.BACKUP_JAM, config.BACKUP_MENIT)
    _scheduler.start()
    logger.info("Aktif. Rekap resertifikasi otomatis akan jalan tiap tanggal %s jam %02d:%02d WIB.",
                config.REKAP_HARI, config.REKAP_JAM, config.REKAP_MENIT)
    logger.info("Pengingat pratinjau rekap akan jalan tiap tanggal %s jam %02d:%02d WIB.",
                hari_pengingat, config.REKAP_JAM, config.REKAP_MENIT)
    return _scheduler
