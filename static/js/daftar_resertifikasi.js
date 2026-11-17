/* Lookup an asset by RFID UID before starting recertification. */
htmxReady(function () {
    const uidInput = document.getElementById('uidInput');
    const loadingBox = document.getElementById('loadingBox');
    const resultCard = document.getElementById('resultCard');
    const notFoundCard = document.getElementById('notFoundCard');
    const byId = (id) => document.getElementById(id);

    if (!uidInput || !loadingBox || !resultCard || !notFoundCard) return;

    function resetCards() {
        loadingBox.style.display = 'none';
        resultCard.style.display = 'none';
        notFoundCard.style.display = 'none';
    }

    async function cariAlat() {
        const uid = uidInput.value.trim();
        if (!uid) return;

        resetCards();
        loadingBox.style.display = 'block';
        try {
            const response = await fetch(`/api/scan_detail/${encodeURIComponent(uid)}`);
            if (!response.ok) throw new Error('Permintaan pencarian gagal.');
            const data = await response.json();
            loadingBox.style.display = 'none';

            if (data.status === 'found') {
                const item = data.data;
                byId('rNama').value = item.nama_peralatan || item.nama_alat || '-';
                byId('rSerial').value = item.nomor_serial || '-';
                byId('rPerusahaan').value = item.nama_perusahaan || '-';
                byId('rStatus').value = item.status_sertifikasi || '-';
                byId('rTglSertif').value = item.tgl_sertifikasi || '-';
                byId('rTglExpired').value = item.tgl_expired || '-';
                byId('btnResertifikasi').href = `/resertifikasi_alat/${item.id_alat || item.id}`;
                resultCard.style.display = 'block';
                return;
            }

            byId('nfUid').textContent = uid;
            byId('btnDaftarBaru').href = `/tambah_alat?uid=${encodeURIComponent(uid)}`;
            notFoundCard.style.display = 'block';
        } catch (error) {
            loadingBox.style.display = 'none';
            window.alert('Gagal menghubungi server. Coba lagi.');
        }
    }

    byId('btnCari')?.addEventListener('click', cariAlat);
    uidInput.addEventListener('keydown', function (event) {
        event.stopPropagation();
        if (event.key === 'Enter') {
            event.preventDefault();
            cariAlat();
        }
    });
    uidInput.focus();
});
