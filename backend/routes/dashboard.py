from flask import Blueprint, render_template, session, request, jsonify
from db import db_cursor
from auth_utils import login_required, admin_required
from error_utils import pesan_aman

main_bp = Blueprint('main', __name__)

# =========================================================
# 1. DASHBOARD & API SCANNER
# =========================================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    with db_cursor() as cursor:
        # A. STATISTIK
        cursor.execute("SELECT COUNT(*) as total FROM tbl_alat")
        total_aset = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as valid FROM tbl_alat WHERE status_sertifikasi = 'Aktif'")
        total_valid = cursor.fetchone()['valid']
        cursor.execute("SELECT COUNT(*) as warning FROM tbl_alat WHERE status_sertifikasi IN ('Expired', 'Masa Resertifikasi')")
        total_warning = cursor.fetchone()['warning']
        cursor.execute("SELECT COUNT(*) as total FROM tbl_master_perusahaan")
        total_klien = cursor.fetchone()['total']

        # B. CHART DATA
        cursor.execute("""
            SELECT DATE_FORMAT(tgl_expired, '%M %Y') as bulan_label, COUNT(id_alat) as jumlah 
            FROM tbl_alat 
            WHERE tgl_expired BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(tgl_expired, '%Y-%m'), bulan_label
            ORDER BY DATE_FORMAT(tgl_expired, '%Y-%m') ASC
        """)
        chart_data = cursor.fetchall()
        chart_labels = [i['bulan_label'] for i in chart_data] if chart_data else ["No Data"]
        chart_values = [i['jumlah'] for i in chart_data] if chart_data else [0]

        # C. URGENT TABLE
        cursor.execute("""
            SELECT a.nama_alat, a.rfid_uid, a.tgl_expired, mp.nama_perusahaan, a.status_sertifikasi
            FROM tbl_alat a
            LEFT JOIN tbl_master_perusahaan mp ON a.id_perusahaan = mp.id_perusahaan
            WHERE a.status_sertifikasi != 'Aktif' OR a.tgl_expired <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            ORDER BY a.tgl_expired ASC LIMIT 5
        """)
        urgent_assets = cursor.fetchall()
    
        # D. LOGS
        cursor.execute("""
            SELECT l.*, u.username FROM tbl_activity_logs l
            LEFT JOIN tbl_users u ON l.id_users = u.id_users
            ORDER BY l.timestamp DESC LIMIT 4
        """)
        recent_logs = cursor.fetchall()
    
        # E. CALENDAR
        events = []
        cursor.execute("SELECT nama_alat, tgl_expired FROM tbl_alat WHERE tgl_expired IS NOT NULL")
        for i in cursor.fetchall():
            events.append({'title': f"EXP: {i['nama_alat']}", 'date': str(i['tgl_expired']), 'type': 'expired'})
    
        cursor.execute("SELECT * FROM tbl_calendar_events")
        for i in cursor.fetchall():
            events.append({'title': i['title'], 'date': str(i['event_date']), 'type': 'manual'})
    return render_template('dashboard.html', active_page='dashboard', user=session['user'],
                           total_aset=total_aset, total_valid=total_valid, total_warning=total_warning,
                           total_klien=total_klien, chart_labels=chart_labels, chart_values=chart_values,
                           urgent_assets=urgent_assets, recent_logs=recent_logs, events_json=events)

# API SCANNER (Pop-up Detail)
@main_bp.route('/api/scan_detail/<uid>')
@login_required(json=True)
def scan_detail(uid):
    query = """
        SELECT a.*, mp.nama_perusahaan, mpl.nama_peralatan
        FROM tbl_alat a
        LEFT JOIN tbl_master_perusahaan mp ON a.id_perusahaan = mp.id_perusahaan
        LEFT JOIN tbl_master_peralatan mpl ON a.id_peralatan = mpl.id_peralatan
        WHERE a.rfid_uid = %s
    """
    with db_cursor(commit=True) as cursor:
        cursor.execute(query, (uid,))
        alat = cursor.fetchone()

        # Catat SEMUA scan ke tbl_logs_scan -- baik yang ketemu alatnya maupun
        # yang enggak (id_alat NULL kalau not found) -- gak peduli dari reader
        # USB, NFC HP, atau BLE portable (semua lewat endpoint ini). Sekalian
        # dicatet siapa (id_users) yang lagi scan, dari session yang login.
        cursor.execute(
            "INSERT INTO tbl_logs_scan (rfid_uid, id_users, id_alat) VALUES (%s, %s, %s)",
            (uid, session.get('uid'), alat['id_alat'] if alat else None)
        )

    if alat:
        alat['tgl_sertifikasi'] = str(alat['tgl_sertifikasi']) if alat['tgl_sertifikasi'] else '-'
        alat['tgl_expired'] = str(alat['tgl_expired']) if alat['tgl_expired'] else '-'
        return jsonify({'status': 'found', 'data': alat})
    else:
        return jsonify({'status': 'not_found'})

# API ADD EVENT CALENDAR
@main_bp.route('/add_event', methods=['POST'])
@admin_required(json=True)
def add_event():
    try:
        with db_cursor(dictionary=False, commit=True) as cursor:
            cursor.execute("INSERT INTO tbl_calendar_events (title, event_date, id_user) VALUES (%s, %s, %s)", 
                           (request.form.get('title'), request.form.get('date'), session.get('uid')))
        return jsonify({'status': 'success'})
    except Exception as e: return jsonify({'status': 'error', 'msg': pesan_aman(e)})