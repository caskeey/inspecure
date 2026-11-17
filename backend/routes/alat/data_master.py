"""Halaman dan API daftar aset (DataTables server-side)."""
from flask import render_template, request, jsonify
from db import db_cursor
from auth_utils import login_required
from . import alat_bp

@alat_bp.route('/data_master')
@login_required
def data_master():
    return render_template('data_master.html', active_page='master')


@alat_bp.route('/api/data_master')
@login_required
def api_data_master():
    """API endpoint untuk DataTables server-side processing.
    Mendukung pagination, sorting, dan search."""
    # DataTables sends these params:
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 25, type=int)
    search_value = request.args.get('search[value]', '').strip()
    order_col_idx = request.args.get('order[0][column]', 0, type=int)
    order_dir = request.args.get('order[0][dir]', 'desc')

    if length < 1:
        length = 25
    elif length > 100:
        length = 100
    if start < 0:
        start = 0

    # Map column index to SQL column
    columns = ['a.rfid_uid', 'a.nama_alat', 'a.nomor_serial', 
               'mpk.nama_pekerjaan', 'mpl.nama_peralatan',
               'mpr.nama_perusahaan', 'a.tgl_expired', 'a.status_sertifikasi']

    order_col = columns[min(max(order_col_idx, 0), len(columns)-1)]
    # Sanitize order direction
    order_dir = 'ASC' if order_dir.lower() == 'asc' else 'DESC'

    base_from = """
        FROM tbl_alat a
        LEFT JOIN tbl_master_perusahaan mpr ON a.id_perusahaan = mpr.id_perusahaan
        LEFT JOIN tbl_master_pekerjaan mpk ON a.id_pekerjaan = mpk.id_pekerjaan
        LEFT JOIN tbl_master_peralatan mpl ON a.id_peralatan = mpl.id_peralatan
    """

    where_conditions = []
    params = []

    # Filter lanjutan dikirim sebagai parameter terpisah agar diterapkan di database,
    # bukan hanya pada halaman yang sedang dimuat browser.
    for key, column in (
        ('job', 'mpk.nama_pekerjaan'),
        ('tool', 'mpl.nama_peralatan'),
        ('company', 'mpr.nama_perusahaan'),
        ('status', 'a.status_sertifikasi'),
    ):
        value = request.args.get(key, '').strip()
        if value:
            where_conditions.append(f"{column} = %s")
            params.append(value)

    year = request.args.get('year', '').strip()
    month = request.args.get('month', '').strip()
    day = request.args.get('day', '').strip()
    if year.isdigit() and len(year) == 4:
        where_conditions.append('YEAR(a.tgl_expired) = %s')
        params.append(int(year))
    if month.isdigit() and 1 <= int(month) <= 12:
        where_conditions.append('MONTH(a.tgl_expired) = %s')
        params.append(int(month))
    if day.isdigit() and 1 <= int(day) <= 31:
        where_conditions.append('DAY(a.tgl_expired) = %s')
        params.append(int(day))

    if search_value:
        where_conditions.append("""(a.rfid_uid LIKE %s OR a.nama_alat LIKE %s OR a.nomor_serial LIKE %s
                   OR mpk.nama_pekerjaan LIKE %s OR mpl.nama_peralatan LIKE %s
                   OR mpr.nama_perusahaan LIKE %s OR a.status_sertifikasi LIKE %s)""")
        params.extend([f"%{search_value}%"] * 7)

    # Dukung juga column search jika dikirimkan oleh DataTables (misal dari advanced filter)
    for i, col in enumerate(columns):
        col_search = request.args.get(f'columns[{i}][search][value]', '').strip()
        if col_search:
            where_conditions.append(f"{col} LIKE %s")
            params.append(f"%{col_search}%")

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    with db_cursor() as cursor:
        # Total records (unfiltered)
        cursor.execute("SELECT COUNT(*) as cnt FROM tbl_alat")
        total = cursor.fetchone()['cnt']

        # Filtered count
        cursor.execute(f"SELECT COUNT(*) as cnt {base_from} {where_clause}", params)
        filtered = cursor.fetchone()['cnt']

        # Data page
        query = f"""
            SELECT a.id_alat as id, a.rfid_uid, a.nomor_serial, a.nama_alat,
                mpk.nama_pekerjaan as jenis_pekerjaan, mpl.nama_peralatan as jenis_alat,
                mpr.nama_perusahaan, a.tgl_expired, a.status_sertifikasi
            {base_from} {where_clause}
            ORDER BY {order_col} {order_dir}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [length, start])
        rows = cursor.fetchall()

    # Format data for DataTables
    data = []
    for row in rows:
        item = [
            row['rfid_uid'] or '',
            row['nama_alat'] or '',
            row['nomor_serial'] or '',
            row['jenis_pekerjaan'] or '',
            row['jenis_alat'] or '',
            row['nama_perusahaan'] or '',
            str(row['tgl_expired']) if row['tgl_expired'] else '',
            row['status_sertifikasi'] or '',
        ]
        # ID dipakai link detail untuk semua role, dan tombol aksi khusus admin.
        item.append(str(row['id']))
        data.append(item)

    return jsonify({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': data,
    })


@alat_bp.route('/api/data_master/filter-options')
@login_required
def api_data_master_filter_options():
    """Nilai unik untuk filter dropdown, tanpa memuat semua baris aset ke browser."""
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT nama_pekerjaan FROM tbl_master_pekerjaan WHERE nama_pekerjaan IS NOT NULL ORDER BY nama_pekerjaan")
        jobs = [row['nama_pekerjaan'] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT nama_peralatan FROM tbl_master_peralatan WHERE nama_peralatan IS NOT NULL ORDER BY nama_peralatan")
        tools = [row['nama_peralatan'] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT nama_perusahaan FROM tbl_master_perusahaan WHERE nama_perusahaan IS NOT NULL ORDER BY nama_perusahaan")
        companies = [row['nama_perusahaan'] for row in cursor.fetchall()]

    return jsonify({'jobs': jobs, 'tools': tools, 'companies': companies})
