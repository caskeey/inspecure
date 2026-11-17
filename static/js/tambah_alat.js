htmxReady(() => {
    
    // 1. LISTENER FILE UPLOAD (Tampilkan nama file yang dipilih)
    const fileInput = document.querySelector('.file-input-hidden');
    const fileNameDisplay = document.querySelector('.file-name-display');
    const uploadBox = document.querySelector('.upload-box');

    if(fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', (e) => {
            if(e.target.files.length > 0) {
                fileNameDisplay.innerText = "File terpilih: " + e.target.files[0].name;
                fileNameDisplay.style.color = "#4F46E5"; // Warna Indigo
                fileNameDisplay.style.fontWeight = "600";
                
                // Visual feedback pada kotak upload
                if(uploadBox) {
                    uploadBox.style.borderColor = "#4F46E5";
                    uploadBox.style.backgroundColor = "#EEF2FF";
                }
            }
        });
    }

    // 3. AUTOFILL EMAIL PERUSAHAAN
    // Begitu nama perusahaan yang diketik/dipilih cocok PERSIS (case-insensitive)
    // sama salah satu perusahaan yang udah ada di database, otomatis isi email-nya
    // -- biar gak perlu ngetik ulang & gak ada resiko typo bikin email lama
    // ke-overwrite gara-gara beda ketikan dikit.
    const dataPerusahaanEl = document.getElementById('data-perusahaan-source');
    const dataPerusahaan = dataPerusahaanEl ? JSON.parse(dataPerusahaanEl.textContent) : [];
    const inputNamaPerusahaan = document.getElementById('inputNamaPerusahaan');
    const inputEmailPerusahaan = document.getElementById('inputEmailPerusahaan');
    const hintEmailPerusahaan = document.getElementById('hintEmailPerusahaan');
    const hintDefaultText = hintEmailPerusahaan ? hintEmailPerusahaan.innerText : '';

    function cariPerusahaanByNama(nama) {
        const target = nama.trim().toUpperCase();
        if (!target) return null;
        return dataPerusahaan.find(pt => (pt.nama_perusahaan || '').trim().toUpperCase() === target) || null;
    }

    function coba_autofill_email_perusahaan() {
        const match = cariPerusahaanByNama(inputNamaPerusahaan.value);
        if (match) {
            const emailTersimpan = (match.email_perusahaan && match.email_perusahaan !== '-') ? match.email_perusahaan : '';
            inputEmailPerusahaan.value = emailTersimpan;
            inputEmailPerusahaan.style.backgroundColor = '#EEF2FF';
            inputEmailPerusahaan.style.borderColor = '#4F46E5';
            if (hintEmailPerusahaan) {
                hintEmailPerusahaan.innerText = emailTersimpan
                    ? 'Otomatis terisi dari data perusahaan yang sudah ada.'
                    : 'Perusahaan ini sudah ada di database, tapi belum ada email tersimpan -- isi di sini buat nyimpen yang baru.';
            }
        } else {
            // Nama gak cocok sama yang manapun -> berarti perusahaan baru,
            // balikin ke keadaan biasa (boleh diisi manual, gak di-lock).
            inputEmailPerusahaan.style.backgroundColor = '';
            inputEmailPerusahaan.style.borderColor = '';
            if (hintEmailPerusahaan) hintEmailPerusahaan.innerText = hintDefaultText;
        }
    }

    if (inputNamaPerusahaan && inputEmailPerusahaan) {
        inputNamaPerusahaan.addEventListener('input', coba_autofill_email_perusahaan);
        // Kalau form ini kebuka dalam keadaan udah keisi (misal browser autofill/back button), cek juga di awal.
        coba_autofill_email_perusahaan();
    }

    // 4. SIDEBAR MOBILE TOGGLE (Opsional untuk mobile)
    const mobileToggle = document.querySelector('.mobile-toggle');
    if(mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            if(sidebar) sidebar.classList.toggle('open');
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    const scannedUid = urlParams.get('uid');
    
    if (scannedUid) {
        const uidInput = document.querySelector('.uid-input');
        if (uidInput) {
            uidInput.value = scannedUid;
            
            // Efek visual biar user sadar sudah terisi
            uidInput.style.backgroundColor = "#EEF2FF";
            uidInput.style.borderColor = "#4F46E5";
            
            // Hapus parameter dari URL biar bersih
            window.history.replaceState({}, document.title, window.location.pathname);
            
            // Fokus ke kolom Serial Number (karena UID sudah isi)
            const serialInput = document.querySelector('input[name="nomor_serial"]');
            if(serialInput) serialInput.focus();
        }
    }
    
});

// LOGIKA DROPDOWN DINAMIS (Alat vs Manual)
function updatePeralatan() {
    try {
        // Ambil data JSON dari elemen script di HTML
        const dataElement = document.getElementById('data-peralatan-source');
        if (!dataElement) return;

        const dataPeralatan = JSON.parse(dataElement.textContent);
        const pekerjaanId = document.getElementById('selectPekerjaan').value;
        const dropdown = document.getElementById('selectPeralatan');
        const manualInput = document.getElementById('inputPeralatan');
        
        // Ambil elemen ikon panah (jika ada di HTML)
        const iconSelect = document.getElementById('iconSelectPeralatan');

        // Reset Dropdown
        dropdown.innerHTML = '<option value="">-- Pilih Spesifik --</option>';

        // LOGIKA UTAMA:
        // ID 1 (K3) & 2 (Laik Operasi) -> Gunakan Dropdown Database
        if (pekerjaanId == "1" || pekerjaanId == "2") {
            // Tampilkan Dropdown, Sembunyikan Input Manual
            dropdown.classList.remove('d-none');
            manualInput.classList.add('d-none');
            
            if(iconSelect) iconSelect.classList.remove('d-none');
            
            // Set Requirement
            manualInput.required = false;
            dropdown.required = true;
            
            // FILTER DATA (PERBAIKAN DI SINI: pakai item.id_pekerjaan)
            const filtered = dataPeralatan.filter(item => item.id_pekerjaan == pekerjaanId);
            
            filtered.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.nama_peralatan; // Kirim nama alat sebagai value
                opt.textContent = item.nama_peralatan;
                dropdown.appendChild(opt);
            });
            
        } else if (pekerjaanId) {
            // Kategori Lain -> Gunakan Input Manual
            dropdown.classList.add('d-none');
            manualInput.classList.remove('d-none');
            
            if(iconSelect) iconSelect.classList.add('d-none');

            dropdown.required = false;
            manualInput.required = true;
        } else {
            // Belum ada yang dipilih -> Sembunyikan Semua
            dropdown.classList.add('d-none');
            manualInput.classList.add('d-none');
            if(iconSelect) iconSelect.classList.add('d-none');
        }
    } catch(e) {
        console.error("Gagal memproses data peralatan:", e);
    }
}

// LOGIKA HITUNG EXPIRED DATE OTOMATIS
function hitungExpired() {
    const tglSertif = document.getElementById('tglSertif').value;
    const durasi = parseInt(document.getElementById('durasiAngka').value);
    const satuan = document.getElementById('durasiSatuan').value;
    const output = document.getElementById('viewExpired');
    
    if (tglSertif && durasi > 0) {
        const date = new Date(tglSertif);
        
        if (satuan === 'Tahun') {
            date.setFullYear(date.getFullYear() + durasi);
        } else if (satuan === 'Bulan') {
            date.setMonth(date.getMonth() + durasi);
        }
        
        // Format Tanggal Indonesia (Contoh: Senin, 12 Oktober 2026)
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        output.value = date.toLocaleDateString('id-ID', options);
        
        // Visual Feedback (Warna Hijau = Valid)
        output.style.borderColor = "#10B981";
        output.style.background = "#F0FDF4";
        output.style.color = "#15803D";
        output.style.fontWeight = "600";
    } else {
        output.value = "";
        output.style.borderColor = "";
        output.style.background = "#E2E8F0";
    }
}