# Peta Kode INSPECURE

Dokumen ini menunjukkan lokasi fitur utama dan alasan file dipisah. Modul CSS/JavaScript yang dimuat berurutan harus tetap mempertahankan urutan `<script>` atau `@import`-nya.

## Backend

| File | Fungsi |
| --- | --- |
| `backend/app.py` | Membuat aplikasi Flask, konfigurasi cookie/CSRF/cache/upload, mendaftarkan blueprint, dan menjalankan scheduler. |
| `backend/error_handlers.py` | Menampilkan halaman kustom untuk error HTTP seperti 404 dan 500. |
| `backend/routes/auth.py` | Login, logout, lupa password, dan reset password. |
| `backend/routes/auth_registration.py` | Registrasi akun; dipisah dari alur autentikasi utama. |
| `backend/routes/dashboard.py` | Dashboard, kalender, agenda, dan endpoint scan detail RFID/NFC. |
| `backend/routes/alat/__init__.py` | Membuat blueprint `alat` dan mengimpor modul route supaya seluruh route terdaftar. |
| `backend/routes/alat/crud.py` | Tambah, ubah, dan hapus aset. |
| `backend/routes/alat/data_master.py` | Halaman daftar aset dan API tabel dengan pencarian serta pagination server-side. |
| `backend/routes/alat/detail.py` | Detail aset, dokumen, dan riwayat inspeksi/sertifikasi. |
| `backend/routes/alat/resertifikasi.py` | Pencarian aset dan proses resertifikasi dari menu alat. |
| `backend/routes/alat/import_export.py` | Impor dan ekspor data aset. |
| `backend/routes/alat/import_helpers.py` | Validasi dan pemetaan nilai baris spreadsheet saat impor. |
| `backend/routes/alat/helpers.py` | Fungsi bersama untuk tanggal expired, status sertifikasi, dan data master aset. |
| `backend/routes/settings.py` | Halaman pengaturan akun dan endpoint profil/password. |
| `backend/routes/settings_users.py` | Operasi manajemen pengguna dan validasi terkait akun. |
| `backend/routes/resertifikasi/` | Route, pengambilan data, pembuatan PDF, pengiriman email, dan job resertifikasi terjadwal. Tiap file menangani satu bagian alur tersebut. |
| `backend/scheduler.py` | Mendaftarkan jadwal otomatis bulanan dan pengingat pratinjau email. |
| `backend/scheduler_notifications.py` | Membuat dan mengirim notifikasi pengingat/ringkasan ke admin. |

## Template

| File | Fungsi |
| --- | --- |
| `templates/base.html` | Kerangka halaman setelah login: sidebar, header, area konten, dan script shell. |
| `templates/components/sidebar.html` | Navigasi samping. |
| `templates/components/head_scripts.html` | Memuat script global untuk shell, pembaca RFID/NFC, modal scan, dan CSRF. |
| `templates/components/dashboard_panels.html` | Panel ringkasan dashboard yang dipanggil oleh `dashboard.html`. |
| `templates/components/detail_tabs.html` | Isi tab spesifikasi, dokumen, dan riwayat di detail aset. |
| `templates/components/settings_user_modals.html` | Modal tambah/ubah pengguna di halaman pengaturan. |
| `templates/dashboard.html` | Susunan halaman dashboard dan penempatan kalender/agenda. |
| `templates/data_master.html` | Susunan halaman database aset. |
| `templates/input_ocr.html` | Form OCR dan pratinjau dokumen. |
| `templates/daftar_resertifikasi.html` | Form pencarian UID sebelum membuka alur resertifikasi. |
| `templates/resertifikasi.html` | Rekap aset yang perlu resertifikasi dan kontrol kirim email/PDF. |

## JavaScript

| File | Fungsi |
| --- | --- |
| `static/js/app_shell.js` | Perilaku dasar header/sidebar dan fungsi shell global. |
| `static/js/app_keyboard_reader.js` | Menangkap input UID dari pembaca RFID/BLE yang bertindak seperti keyboard. |
| `static/js/app_web_nfc.js` | Membaca tag menggunakan Web NFC di perangkat yang mendukungnya. |
| `static/js/app_scan_modal.js` | Membuka/menutup modal scan dan menampilkan hasil scan. |
| `static/js/app_csrf.js` | Menambahkan token CSRF ke permintaan JavaScript. |
| `static/js/shell_store.js` | Penyimpanan preferensi shell di browser. |
| `static/js/shell_preferences.js` | Preferensi tampilan dan sidebar. |
| `static/js/shell_command_palette.js` | Pencarian halaman dengan pintasan Ctrl/Cmd+K. |
| `static/js/shell_database_views.js` | Perilaku tampilan tabel, list, dan gallery yang digunakan lintas halaman. |
| `static/js/shell_sidebar_tips.js` | Tip kecil pada navigasi/sidebar. |
| `static/js/dashboard_calendar.js` | Render kalender dan perpindahan bulan. |
| `static/js/dashboard.js` | Interaksi tambahan dashboard setelah kalender siap. |
| `static/js/daftar_resertifikasi.js` | Mencari UID, mengisi data aset, dan mengarahkan ke resertifikasi atau registrasi baru. |
| `static/js/input_ocr_form.js` | Interaksi form OCR dan pengiriman data. |
| `static/js/input_ocr_render.js` | Render halaman PDF/gambar dan kontrol zoom/geser. |
| `static/js/input_ocr_tesseract.js` | OCR lokal di browser dan pemilihan teks hasil OCR. |
| `static/js/input_ocr_selection.js` | Memilih kata pada hasil OCR untuk mengisi kolom form. |
| `static/js/input_ocr_navigation.js` | Navigasi halaman dokumen dan kontrol zoom. |

## CSS

File seperti `static/css/dashboard.css` adalah entrypoint yang mengimpor bagian-bagian berurutan dari `static/css/parts/`. Bagian bernomor menjaga satu file aturan tetap mudah dicari dan diedit. Pola yang sama dipakai untuk halaman data master, detail, OCR, pengaturan, sidebar, dan form lainnya.

## Batas ukuran

Kode aplikasi Python, HTML, CSS, dan JavaScript ditata agar maksimal 200 baris per file. CSS font di `static/fonts/` berasal dari paket font vendor dan sengaja tetap utuh: file tersebut berisi ribuan definisi glyph yang tidak aman/berguna jika dipisah manual. `db.sql` juga merupakan dump database untuk impor, sehingga sebaiknya tetap menjadi satu berkas.
