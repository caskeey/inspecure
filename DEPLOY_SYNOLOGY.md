# Persiapan deploy INSPECURE ke Synology

Panduan ini memakai Synology Container Manager (Docker Compose), MySQL 8.4, dan reverse proxy HTTPS DSM. Ganti `domain-anda` dan path contoh sesuai NAS kamu.

## 1. Siapkan folder dan salinan data

Buat folder project, misalnya `/volume1/docker/inspecure`, lalu salin source project ke sana. Jangan salin folder `.venv`, `.venv-1`, atau cache Python. Pastikan `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `db.sql`, `backend/`, `templates/`, dan `static/` ikut tersalin.

Sebelum deploy, buat salinan aman database lokal. Jika database lokal sudah berisi aset yang harus dipertahankan, ekspor database tersebut dan rencanakan impor/migrasi tersendiri. `db.sql` hanya otomatis diimpor saat volume `db_data` baru dan kosong; ia tidak memperbarui database yang sudah berjalan.

## 2. Siapkan `.env` di NAS

Salin `env.example` menjadi `.env` di folder project NAS. Isi nilai rahasia langsung di NAS, jangan kirim `.env` ke chat atau commit ke Git.

- Buat `DB_ROOT_PASSWORD`, `DB_PASSWORD`, dan `SECRET_KEY` yang kuat dan unik.
- Isi `APP_PUBLIC_URL` dan `PASSWORD_RESET_URL_BASE` dengan URL HTTPS final.
- Isi kredensial SMTP dengan App Password (jangan password login Gmail biasa).
- Isi kredensial R2 jika file dan backup akan disimpan di R2.
- `BACKUP_ENABLED=true` dan `SCHEDULER_ENABLED=true` mengaktifkan backup harian serta rekap terjadwal.

Nilai `.env` lokal sekarang berbeda dari contoh produksi. Jangan menyalinnya mentah-mentah ke server; tetapkan URL dan rahasia khusus produksi.

## 3. Jalankan project

Di Synology Container Manager, buat Project dari folder `/volume1/docker/inspecure` dan gunakan `docker-compose.yml`. Atau melalui SSH dari folder project:

```sh
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100 app db
```

Pastikan service `db` sehat dan log aplikasi menunjukkan Gunicorn berjalan. Port aplikasi dibatasi ke `127.0.0.1:8085`; database tidak dipublikasikan ke port host.

## 4. Pasang HTTPS melalui DSM

Di DSM, buat reverse proxy dari domain publik port 443 ke `http://127.0.0.1:8085`. Pasang sertifikat TLS untuk domain itu dan aktifkan pembaruan sertifikat otomatis. Setelah HTTPS berhasil, ubah `SESSION_COOKIE_SECURE=true` di `.env`, lalu recreate app:

```sh
docker compose up -d --force-recreate app
```

Jangan mengaktifkan `SESSION_COOKIE_SECURE=true` sebelum HTTPS bekerja, karena login melalui HTTP tidak akan menyimpan sesi.

## 5. Periksa fitur penting

Masuk sebagai admin, lalu periksa dashboard, tambah/edit aset, pencarian UID RFID/NFC, unggah/buka dokumen, resertifikasi, pembuatan PDF, dan pengiriman email uji. Periksa tautan reset password dan pastikan URL email memakai domain HTTPS, bukan alamat lokal atau IP privat.

## 6. Pastikan backup bisa dipulihkan

Backup otomatis dijadwalkan harian pada `BACKUP_JAM:BACKUP_MENIT` zona WIB. Jika R2 aktif, file `.sql.gz` dikirim ke bucket; jika tidak, file disimpan di `static/backups/` lewat folder `./backups` pada NAS.

Setelah backup pertama, pastikan file benar-benar muncul di R2 atau folder `backups` NAS. Unduh satu backup dan uji pemulihan ke database uji terpisah. Backup yang belum pernah diuji restore belum terbukti dapat dipakai.

## 7. Catatan operasional

- `db_data`, `uploads`, `rekap`, dan `backups` adalah data persisten; jangan hapus saat memperbarui image.
- Jangan menjalankan lebih dari satu replika `app`: scheduler email dan backup berada dalam proses aplikasi dan dapat berjalan ganda.
- Untuk update kode, backup database dulu, salin perubahan, lalu jalankan `docker compose up -d --build`.
- Periksa log aplikasi dan status healthcheck Container Manager setelah update.
- Jangan membuka port MySQL `3306` ke internet.
