htmxReady(() => {
    // Reset currentDt ke tanggal HARI INI setiap kali halaman dashboard ini
    // dibuka -- baik pas load pertama maupun tiap kunjungan ulang lewat SPA.
    // WAJIB diisi di sini, PALING ATAS callback ini, sebelum initCalendar()
    // dipanggil -- soalnya pas navigasi SPA, htmxReady menjalankan callback
    // ini SECARA LANGSUNG/SYNCHRONOUS, jadi baris-baris di bawah titik ini
    // di file (kayak dulu assignment currentDt ada di sini) belum tentu
    // sempat kejalanin duluan.
    currentDt = new Date();

    // 1. UPDATE TANGGAL HEADER
    const dateEl = document.getElementById('currentDateDisplay');
    if(dateEl) {
        // Format bahasa Indonesia yang lengkap
        dateEl.innerText = new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    }

    // 2. LOAD DATA & CALENDAR
    let events = [];
    try {
        const raw = document.getElementById('calendar-data')?.textContent;
        if(raw) events = JSON.parse(raw);
    } catch(e) {
        console.error("Error parsing calendar data", e);
    }

    initCalendar(events);

    // 3. MODAL HANDLER
    const form = document.getElementById('addEventForm');
    if(form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.innerText;
            btn.innerText = "Menyimpan...";
            
            fetch('/add_event', { method: 'POST', body: new FormData(form) })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    location.reload();
                } else { 
                    alert(data.msg || "Gagal menyimpan"); 
                    btn.innerText = originalText; 
                }
            })
            .catch(err => {
                alert("Terjadi kesalahan koneksi");
                btn.innerText = originalText;
            });
        });
    }

    // Fungsi Global untuk diakses dari onClick HTML
    window.openEventModal = () => document.getElementById('eventModal').classList.add('active');
    window.closeEventModal = () => document.getElementById('eventModal').classList.remove('active');
});
