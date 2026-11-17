import os

# --- PATH ---
# File ini ada di backend/routes/resertifikasi/, sedangkan folder static/ ada di
# folder utama project (tiga tingkat di atas folder resertifikasi/).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # -> folder utama project
KOP_SURAT_PATH = os.path.join(BASE_DIR, 'static', 'assets', 'kop_surat.jpg')     # background 1 halaman penuh (dipakai PDF rekap)
LOGO_DANANTARA_PATH = os.path.join(BASE_DIR, 'static', 'assets', 'static_assets_logo_danantara.png')
LOGO_IDSURVEY_PATH = os.path.join(BASE_DIR, 'static', 'assets', 'static_assets_logo_idsurvey.png')
LOGO_SUCOFINDO_PATH = os.path.join(BASE_DIR, 'static', 'assets', 'static_assets_logo_sucofindo.jpeg')
REKAP_DIR = os.path.join(BASE_DIR, 'static', 'rekap_resertifikasi')
os.makedirs(REKAP_DIR, exist_ok=True)

BULAN_ID = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}
