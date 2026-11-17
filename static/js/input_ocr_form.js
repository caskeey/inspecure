/* static/js/input_ocr_form.js
 * Isinya logic FORM di halaman Input OCR:
 * - Dropdown "Jenis Peralatan" yang berubah sesuai kategori pekerjaan
 * - Nandain input mana yang lagi "aktif" (target buat diisi hasil klik OCR)
 * - Autofill email perusahaan
 *
 * Variabel `activeInput` di sini dipakai bareng sama input_ocr_engine.js
 * (di sana yang isi nilainya waktu user klik kata hasil OCR) -- makanya
 * file ini WAJIB di-load sebelum input_ocr_engine.js di HTML.
 */

// Sengaja pakai `var` (bukan `let`) -- file ini bisa RE-EKSEKUSI kalau
// halaman Input OCR dibuka lagi lewat navigasi SPA (htmx) tanpa hard refresh.
// `let` bakal SyntaxError kalau dideklarasiin dua kali; `var` aman.
var activeInput = null;

htmxReady(() => {
    setupDropdownLogic();
    setupInputFocusListener();
    setupPerusahaanAutofill();
});

// 1. SETUP LOGIC DROPDOWN (YANG DIPERBAIKI)
function setupDropdownLogic() {
    try {
        const dataElement = document.getElementById('data-peralatan-source');
        if(!dataElement) return;
        
        const dataPeralatan = JSON.parse(dataElement.textContent);
        const selectPekerjaan = document.getElementById('selectPekerjaan');
        
        selectPekerjaan.addEventListener('change', () => {
            const pid = selectPekerjaan.value;
            const dropdown = document.getElementById('selectPeralatan');
            const manual = document.getElementById('inputPeralatan');
            const icon = document.getElementById('iconSelectPeralatan');
            
            // Reset
            dropdown.innerHTML = '<option value="">- Pilih Alat -</option>';
            
            // Logic: ID 1 (K3) & 2 (Laik Operasi) pakai Dropdown
            if (pid == "1" || pid == "2") {
                dropdown.classList.remove('d-none'); 
                if(icon) icon.classList.remove('d-none');
                
                manual.classList.add('d-none'); 
                manual.classList.remove('target-input'); // Biar gak bisa di-klik OCR
                
                // --- PERBAIKAN UTAMA DI SINI ---
                // Menggunakan 'id_pekerjaan' (bukan pekerjaan_id)
                const filtered = dataPeralatan.filter(i => i.id_pekerjaan == pid);
                
                filtered.forEach(i => {
                    dropdown.add(new Option(i.nama_peralatan, i.nama_peralatan));
                });
                
            } else if(pid) {
                // Kategori Lain -> Manual Input
                dropdown.classList.add('d-none'); 
                if(icon) icon.classList.add('d-none');
                
                manual.classList.remove('d-none'); 
                manual.classList.add('target-input'); // Bisa di-klik OCR
            } else {
                // Belum pilih
                dropdown.classList.add('d-none'); 
                if(icon) icon.classList.add('d-none');
                manual.classList.add('d-none');
            }
        });
    } catch(e) { console.error("Gagal setup dropdown:", e); }
}

// 2. SETUP INPUT FOCUS (Agar tahu kolom mana yang mau diisi OCR)
function setupInputFocusListener() {
    document.body.addEventListener('click', (e) => {
        if (e.target.classList.contains('target-input')) {
            activeInput = e.target;
            // Hapus highlight dari input lain
            document.querySelectorAll('.target-input').forEach(i => i.classList.remove('active-target'));
            // Highlight input yang aktif
            e.target.classList.add('active-target');
        }
    });
}

// 3. AUTOFILL EMAIL PERUSAHAAN
// Sama persis logicnya kayak di tambah_alat.js -- begitu nama perusahaan yang
// keisi (baik diketik manual, dipilih dari datalist, MAUPUN diisi lewat klik
// OCR) cocok persis sama salah satu yang udah ada di database, email-nya
// otomatis keisi juga.
function setupPerusahaanAutofill() {
    const dataPerusahaanEl = document.getElementById('data-perusahaan-source');
    const dataPerusahaan = dataPerusahaanEl ? JSON.parse(dataPerusahaanEl.textContent) : [];
    const inputNamaPerusahaan = document.getElementById('inputNamaPerusahaan');
    const inputEmailPerusahaan = document.getElementById('inputEmailPerusahaan');
    const hintEmailPerusahaan = document.getElementById('hintEmailPerusahaan');
    const hintDefaultText = hintEmailPerusahaan ? hintEmailPerusahaan.innerText : '';

    if (!inputNamaPerusahaan || !inputEmailPerusahaan) return;

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
            inputEmailPerusahaan.style.backgroundColor = '';
            inputEmailPerusahaan.style.borderColor = '';
            if (hintEmailPerusahaan) hintEmailPerusahaan.innerText = hintDefaultText;
        }
    }

    inputNamaPerusahaan.addEventListener('input', coba_autofill_email_perusahaan);
    coba_autofill_email_perusahaan();
}