/* Pemilihan kata OCR dengan klik atau drag. */

// DRAG-SELECT KATA HASIL OCR
// Drag-select untuk ambil BEBERAPA kata sekaligus (bukan cuma 1 kata per klik).
// Klik biasa (tanpa geser) tetap berfungsi seperti sebelumnya: isi 1 kata saja.
// Klik+geser (drag) akan mengambil semua kata yang tersentuh kotak seleksi,
// diurutkan sesuai urutan baca (atas ke bawah, kiri ke kanan), lalu digabung
// dengan spasi ke kolom input yang sedang aktif (`activeInput`, dari
// input_ocr_form.js).
function setupWordSelection(layer) {
    if (layer.dataset.selectionReady) return; // pasang listener sekali saja per layer
    layer.dataset.selectionReady = '1';

    let dragging = false;
    let startX = 0, startY = 0;
    let selectionBox = null;

    const getLocalPoint = (e) => {
        const rect = layer.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const wordsInRect = (rect) => {
        return Array.from(layer.querySelectorAll('.ocr-word')).filter(w => {
            const l = parseFloat(w.style.left), t = parseFloat(w.style.top);
            const wd = parseFloat(w.style.width), ht = parseFloat(w.style.height);
            const r = l + wd, b = t + ht;
            return l < rect.right && r > rect.left && t < rect.bottom && b > rect.top;
        });
    };

    const wordAtPoint = (x, y) => {
        return Array.from(layer.querySelectorAll('.ocr-word')).find(w => {
            const l = parseFloat(w.style.left), t = parseFloat(w.style.top);
            const wd = parseFloat(w.style.width), ht = parseFloat(w.style.height);
            return x >= l && x <= l + wd && y >= t && y <= t + ht;
        });
    };

    const sortReadingOrder = (arr) => {
        arr.sort((a, b) => {
            const ta = parseFloat(a.style.top), tb = parseFloat(b.style.top);
            const ha = parseFloat(a.style.height) || 0;
            // Anggap satu "baris" kalau selisih top masih di bawah setengah tinggi kata
            if (Math.abs(ta - tb) > Math.max(8, ha * 0.6)) return ta - tb;
            return parseFloat(a.style.left) - parseFloat(b.style.left);
        });
        return arr;
    };

    const fillActiveInput = (words) => {
        if (!words.length) return;
        if (!activeInput) {
            alert("Klik dulu kolom input di sebelah kiri!");
            return;
        }
        const text = sortReadingOrder(words)
            .map(w => w.dataset.text)
            .join(' ')
            .replace(/[^a-zA-Z0-9\-\.\/\s]/g, "");
        activeInput.value = text;
        // Trigger event 'input' manual -- soalnya set .value langsung lewat JS
        // gak otomatis mancing listener kayak addEventListener('input', ...).
        // Ini penting biar misal field "Perusahaan" diisi lewat klik OCR
        // (bukan diketik manual), autofill email perusahaan (di
        // input_ocr_form.js) tetap kepicu.
        activeInput.dispatchEvent(new Event('input', { bubbles: true }));
        activeInput.style.borderColor = "#10B981";
        setTimeout(() => activeInput.style.borderColor = "", 500);

        layer.querySelectorAll('.ocr-word.selected').forEach(w => w.classList.remove('selected'));
        words.forEach(w => w.classList.add('selected'));
    };

    // FIX "ngadat": dulu mousemove/mouseup ini didaftarkan langsung ke
    // `window` di sini. Karena setupWordSelection() ikut jalan ulang tiap
    // kali halaman Smart Input dibuka lewat navigasi htmx (bukan cuma
    // sekali), listener numpuk terus tiap kunjungan -- makin sering
    // bolak-balik, makin banyak listener zombie yang nunjuk ke `layer`
    // lama & bikin drag-select kerasa berat/nyangkut, sampai di-refresh.
    // Sekarang logic-nya cuma disimpan sebagai fungsi biasa, didaftarkan ke
    // `window` lewat listener global yang di-guard (lihat bawah file),
    // jadi cuma ada SATU mousemove & SATU mouseup listener seumur tab.
    const onDragMove = (e) => {
        if (!dragging || !selectionBox) return;
        const p = getLocalPoint(e);
        const left = Math.min(startX, p.x);
        const top = Math.min(startY, p.y);
        const width = Math.abs(p.x - startX);
        const height = Math.abs(p.y - startY);
        selectionBox.style.left = left + 'px';
        selectionBox.style.top = top + 'px';
        selectionBox.style.width = width + 'px';
        selectionBox.style.height = height + 'px';
    };

    const onDragEnd = (e) => {
        if (!dragging) return;
        dragging = false;

        const p = getLocalPoint(e);
        const dist = Math.hypot(p.x - startX, p.y - startY);

        if (selectionBox) { selectionBox.remove(); selectionBox = null; }

        if (dist < 4) {
            // Dianggap klik biasa -> isi 1 kata saja (perilaku lama, tetap dipertahankan)
            const w = wordAtPoint(p.x, p.y);
            if (w) fillActiveInput([w]);
        } else {
            const rect = {
                left: Math.min(startX, p.x), right: Math.max(startX, p.x),
                top: Math.min(startY, p.y), bottom: Math.max(startY, p.y)
            };
            fillActiveInput(wordsInRect(rect));
        }

        window.__ocrActiveDrag = null;
    };

    layer.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        const p = getLocalPoint(e);
        startX = p.x; startY = p.y;
        dragging = true;

        selectionBox = document.createElement('div');
        selectionBox.className = 'ocr-selection-box';
        selectionBox.style.left = startX + 'px';
        selectionBox.style.top = startY + 'px';
        selectionBox.style.width = '0px';
        selectionBox.style.height = '0px';
        layer.appendChild(selectionBox);

        // Kasih tau listener window mana yang lagi aktif drag-nya sekarang.
        window.__ocrActiveDrag = { onDragMove, onDragEnd };

        e.preventDefault();
    });
}

// Listener window untuk drag-select didaftarkan SEKALI SAJA seumur tab
// (guard lewat window.__ocrDragBound), lalu didelegasikan ke drag handler
// milik layer yang sedang aktif lewat window.__ocrActiveDrag. Ini yang
// mencegah listener numpuk tiap kali halaman ini dibuka ulang via htmx.
if (!window.__ocrDragBound) {
    window.__ocrDragBound = true;
    window.addEventListener('mousemove', (e) => {
        if (window.__ocrActiveDrag) window.__ocrActiveDrag.onDragMove(e);
    });
    window.addEventListener('mouseup', (e) => {
        if (window.__ocrActiveDrag) window.__ocrActiveDrag.onDragEnd(e);
    });
}
