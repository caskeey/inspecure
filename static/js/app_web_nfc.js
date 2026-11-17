// === LOGIC NFC HP (Web NFC / NDEFReader) ===
if ('NDEFReader' in window && window.isSecureContext) {
    startGlobalWebNfc();
}

async function startGlobalWebNfc() {
    try {
        const ndef = new NDEFReader();
        await ndef.scan();
        ndef.onreading = (event) => {
            const uid = (event.serialNumber || '').toUpperCase();
            if (uid) handleNfcScan(uid);
        };
        ndef.onreadingerror = () => {
            console.warn('Gagal membaca kartu NFC, coba tempel ulang.');
        };
    } catch (err) {
        console.warn('Web NFC belum aktif:', err.message);
    }
}

// Anti "nimpah" hasil scan ganda dalam waktu singkat.
let __lastScanUid = null;
let __lastScanTime = 0;
let __lastScannedUid = '';
const __SCAN_COOLDOWN_MS = 2500;

function handleNfcScan(uid) {
    // Normalisasi format UID: BLE keyboard ngirim "B117D806",
    // Web NFC (event.serialNumber) ngirim "b1:17:d8:06" -> disamain jadi "B117D806"
    uid = uid.replace(/:/g, '').toUpperCase();

    const now = Date.now();
    if (uid === __lastScanUid && (now - __lastScanTime) < __SCAN_COOLDOWN_MS) {
        console.log("Scan diabaikan (duplikat dalam jeda singkat):", uid);
        return;
    }
    __lastScanUid = uid;
    __lastScanTime = now;
    __lastScannedUid = uid;

    // UID sudah lengkap diterima (BLE keyboard maupun NFC HP): tutup modal scan
    // supaya popup hasil yang muncul sesudah respons API tidak tertutup olehnya.
    const scanModal = document.getElementById('btScanModal');
    if (scanModal && scanModal.classList.contains('active')) closeBtModal();

    console.log("Scan Detected:", uid);
    requestScanDetail(uid);
}

function requestScanDetail(uid) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    fetch(`/api/scan_detail/${encodeURIComponent(uid)}`, { signal: controller.signal })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (data.status === 'found') {
                showScanResultPopup(data.data);
            } else if (data.status === 'not_found') {
                showScanNotFoundPopup(uid);
            } else {
                throw new Error('Respons server tidak dikenali');
            }
        })
        .catch(err => {
            console.error("Error scan:", err);
            let message = 'Terjadi gangguan saat menghubungi server. Periksa koneksi, lalu coba lagi.';
            if (err.name === 'AbortError') message = 'Server terlalu lama merespons. Periksa koneksi, lalu coba lagi.';
            else if (navigator.onLine === false) message = 'Perangkat sedang offline. Sambungkan ke internet, lalu coba lagi.';
            else if (/HTTP 401|HTTP 403/.test(err.message)) message = 'Sesi login berakhir. Silakan masuk kembali, lalu scan ulang.';
            showScanErrorPopup(message);
        })
        .finally(() => clearTimeout(timeoutId));
}

function retryLastNfcScan() {
    if (__lastScannedUid) requestScanDetail(__lastScannedUid);
}

function resetScanResultViews(title) {
    ['scanContent', 'scanNotFoundContent', 'scanErrorContent'].forEach((id) => {
        const section = document.getElementById(id);
        if (section) section.style.display = 'none';
    });
    const heading = document.getElementById('scanModalTitle');
    if (heading) heading.innerText = title;
}

function showScanResultPopup(item) {
    const modal = document.getElementById('scanResultModal');
    if (!modal) {
        console.error('Modal hasil scan tidak ditemukan di halaman ini.');
        return;
    }
    resetScanResultViews('Detail Aset');
    const content = document.getElementById('scanContent');
    if (content) content.style.display = 'block';

    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.innerText = value;
    };
    setText('d-nama', item.nama_alat || '-');
    setText('d-sn', item.nomor_serial || '-');
    setText('d-pt', item.nama_perusahaan || '-');

    const statusEl = document.getElementById('d-status');
    const status = item.status_sertifikasi || '-';
    if (statusEl) {
        statusEl.innerText = status;
        statusEl.className = 'status-badge ' + (status === 'Aktif' ? 'green' : status === 'Expired' ? 'red' : 'orange');
    }

    setText('d-exp', item.tgl_expired || '-');

    const idAlat = item.id_alat || item.id;
    document.getElementById('btn-detail').href = `/detail/${idAlat}`;
    const btnEdit = document.getElementById('btn-edit');       // hanya ada untuk Admin
    if (btnEdit) btnEdit.href = `/edit_alat/${idAlat}`;
    const formDelete = document.getElementById('form-delete'); // hanya ada untuk Admin
    if (formDelete) formDelete.action = `/hapus_alat/${idAlat}`;

    modal.classList.add('active');
}

function showScanNotFoundPopup(uid) {
    const modal = document.getElementById('scanResultModal');
    if (!modal) {
        window.alert(`UID ${uid} belum terdaftar.`);
        return;
    }
    resetScanResultViews('Hasil Scan');
    const content = document.getElementById('scanNotFoundContent');
    if (content) content.style.display = 'block';

    const uidElement = document.getElementById('nf-uid');
    if (uidElement) uidElement.innerText = uid;
    const btnDaftar = document.getElementById('btn-daftar-baru'); // hanya ada untuk Admin
    if (btnDaftar) btnDaftar.href = `/tambah_alat?uid=${encodeURIComponent(uid)}`;

    modal.classList.add('active');
}

function showScanErrorPopup(message) {
    const modal = document.getElementById('scanResultModal');
    if (!modal) {
        window.alert(message);
        return;
    }
    resetScanResultViews('Koneksi Bermasalah');
    const content = document.getElementById('scanErrorContent');
    const messageElement = document.getElementById('scanErrorMessage');
    if (content) content.style.display = 'block';
    if (messageElement) messageElement.innerText = message;
    modal.classList.add('active');
}

function closeScanModal() {
    const modal = document.getElementById('scanResultModal');
    if (modal) modal.classList.remove('active');
}
