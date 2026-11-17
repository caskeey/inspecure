// === MODAL: PAIRING BLUETOOTH (buka/tutup) ===
function openBtModal() {
    const modal = document.getElementById('btScanModal');
    if (modal) modal.classList.add('active');
}
function closeBtModal() {
    const modal = document.getElementById('btScanModal');
    if (modal) modal.classList.remove('active');
    stopModalNfcScan();
}

function startReaderScan() {
    const button = document.getElementById('modalReaderBtn');
    if (button) {
        button.classList.add('scanning');
        button.innerHTML = '<i class="ph-bold ph-spinner-gap"></i> Menunggu RFID/BLE...';
    }
    setModalNfcStatus('Tempelkan tag atau tekan tombol scan pada reader RFID/BLE sekarang.', 'info');
    const active = document.activeElement;
    if (active && active !== document.body && typeof active.blur === 'function') active.blur();
}

// === LOGIC NFC HP DI DALAM MODAL "SCAN PORTABLE" ===
let modalNfcAbortController = null;

function setModalNfcStatus(text, type) {
    const el = document.getElementById('modalNfcStatus');
    if (!el) return;
    el.innerText = text;
    el.className = 'nfc-modal-status show ' + (type || 'info');
}

async function startModalNfcScan() {
    const btn = document.getElementById('modalNfcBtn');

    if (!('NDEFReader' in window)) {
        setModalNfcStatus('Browser/perangkat ini belum support Web NFC. Pakai Chrome di Android, atau pakai reader Bluetooth di atas.', 'error');
        return;
    }
    if (!window.isSecureContext) {
        setModalNfcStatus('Halaman harus diakses lewat HTTPS supaya NFC bisa dipakai.', 'error');
        return;
    }

    try {
        if (btn) { btn.classList.add('scanning'); btn.disabled = true; btn.innerHTML = '<i class="ph-bold ph-wifi-high"></i> Menunggu tag...'; }
        setModalNfcStatus('Tempelkan kartu/tag ke bagian belakang HP sekarang.', 'info');

        modalNfcAbortController = new AbortController();
        const ndef = new NDEFReader();
        await ndef.scan({ signal: modalNfcAbortController.signal });

        ndef.onreading = (event) => {
            const uid = (event.serialNumber || '').toUpperCase();
            setModalNfcStatus(uid ? `Kartu terbaca: ${uid}` : 'Kartu terbaca.', 'success');
            if (uid) handleNfcScan(uid);
        };
        ndef.onreadingerror = () => {
            setModalNfcStatus('Gagal membaca kartu. Coba tempelkan ulang, posisinya jangan bergeser.', 'error');
        };
    } catch (err) {
        if (btn) { btn.classList.remove('scanning'); btn.disabled = false; btn.innerHTML = '<i class="ph-bold ph-wifi-high"></i> Scan pakai NFC HP'; }
        if (err.name === 'NotAllowedError') {
            setModalNfcStatus('Izin NFC ditolak. Aktifkan izin NFC untuk situs ini di pengaturan browser.', 'error');
        } else if (err.name === 'NotSupportedError' || err.name === 'NotReadableError') {
            setModalNfcStatus('NFC tidak tersedia di perangkat ini. Pastikan NFC di HP sudah aktif.', 'error');
        } else {
            setModalNfcStatus('Gagal memulai scan NFC: ' + err.message, 'error');
        }
    }
}

function stopModalNfcScan() {
    if (modalNfcAbortController) {
        modalNfcAbortController.abort();
        modalNfcAbortController = null;
    }
    const btn = document.getElementById('modalNfcBtn');
    if (btn) { btn.classList.remove('scanning'); btn.disabled = false; btn.innerHTML = '<i class="ph-bold ph-wifi-high"></i> Scan pakai NFC HP'; }
    const readerBtn = document.getElementById('modalReaderBtn');
    if (readerBtn) {
        readerBtn.classList.remove('scanning');
        readerBtn.disabled = false;
        readerBtn.innerHTML = '<i class="ph-bold ph-broadcast"></i> Scan dengan RFID/Bluetooth';
    }
    const el = document.getElementById('modalNfcStatus');
    if (el) el.className = 'nfc-modal-status';
}
