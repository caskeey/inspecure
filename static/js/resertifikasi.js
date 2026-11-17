function kirimSatu(idPerusahaan, btnEl) {
    if (!confirm("Kirim email rekap resertifikasi untuk perusahaan ini sekarang?")) return;

    const originalHtml = btnEl.innerHTML;
    btnEl.disabled = true;
    btnEl.innerHTML = '<i class="ph-bold ph-spinner-gap" style="animation: spin 1s linear infinite;"></i> Mengirim...';

    fetch(`/resertifikasi/kirim/${idPerusahaan}`, { method: 'POST' })
        .then(res => res.json())
        .then(d => {
            alert(d.msg);
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
        })
        .catch(err => {
            alert("Terjadi kesalahan: " + err);
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
        });
}

// Guard: bagian di bawah ini (pasang listener klik + suntik <style> animasi
// spinner) cuma boleh jalan SEKALI seumur sesi browser, walau file ini
// re-eksekusi tiap kali halaman Resertifikasi dibuka ulang lewat navigasi
// SPA (htmx). Tanpa guard ini: listener klik numpuk (tombol "Kirim" bisa
// ngirim berkali-kali per klik), dan tag <style> ke-duplikat tiap kunjungan.
if (!window.__resertifikasiInited) {
    window.__resertifikasiInited = true;

    // Tombol "Kirim Email" per perusahaan (pakai data-id-perusahaan, bukan onclick inline,
    // biar gak ada sintaks Jinja {{ }} yang nyampur ke JS dan bikin editor bingung)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-kirim-satu');
        if (btn) {
            const idPerusahaan = btn.dataset.idPerusahaan;
            kirimSatu(idPerusahaan, btn);
        }
    });

    const styleSpin = document.createElement('style');
    styleSpin.innerHTML = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
    document.head.appendChild(styleSpin);
}

function jalankanSemua() {
    if (!confirm("Buat & kirim rekap resertifikasi ke SEMUA perusahaan yang terdampak sekarang?")) return;

    const btn = document.getElementById('btnKirimSemua');
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="ph-bold ph-spinner-gap" style="animation: spin 1s linear infinite;"></i> Memproses...';

    fetch('/resertifikasi/jalankan_semua', { method: 'POST' })
        .then(res => res.json())
        .then(d => {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            if (d.status === 'success') {
                let ringkasan = d.hasil.map(h =>
                    `- ${h.nama_perusahaan} (${h.jumlah_alat} alat): ${h.terkirim ? 'Terkirim' : 'Gagal - ' + h.pesan}`
                ).join('\n');
                alert("Selesai diproses:\n\n" + ringkasan);
                location.reload();
            } else {
                alert("Gagal: " + d.msg);
            }
        })
        .catch(err => {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            alert("Terjadi kesalahan: " + err);
        });
}