import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from .constants import KOP_SURAT_PATH, REKAP_DIR, BULAN_ID
from .data import safe_filename


# =========================================================
# 2. BUAT PDF REKAP (pakai kertas/kop surat asli, format sama seperti contoh)
#    -> "Buat rekapitulasi"
# =========================================================
def generate_pdf_rekap(nama_perusahaan, alat_list, bulan_label=None, tahun_label=None):
    if bulan_label is None:
        bulan_label = BULAN_ID[datetime.now().month]
    if tahun_label is None:
        tahun_label = datetime.now().year

    filename = f"rekap_{safe_filename(nama_perusahaan)}_{safe_filename(bulan_label)}_{tahun_label}.pdf"
    filepath = os.path.join(REKAP_DIR, filename)

    def draw_kop(canvas_obj, doc):
        canvas_obj.saveState()
        if os.path.exists(KOP_SURAT_PATH):
            canvas_obj.drawImage(
                KOP_SURAT_PATH, 0, 0,
                width=A4[0], height=A4[1],
                preserveAspectRatio=False, mask='auto'
            )
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=58 * mm, bottomMargin=38 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle('body_rekap', parent=styles['Normal'], fontSize=10.5, leading=15.5)

    story = []
    story.append(Paragraph(f"Yth. Pimpinan <b>{nama_perusahaan}</b>,", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Dengan hormat,", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Bersama dengan surat ini, kami sampaikan rekapitulasi peralatan milik perusahaan Bapak/Ibu "
        f"yang akan memasuki masa resertifikasi pada bulan <b>{bulan_label} {tahun_label}</b>.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Mohon agar dapat dilakukan penjadwalan ulang untuk proses resertifikasi sesuai ketentuan yang berlaku.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Rincian peralatan tercantum pada tabel di bawah ini.", body_style))
    story.append(Spacer(1, 16))

    data = [["No", "Nama Alat", "Seri", "Masa Berlaku", "Tanggal Resertifikasi"]]
    for i, a in enumerate(alat_list, start=1):
        durasi = a.get('durasi_angka')
        satuan = a.get('durasi_satuan') or ''
        masa = f"{durasi} {satuan}".strip() if durasi else "-"
        tgl_exp = a.get('tgl_expired')
        if hasattr(tgl_exp, 'strftime'):
            tgl_str = tgl_exp.strftime('%d-%m-%Y')
        else:
            tgl_str = str(tgl_exp) if tgl_exp else '-'
        data.append([
            str(i),
            a.get('nama_alat') or '-',
            a.get('nomor_serial') or '-',
            masa,
            tgl_str
        ])

    table = Table(data, colWidths=[10 * mm, 55 * mm, 33 * mm, 27 * mm, 42 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#BEE3F8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B3C5D')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#8FB8CC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3FAFD')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))
    story.append(Paragraph("Demikian kami sampaikan. Atas perhatian dan kerja sama yang baik, kami ucapkan terima kasih.", body_style))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Hormat kami,<br/><br/><b>PT SUCOFINDO (Persero)</b>", body_style))

    doc.build(story, onFirstPage=draw_kop, onLaterPages=draw_kop)
    return filepath, filename