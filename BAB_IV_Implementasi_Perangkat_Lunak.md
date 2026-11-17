# Draf Bab IV — Hasil Implementasi Perangkat Lunak

> Draf ini disusun dari kerangka Bab IV pada naskah dan implementasi website INSPECURE pada workspace. Sesuaikan nomor gambar/tabel, nama lingkungan implementasi, serta tangkapan layar dengan kondisi sistem yang benar-benar digunakan saat penelitian.

## 4.1.2 Implementasi Perangkat Lunak

Implementasi perangkat lunak pada penelitian ini meliputi platform berbasis web INSPECURE dan program pada purwarupa RFID portabel. Platform INSPECURE dikembangkan menggunakan Python dengan framework Flask pada sisi server, HTML sebagai penyusun halaman, CSS untuk tampilan, dan JavaScript untuk interaksi pada sisi pengguna. Data aplikasi disimpan dalam basis data MySQL. Website dijalankan melalui peramban pada perangkat pengguna, sedangkan proses pembacaan tag pada purwarupa dilakukan oleh ESP32-S3 dan MFRC522. Hasil pembacaan dikirim ke perangkat host menggunakan BLE dalam mode HID, sehingga UID diterima sebagai masukan papan ketik. Sebagai jalur alternatif, tag dapat dibaca menggunakan fitur NFC pada perangkat Android yang mendukung Web NFC.

Pada versi perangkat yang digunakan dalam penelitian ini, modul sentuh TTP223 tidak digunakan. Oleh karena itu, uraian implementasi perangkat lunak dan alur sistem pada bab ini tidak menempatkan TTP223 sebagai masukan atau pemicu proses pemindaian. Pemindaian dimulai melalui antarmuka scan pada website dan dilakukan dengan menempelkan tag pada pembaca RFID portabel atau pembaca NFC yang didukung perangkat host.

### 1. Implementasi antarmuka dan fungsi website

INSPECURE menyediakan halaman autentikasi untuk membatasi akses ke fitur yang memerlukan sesi pengguna. Setelah berhasil masuk, pengguna diarahkan ke halaman dashboard. Dashboard menampilkan ringkasan jumlah aset, aset dengan sertifikasi aktif, aset yang memerlukan perhatian, serta jumlah perusahaan. Halaman ini juga menyediakan informasi masa berlaku sertifikat, aktivitas terbaru, dan kalender yang memuat tanggal kedaluwarsa maupun agenda yang dimasukkan pengguna.

Data aset dikelola melalui halaman data master. Pengguna dapat melihat dan mencari aset, sedangkan proses penambahan, perubahan, dan penghapusan data tersedia sesuai hak akses. Data aset mencakup identitas perangkat, UID RFID, nomor serial, perusahaan, informasi sertifikasi, masa berlaku, serta dokumen pendukung. Sistem juga menyediakan proses impor/ekspor dan beberapa alur input data. Status sertifikasi dihitung berdasarkan tanggal kedaluwarsa; perangkat yang telah melewati tanggal tersebut berstatus *Expired*, perangkat yang memasuki rentang masa resertifikasi ditandai *Masa Resertifikasi*, dan perangkat yang masih berada di luar rentang tersebut ditandai *Aktif*.

Halaman detail aset menyajikan spesifikasi, informasi perusahaan, status sertifikasi, tanggal sertifikasi dan kedaluwarsa, dokumen, serta riwayat resertifikasi. Ketika data sertifikasi diperbarui melalui proses resertifikasi, informasi sertifikasi sebelumnya disimpan sebagai riwayat agar perubahan dapat ditelusuri.

### 2. Implementasi proses pemindaian RFID/NFC

Proses identifikasi perangkat dilakukan melalui halaman *Scan Portable RFID/NFC*. Pengguna membuka antarmuka pemindaian, lalu memindai tag melalui reader BLE HID atau menggunakan NFC perangkat yang mendukung Web NFC. Pada jalur BLE HID, reader mengirim rangkaian karakter UID seperti masukan papan ketik. JavaScript pada halaman menangkap rangkaian karakter yang datang dengan jeda singkat dan diakhiri tombol Enter. Pada jalur Web NFC, browser membaca nomor seri tag, kemudian aplikasi menormalisasi format UID agar kedua jalur menggunakan format yang sama. Sistem menerapkan jeda pemrosesan untuk mengabaikan UID yang sama apabila terbaca berulang dalam waktu singkat.

Setelah UID diterima, JavaScript mengirim permintaan ke endpoint `/api/scan_detail/<uid>`. Server memeriksa UID pada data aset dan mencatat setiap pemindaian beserta pengguna dan waktu pemindaian pada tabel log scan, termasuk pemindaian dengan UID yang tidak terdaftar. Jika UID ditemukan, website menampilkan informasi ringkas aset, seperti nama perangkat, nomor serial, perusahaan, status, dan tanggal kedaluwarsa, serta tautan ke halaman detail. Jika UID tidak ditemukan, website menampilkan pemberitahuan bahwa UID belum terdaftar. Jika permintaan tidak berhasil karena koneksi atau sesi, website menampilkan pesan kesalahan agar pengguna dapat mencoba kembali.

Pada jalur reader BLE HID, komunikasi dari reader ke host berlangsung melalui Bluetooth dan menyerupai pengetikan keyboard. Koneksi internet diperlukan oleh browser untuk mengakses website serta mengirim UID ke server dan mengambil data aset. Dengan demikian, pemindaian fisik melalui BLE tidak dengan sendirinya menyimpan atau mencocokkan data sertifikasi secara luring.

**[Sisipkan Gambar 4.x di sini: tangkapan layar halaman Scan Portable RFID/NFC dan contoh hasil scan aset terdaftar.]**

*Gambar 4.x Antarmuka pemindaian dan hasil identifikasi aset pada INSPECURE*

### 3. Implementasi pengingat dan rekapitulasi resertifikasi

INSPECURE menyediakan halaman resertifikasi untuk menampilkan aset yang memasuki periode resertifikasi. Data dapat dikelompokkan berdasarkan perusahaan dan disiapkan sebagai rekap PDF. Pengiriman rekap dapat dijalankan melalui fitur yang tersedia pada halaman, sedangkan scheduler aplikasi menjalankan proses otomatis sesuai konfigurasi hari dan waktu yang ditetapkan. Proses otomatis mengambil data yang belum dikirim, menyusun rekap per perusahaan, membuat dokumen PDF, dan mengirimkannya melalui email apabila konfigurasi email tersedia. Sistem juga memiliki proses pengingat pratinjau sebelum jadwal rekap bulanan.

Untuk naskah final, cantumkan tanggal dan jam aktual dari konfigurasi penelitian. Jangan menyatakan jadwal tanggal 28 pukul 10.00 WIB sebagai hasil implementasi apabila nilai konfigurasi yang dipakai berbeda. Demikian pula, keberhasilan pengiriman email perlu didukung oleh hasil pengujian dan konfigurasi yang benar-benar digunakan.

**[Sisipkan Gambar 4.x di sini: halaman rekap resertifikasi atau contoh dokumen PDF yang dihasilkan.]**

*Gambar 4.x Halaman rekapitulasi resertifikasi perangkat*

### 4. Implementasi basis data

Basis data MySQL digunakan untuk menyimpan akun pengguna, data aset dan UID, data master perusahaan dan jenis peralatan, catatan pemindaian, riwayat sertifikasi, aktivitas pengguna, serta agenda kalender. Data UID pada aset menjadi kunci pencarian saat proses scan berlangsung. Hasil pencocokan UID digunakan untuk menentukan informasi yang ditampilkan pada website, sedangkan catatan pemindaian disimpan agar aktivitas identifikasi dapat ditelusuri.

**[Sisipkan Gambar 4.x di sini: diagram relasi tabel yang sesuai dengan skema basis data versi implementasi.]**

*Gambar 4.x Struktur relasi basis data INSPECURE*

### 5. Implementasi program pada perangkat RFID portabel

Program pada ESP32-S3 bertugas menginisialisasi modul MFRC522, membaca UID tag, dan mengirimkan karakter UID ke perangkat host melalui BLE HID. Website menerima UID tersebut melalui mekanisme pembaca papan ketik yang telah dijelaskan sebelumnya. Bagian ini perlu dilengkapi dengan tangkapan layar atau potongan kode firmware yang benar-benar digunakan, berikut konfigurasi pin dan parameter BLE yang terverifikasi.

Karena TTP223 tidak digunakan pada purwarupa akhir, hapus komponen tersebut dari uraian implementasi, gambar rangkaian, daftar komponen, konfigurasi pin, dan diagram alir yang menggambarkan masukan sentuh. Jika tombol atau mekanisme pemicu lain memang digunakan, sebutkan hanya setelah komponen tersebut dipastikan pada perangkat akhir. Jangan mengganti TTP223 dengan komponen lain di dalam naskah tanpa verifikasi fisik.

### 6. Ringkasan alur implementasi perangkat lunak

Secara umum, alur perangkat lunak dimulai ketika pengguna masuk ke INSPECURE dan membuka halaman pemindaian. UID diterima dari reader BLE HID atau Web NFC, kemudian dinormalisasi dan dikirimkan ke server. Server mencatat aktivitas pemindaian, mencocokkan UID dengan data aset, lalu mengirimkan respons. Website menampilkan detail aset apabila UID terdaftar atau pemberitahuan apabila UID tidak ditemukan. Data sertifikasi, dokumen, dan riwayat dapat dilihat pada halaman detail, sedangkan pemantauan masa berlaku serta proses resertifikasi tersedia pada dashboard dan halaman resertifikasi.

**[Sisipkan Gambar 4.x di sini: diagram alir implementasi final, tanpa TTP223.]**

*Gambar 4.x Alur implementasi perangkat lunak INSPECURE dan pemindaian RFID/NFC*

## Catatan penyesuaian naskah sebelum final

1. PDF sumber masih memiliki kerangka Bab IV dan belum memuat tangkapan layar maupun hasil pengujian. Masukkan gambar hasil implementasi yang aktual sebelum menyerahkan naskah.
2. Sinkronkan seluruh bagian Bab I–III yang menyebut TTP223 dengan keadaan perangkat akhir. Pada PDF sumber, komponen tersebut masih disebut pada uraian konfigurasi daya, tabel komponen PCB, dan penjelasan rancangan. Hapus atau revisi penyebutan tersebut sesuai rangkaian final.
3. Diagram blok, skematik, tata letak PCB, tabel komponen, casing, dan diagram alir harus mencerminkan perangkat yang benar-benar dirakit. Draf ini tidak mengasumsikan adanya tombol pengganti TTP223.
4. Bedakan fungsi prototipe reader BLE HID dari aplikasi web: reader mengirim UID ke host, sedangkan pencocokan UID dengan data aset dilakukan oleh server INSPECURE.
5. Isi subbab 4.2–4.4 dengan data hasil pengujian aktual. Angka target pada Bab III bukan hasil pengukuran dan tidak boleh dituliskan sebagai hasil.
