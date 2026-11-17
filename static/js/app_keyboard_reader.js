// === LOGIC RFID/NFC READER (Keyboard-emulator: BLE HID / USB) ===
// Reader mengetik UID + Enter seperti keyboard. Burst UID dikenali dari jeda
// antar karakter yang singkat, termasuk saat kolom input sedang fokus.
// Listener ini nempel ke `document` itu sendiri (bukan elemen yang ikut
// di-swap), dan file ini cuma jalan sekali -> aman didaftarkan sekali di sini,
// gak akan pernah numpuk/dobel walau kamu pindah halaman berkali-kali.
let nfcBuffer = "";
let lastKeyTime = 0;
const READER_KEY_GAP_MS = 160;

document.addEventListener('keydown', (e) => {
    const char = e.key;
    if (typeof char !== 'string' || e.ctrlKey || e.altKey || e.metaKey) return;

    const target = e.target;
    const tag = target?.tagName;
    const isEditableField = tag === 'INPUT' || tag === 'TEXTAREA' ||
        tag === 'SELECT' || target?.isContentEditable;

    const currentTime = Date.now();

    if (char === 'Enter') {
        const uid = nfcBuffer.replace(/[^a-z0-9]/gi, '');
        if (uid.length > 5) {
            e.preventDefault();
            e.stopPropagation();
            if (isEditableField && typeof target.value === 'string' && target.value.endsWith(nfcBuffer)) {
                target.value = target.value.slice(0, -nfcBuffer.length);
                target.dispatchEvent(new Event('input', { bubbles: true }));
            }
            handleNfcScan(uid);
        }
        nfcBuffer = "";
        lastKeyTime = 0;
        return;
    }

    if (char.length === 1 && /^[a-z0-9:-]$/i.test(char)) {
        if (lastKeyTime && currentTime - lastKeyTime > READER_KEY_GAP_MS) {
            nfcBuffer = "";
        }
        nfcBuffer += char;
        lastKeyTime = currentTime;
    } else if (!['Shift', 'CapsLock', 'Control', 'Alt', 'Meta'].includes(char)) {
        nfcBuffer = "";
        lastKeyTime = 0;
    }
}, true);
