"""Email pengingat pratinjau dan ringkasan hasil rekap otomatis."""
import logging
import smtplib
from html import escape
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)

def _kirim_ringkasan_otomatis_ke_admin(hasil):
    """Kirim status per perusahaan ke akun Admin setelah scheduler selesai."""
    from db import db_cursor

    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT email_user FROM tbl_users WHERE role = 'Admin' AND email_user IS NOT NULL")
            admin_emails = list(dict.fromkeys(
                row['email_user'].strip() for row in cursor.fetchall()
                if row.get('email_user') and row['email_user'].strip()
            ))
        if not admin_emails or not config.SMTP_USER or not config.SMTP_PASS:
            logger.warning("Ringkasan email otomatis tidak terkirim: email Admin atau SMTP belum dikonfigurasi.")
            return

        rows_html = []
        rows_text = []
        for item in hasil:
            status = 'TERKIRIM' if item.get('terkirim') else 'GAGAL'
            detail = item.get('pesan') or '-'
            nama = item.get('nama_perusahaan') or '-'
            count = item.get('jumlah_alat', 0)
            rows_html.append(
                f'<tr><td style="padding:8px;border:1px solid #ddd">{escape(str(nama))}</td>'
                f'<td style="padding:8px;border:1px solid #ddd">{count}</td>'
                f'<td style="padding:8px;border:1px solid #ddd"><b>{status}</b><br>{escape(str(detail))}</td></tr>'
            )
            rows_text.append(f"- {nama} ({count} alat): {status} — {detail}")

        sukses = sum(1 for item in hasil if item.get('terkirim'))
        gagal = len(hasil) - sukses
        subject = f"Hasil pengiriman rekap otomatis INSPECURE: {sukses} terkirim, {gagal} gagal"
        plain = "Pengiriman rekap otomatis selesai.\n\n" + "\n".join(rows_text)
        html_body = (
            '<div style="font:14px/1.5 Arial,sans-serif;color:#1f2937">'
            '<h2>Hasil pengiriman rekap otomatis</h2>'
            f'<p>Selesai: <b>{sukses} terkirim</b>, <b>{gagal} gagal</b>.</p>'
            '<table style="border-collapse:collapse"><thead><tr>'
            '<th style="padding:8px;border:1px solid #ddd">Perusahaan</th>'
            '<th style="padding:8px;border:1px solid #ddd">Jumlah alat</th>'
            '<th style="padding:8px;border:1px solid #ddd">Status dan detail</th>'
            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
        )
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config.EMAIL_SENDER_NAME} <{config.EMAIL_FROM}>"
        msg['To'] = ', '.join(admin_emails)
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
            if config.SMTP_USE_TLS:
                server.starttls()
        try:
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.EMAIL_FROM, admin_emails, msg.as_string())
        finally:
            server.quit()
        logger.info("Ringkasan pengiriman otomatis dikirim ke %d akun Admin.", len(admin_emails))
    except Exception:
        logger.exception("Ringkasan hasil pengiriman otomatis gagal dikirim ke Admin")


def _job_pengingat_pratinjau():
    """Email Admin tiga hari sebelum rekap otomatis, berisi tautan pratinjau."""
    from db import db_cursor
    from routes.resertifikasi.data import get_rekap_data

    try:
        grouped = get_rekap_data(hanya_belum_terkirim=True)
        if not grouped:
            logger.info("Pengingat pratinjau dilewati: tidak ada rekap otomatis yang menunggu.")
            return

        with db_cursor() as cursor:
            cursor.execute("SELECT email_user FROM tbl_users WHERE role = 'Admin' AND email_user IS NOT NULL")
            admin_emails = list(dict.fromkeys(
                row['email_user'].strip() for row in cursor.fetchall()
                if row.get('email_user') and row['email_user'].strip()
            ))
        if not admin_emails:
            logger.warning("Pengingat pratinjau tidak terkirim: akun Admin belum memiliki email.")
            return
        if not config.SMTP_USER or not config.SMTP_PASS:
            logger.warning("Pengingat pratinjau tidak terkirim: SMTP_USER/SMTP_PASS belum dikonfigurasi.")
            return

        company_rows = []
        text_rows = []
        for company_id, company in grouped.items():
            name = company['nama_perusahaan']
            count = len(company['alat'])
            path = f"/resertifikasi/preview-otomatis/{company_id}"
            href = f"{config.APP_PUBLIC_URL}{path}" if config.APP_PUBLIC_URL else ''
            if href:
                company_rows.append(f'<li><a href="{escape(href, quote=True)}">{escape(name)}</a> — {count} alat</li>')
                text_rows.append(f"- {name}: {count} alat — {href}")
            else:
                company_rows.append(f'<li>{escape(name)} — {count} alat</li>')
                text_rows.append(f"- {name}: {count} alat")

        subject = "Tinjau pratinjau rekap resertifikasi otomatis INSPECURE"
        plain = (
            f"Rekap otomatis akan dikirim pada tanggal {config.REKAP_HARI} pukul "
            f"{config.REKAP_JAM:02d}:{config.REKAP_MENIT:02d} WIB. Periksa pratinjau email dan PDF "
            "di INSPECURE > Rekap Resertifikasi sebelum jadwal tersebut.\n\n"
            + "\n".join(text_rows)
        )
        html_body = (
            '<div style="font:14px/1.6 Arial,sans-serif;color:#1f2937">'
            '<h2>Tinjau rekap resertifikasi otomatis</h2>'
            f'<p>Rekap akan dikirim pada tanggal <b>{config.REKAP_HARI}</b> pukul '
            f'<b>{config.REKAP_JAM:02d}:{config.REKAP_MENIT:02d} WIB</b>.</p>'
            '<p>Buka pratinjau email dan lampiran PDF dari menu <b>Resertifikasi → Rekap</b>. '
            'Periksa data dan alamat penerima sebelum jadwal kirim.</p>'
            f'<ul>{"".join(company_rows)}</ul></div>'
        )
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config.EMAIL_SENDER_NAME} <{config.EMAIL_FROM}>"
        msg['To'] = ', '.join(admin_emails)
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
            if config.SMTP_USE_TLS:
                server.starttls()
        try:
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.EMAIL_FROM, admin_emails, msg.as_string())
        finally:
            server.quit()
        logger.info("Pengingat pratinjau rekap dikirim ke %d akun Admin.", len(admin_emails))
    except Exception:
        logger.exception("Pengingat pratinjau rekap otomatis gagal dikirim")
