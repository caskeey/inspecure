from datetime import datetime
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
from db import db_cursor
from error_utils import PesanUser

# --- HELPER FUNCTIONS (dipakai bareng oleh crud.py, resertifikasi.py, dll) ---

def build_dokumen_key(uid, original_filename):
    """Bikin key R2 untuk sebuah dokumen yang DIJAMIN unik, walau nama file
    aslinya kebetulan sama persis dengan upload sebelumnya (mis. alat yang
    sama diresertifikasi dua kali dan dua-duanya diupload dengan nama file
    'sertifikat.pdf'). Tanpa timestamp ini, upload_file() bakal MENIMPA
    dokumen lama di R2 karena key-nya jadi sama persis -- padahal dokumen
    lama itu masih dirujuk oleh tbl_riwayat_sertifikasi.
    Format: dokumen/{uid}_{YYYYMMDDHHMMSS}_{nama_file}
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = secure_filename(f"{uid}_{timestamp}_{original_filename}")
    return f"dokumen/{filename}"

def hitung_tgl_expired(tgl_sertifikasi, durasi, satuan):
    """Tanggal expired = tgl_sertifikasi + durasi. satuan 'Tahun' -> tahun, selain itu -> bulan.

    tgl_sertifikasi : string 'YYYY-MM-DD'
    durasi          : int (angka sudah divalidasi pemanggil)
    Return string 'YYYY-MM-DD'. Format yang tidak valid menimbulkan ValueError;
    tahun di luar 1900-2100 ditolak dengan pesan validasi yang aman untuk pengguna."""
    tgl = datetime.strptime(tgl_sertifikasi, '%Y-%m-%d')
    if not 1900 <= tgl.year <= 2100:
        raise PesanUser('Tahun sertifikasi harus antara 1900 dan 2100. Periksa kembali tanggal yang dipilih.')
    delta = relativedelta(years=durasi) if satuan == 'Tahun' else relativedelta(months=durasi)
    return (tgl + delta).strftime('%Y-%m-%d')

def hitung_status(tgl_expired_str):
    if not tgl_expired_str: return "Unknown"
    try:
        exp_date = datetime.strptime(str(tgl_expired_str), '%Y-%m-%d').date()
    except ValueError:
        return "Error Date"
    today = datetime.now().date()
    delta = exp_date - today
    if today > exp_date: return "Expired"
    elif delta.days <= 90: return "Masa Resertifikasi"
    else: return "Aktif"

def get_or_create_perusahaan(nama_pt, email_pt=None):
    if not nama_pt: return None
    nama_pt = str(nama_pt).strip().upper()
    email_pt = str(email_pt).strip() if email_pt else None
    with db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id_perusahaan, email_perusahaan FROM tbl_master_perusahaan WHERE UPPER(nama_perusahaan) = %s", (nama_pt,))
        existing = cursor.fetchone()
        if existing:
            pt_id = existing['id_perusahaan']
            # Kalau email diisi & beda dari yang tersimpan (atau yang lama masih kosong/'-'), update.
            if email_pt and email_pt != existing.get('email_perusahaan'):
                cursor.execute("UPDATE tbl_master_perusahaan SET email_perusahaan=%s WHERE id_perusahaan=%s", (email_pt, pt_id))
        else:
            cursor.execute("INSERT INTO tbl_master_perusahaan (nama_perusahaan, email_perusahaan) VALUES (%s, %s)", (nama_pt, email_pt or '-'))
            pt_id = cursor.lastrowid
    return pt_id

def get_or_create_peralatan(nama_peralatan, id_pekerjaan):
    """Dipakai buat kategori pekerjaan yang belum ada master datanya (mis. LAINNYA / SERTIFIKASI LAIK FUNGSI),
    di mana user isi 'Jenis Peralatan' secara manual (teks bebas), bukan pilih dari dropdown."""
    if not nama_peralatan or not id_pekerjaan: return None
    nama_peralatan = str(nama_peralatan).strip()
    if not nama_peralatan: return None
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id_peralatan FROM tbl_master_peralatan WHERE UPPER(nama_peralatan) = %s AND id_pekerjaan = %s",
            (nama_peralatan.upper(), id_pekerjaan)
        )
        existing = cursor.fetchone()
        if existing:
            peralatan_id = existing['id_peralatan']
        else:
            cursor.execute(
                "INSERT INTO tbl_master_peralatan (id_pekerjaan, nama_peralatan) VALUES (%s, %s)",
                (id_pekerjaan, nama_peralatan)
            )
            peralatan_id = cursor.lastrowid
    return peralatan_id

def get_master_data():
    with db_cursor() as cursor:
        cursor.execute("SELECT id_pekerjaan as id, nama_pekerjaan FROM tbl_master_pekerjaan")
        pek = cursor.fetchall()
        cursor.execute("SELECT id_peralatan as id, id_pekerjaan, nama_peralatan FROM tbl_master_peralatan")
        per = cursor.fetchall()
        cursor.execute("SELECT id_perusahaan as id, nama_perusahaan, email_perusahaan FROM tbl_master_perusahaan")
        pt = cursor.fetchall()
    return pek, per, pt

def safe_int(val):
    if not val: return None
    try: return int(val)
    except: return None
