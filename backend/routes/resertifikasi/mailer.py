import os
import logging
import smtplib
from html import escape
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

import config
from .constants import LOGO_DANANTARA_PATH, LOGO_IDSURVEY_PATH, LOGO_SUCOFINDO_PATH, BULAN_ID
from storage_r2 import upload_local_file


# =========================================================
# 3. KIRIM EMAIL REKAP (format & header sama seperti contoh email)
#    -> "Kirim email ke perusahaan"
# =========================================================
def build_email_rekap_content(nama_perusahaan, bulan_label=None, tahun_label=None):
    """Buat subjek dan isi yang dipakai bersama oleh email dan halaman pratinjau."""
    if bulan_label is None:
        bulan_label = BULAN_ID[datetime.now().month]
    if tahun_label is None:
        tahun_label = datetime.now().year

    nama_aman = escape(str(nama_perusahaan or ''))
    subject = f"Rekapitulasi Resertifikasi Peralatan - {nama_perusahaan} ({bulan_label} {tahun_label})"
    html_body = f"""
    <html>
    <body style="font-family: Arial, Helvetica, sans-serif; color:#1F2937; font-size:14px; line-height:1.6;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%; table-layout:fixed; margin:0 0 22px;">
            <tr>
                <td width="33.33%" align="left" valign="middle" style="width:33.33%; height:58px; text-align:left; vertical-align:middle;">
                    <img src="cid:logo_danantara" alt="Danantara Indonesia" height="42" style="display:inline-block; height:42px; width:auto; max-width:100%; border:0;">
                </td>
                <td width="33.33%" align="center" valign="middle" style="width:33.33%; height:58px; text-align:center; vertical-align:middle;">
                    <img src="cid:logo_idsurvey" alt="IDSurvey" height="42" style="display:inline-block; height:42px; width:auto; max-width:100%; border:0;">
                </td>
                <td width="33.33%" align="right" valign="middle" style="width:33.33%; height:58px; text-align:right; vertical-align:middle;">
                    <img src="cid:logo_sucofindo" alt="Sucofindo" height="42" style="display:inline-block; height:42px; width:auto; max-width:100%; border:0;">
                </td>
            </tr>
        </table>
        <p>Yth. Pimpinan <b>{nama_aman}</b>,</p>
        <p>Dengan hormat,</p>
        <p>Bersama dengan email ini, kami sampaikan rekapitulasi peralatan milik perusahaan Bapak/Ibu
        yang akan memasuki masa resertifikasi pada bulan <b>{escape(str(bulan_label))} {tahun_label}</b>.</p>
        <p>Mohon agar dapat dilakukan penjadwalan ulang untuk proses resertifikasi sesuai ketentuan yang berlaku.</p>
        <p>Rincian peralatan terlampir dalam dokumen PDF pada email ini.</p>
        <p>Demikian kami sampaikan. Atas perhatian dan kerja sama yang baik, kami ucapkan terima kasih.</p>
        <p>Hormat kami,<br><b>PT SUCOFINDO (Persero)</b></p>
    </body>
    </html>
    """
    text_body = (
        f"Yth. Pimpinan {nama_perusahaan},\n\n"
        "Dengan hormat,\n"
        f"Bersama dengan email ini, kami sampaikan rekapitulasi peralatan milik perusahaan Bapak/Ibu "
        f"yang akan memasuki masa resertifikasi pada bulan {bulan_label} {tahun_label}.\n\n"
        "Mohon agar dapat dilakukan penjadwalan ulang untuk proses resertifikasi sesuai ketentuan yang berlaku.\n\n"
        "Rincian peralatan terlampir dalam dokumen PDF pada email ini.\n\n"
        "Demikian kami sampaikan. Atas perhatian dan kerja sama yang baik, kami ucapkan terima kasih.\n\n"
        "Hormat kami,\nPT SUCOFINDO (Persero)"
    )
    return subject, html_body, text_body


def get_email_rekap_recipients(email_perusahaan, emails_inspektur, target='both'):
    """Kembalikan daftar To yang sama untuk pratinjau dan pengiriman aktual."""
    if target not in ('both', 'perusahaan', 'inspektur'):
        target = 'both'
    penerima = []
    if target in ('both', 'perusahaan') and email_perusahaan:
        email = email_perusahaan.strip()
        if email not in ('', '-'):
            penerima.append(email)
    if target in ('both', 'inspektur'):
        for item in emails_inspektur or []:
            email = (item or '').strip()
            if email and email not in penerima:
                penerima.append(email)
    return penerima


def send_email_rekap(nama_perusahaan, email_perusahaan, emails_inspektur, pdf_path, pdf_filename,
                      bulan_label=None, tahun_label=None, target='both'):
    """
    target: 'both' (default, perusahaan + inspektur), 'perusahaan' (hanya
    perusahaan), atau 'inspektur' (hanya inspektur). Dipakai oleh tombol
    "Ke Perusahaan" / "Ke Inspektur" / "Kirim Semua" di halaman Rekap
    Resertifikasi. Scheduler otomatis tetap pakai default 'both'.
    """
    if target not in ('both', 'perusahaan', 'inspektur'):
        target = 'both'

    if bulan_label is None:
        bulan_label = BULAN_ID[datetime.now().month]
    if tahun_label is None:
        tahun_label = datetime.now().year

    penerima = get_email_rekap_recipients(email_perusahaan, emails_inspektur, target)

    if not penerima:
        if target == 'perusahaan':
            return False, "Tidak ada alamat email perusahaan yang valid untuk perusahaan ini."
        elif target == 'inspektur':
            return False, "Tidak ada alamat email inspektur yang valid untuk perusahaan ini."
        return False, "Tidak ada alamat email perusahaan/inspektur yang valid."

    if not config.SMTP_USER or not config.SMTP_PASS:
        return False, "SMTP belum dikonfigurasi (SMTP_USER/SMTP_PASS kosong). Cek file .env / environment variable."

    msg = MIMEMultipart('related')
    subject, html_body, text_body = build_email_rekap_content(nama_perusahaan, bulan_label, tahun_label)
    msg['Subject'] = subject
    msg['From'] = f"{config.EMAIL_SENDER_NAME} <{config.EMAIL_FROM}>"
    msg['To'] = ", ".join(penerima)

    alt = MIMEMultipart('alternative')
    msg.attach(alt)

    alt.attach(MIMEText(text_body, 'plain'))
    alt.attach(MIMEText(html_body, 'html'))

    for cid, path, fname in [
        ('logo_danantara', LOGO_DANANTARA_PATH, 'logo_danantara.png'),
        ('logo_idsurvey', LOGO_IDSURVEY_PATH, 'logo_idsurvey.png'),
        ('logo_sucofindo', LOGO_SUCOFINDO_PATH, 'logo_sucofindo.jpeg'),
    ]:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', f'<{cid}>')
                img.add_header('Content-Disposition', 'inline', filename=fname)
                msg.attach(img)

    with open(pdf_path, 'rb') as f:
        pdf_part = MIMEApplication(f.read(), _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(pdf_part)

    try:
        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
            if config.SMTP_USE_TLS:
                server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        semua_penerima = penerima + config.EMAIL_BCC_DEFAULT
        server.sendmail(config.EMAIL_FROM, semua_penerima, msg.as_string())
        server.quit()

        # Arsipkan PDF yang barusan dikirim ke R2, biar ada jejak permanen.
        # Kegagalan arsip TIDAK menggagalkan status "email terkirim" -- email-nya
        # kan sudah beneran terkirim, jadi tetap dilaporkan sukses ke user.
        ok_arsip, pesan_arsip = upload_local_file(pdf_path, f"rekap/{pdf_filename}", content_type='application/pdf')
        if not ok_arsip:
            logging.getLogger(__name__).warning("Arsip PDF ke R2 gagal (email tetap terkirim): %s", pesan_arsip)

        return True, f"Email terkirim ke: {', '.join(penerima)}"
    except Exception:
        logging.getLogger(__name__).exception("Gagal kirim email rekap")
        return False, "Gagal kirim email. Periksa konfigurasi SMTP (detail ada di log server)."
