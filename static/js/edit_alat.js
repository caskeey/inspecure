/* static/js/edit_alat.js */

htmxReady(function() {
    // 1. Update Dropdown sesuai data DB saat load
    updatePeralatan(true);
    
    // 2. Hitung expired awal (berdasarkan data DB)
    hitungExpired();

    // 3. Autofill email perusahaan tiap kali dropdown perusahaan diganti
    const selectPerusahaan = document.getElementById('selectPerusahaan');
    const inputEmailPerusahaan = document.getElementById('inputEmailPerusahaan');
    if (selectPerusahaan && inputEmailPerusahaan) {
        selectPerusahaan.addEventListener('change', () => {
            const opt = selectPerusahaan.selectedOptions[0];
            const email = opt ? (opt.dataset.email || '') : '';
            inputEmailPerusahaan.value = email;
            inputEmailPerusahaan.style.backgroundColor = '#EEF2FF';
            inputEmailPerusahaan.style.borderColor = '#4F46E5';
        });
    }
});

// FUNGSI HITUNG EXPIRED
function hitungExpired() {
    const tglSertif = document.getElementById('tglSertif').value;
    const durasi = parseInt(document.getElementById('durasiAngka').value);
    const satuan = document.getElementById('durasiSatuan').value;
    const output = document.getElementById('viewExpired');
    const container = document.querySelector('.expired-display');
    
    if (tglSertif && durasi > 0) {
        const date = new Date(tglSertif);
        
        if (satuan === 'Tahun') {
            date.setFullYear(date.getFullYear() + durasi);
        } else if (satuan === 'Bulan') {
            date.setMonth(date.getMonth() + durasi);
        }
        
        // Format Tanggal Indonesia
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        output.value = date.toLocaleDateString('id-ID', options);
        
        // Visual Feedback (Warna Kuning/Orange untuk mode Edit)
        output.style.color = "#B45309";
        if(container) {
            container.style.borderColor = "#F59E0B";
            container.style.background = "#FFFBEB";
        }
    } else {
        output.value = "";
        output.style.color = "#64748B";
        if(container) {
            container.style.borderColor = "#E2E8F0";
            container.style.background = "white";
        }
    }
}

function updatePeralatan(isFirstLoad = false) {
    try {
        const dataElement = document.getElementById('data-peralatan-source');
        if(!dataElement) return;
        const dataPeralatan = JSON.parse(dataElement.textContent);
        
        const pekerjaanId = document.getElementById('selectPekerjaan').value;
        const dropdown = document.getElementById('selectPeralatan');
        const manualInput = document.getElementById('inputPeralatan');
        const iconSelect = document.getElementById('iconSelectPeralatan');
        const oldValue = document.getElementById('oldJenisAlat').value;

        dropdown.innerHTML = '<option value="">-- Pilih Alat --</option>';

        // Logic: ID 1 & 2 Pakai Dropdown
        if (pekerjaanId == "1" || pekerjaanId == "2") {
            dropdown.classList.remove('d-none');
            iconSelect.classList.remove('d-none');
            manualInput.classList.add('d-none');
            
            manualInput.required = false;
            dropdown.required = true;
            
            const filtered = dataPeralatan.filter(item => item.id_pekerjaan == pekerjaanId);
            
            filtered.forEach(item => {
                const option = document.createElement('option');
                option.value = item.nama_peralatan;
                option.textContent = item.nama_peralatan;
                
                // Auto Select Data Lama
                if (isFirstLoad && item.nama_peralatan === oldValue) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });

        } else {
            // ID Lain Pakai Input Manual
            dropdown.classList.add('d-none');
            iconSelect.classList.add('d-none');
            manualInput.classList.remove('d-none');
            
            dropdown.required = false;
            manualInput.required = true;
            
            if (isFirstLoad) {
                manualInput.value = oldValue;
            }
        }
    } catch(e) { console.error(e); }
}