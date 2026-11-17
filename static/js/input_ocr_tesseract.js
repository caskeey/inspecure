/* static/js/input_ocr_tesseract.js
 * Tanggung jawab file ini CUMA: jalanin OCR (Tesseract) per halaman &
 * gambar kotak di atas tiap kata yang berhasil dibaca.
 * Gak ngurusin baca file/render halaman (itu di input_ocr_render.js).
 * Gak ngurusin drag-select/zoom (itu di input_ocr_selection.js / input_ocr_navigation.js).
 */

// Preprocessing gambar: grayscale + kontras ringan, biar teks lebih tajam sebelum di-OCR
function preprocessImage(imageUrl) {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);

            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imgData.data;
            for (let i = 0; i < data.length; i += 4) {
                // Grayscale
                const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
                // Kontras sederhana: gelapin yang gelap, terangin yang terang
                const val = gray < 150 ? gray * 0.7 : Math.min(255, gray * 1.2);
                data[i] = data[i + 1] = data[i + 2] = val;
            }
            ctx.putImageData(imgData, 0, 0);
            resolve(canvas.toDataURL('image/png'));
        };
        img.onerror = () => resolve(imageUrl); // fallback: kalau gagal preprocess, pakai gambar asli
        img.src = imageUrl;
    });
}

// Jalankan OCR untuk semua halaman SATU-SATU secara berurutan di background,
// tanpa nge-block scroll/preview. Tiap halaman dibaca utuh sekali proses (bukan per-baris/kata).
// `pageBlocks` & `pageWordsCache` datang dari input_ocr_render.js.
async function runOcrQueue() {
    const total = pageBlocks.length;
    for (let i = 0; i < total; i++) {
        await runTesseractForPage(pageBlocks[i], i, total);
    }
    hideQueueStatus();
}

function runTesseractForPage(block, idx, total) {
    return new Promise(async (resolve) => {
        showQueueStatus(`Memindai Halaman ${idx + 1}/${total}: 0%`);

        const processedUrl = await preprocessImage(block.img.src);

        Tesseract.recognize(
            processedUrl, 'ind+eng', // Bahasa Indonesia + Inggris
            { logger: m => {
                if (m.status === 'recognizing text') {
                    showQueueStatus(`Memindai Halaman ${idx + 1}/${total}: ${Math.round(m.progress * 100)}%`);
                }
            }}
        ).then(({ data: { words } }) => {
            pageWordsCache[idx] = words;
            renderBoxesForPage(block, words);
            resolve();
        }).catch(err => {
            console.error(err);
            resolve(); // tetap lanjut ke halaman berikutnya walau 1 halaman gagal
        });
    });
}

function showQueueStatus(text) {
    const el = document.getElementById('ocrQueueStatus');
    if (!el) return;
    el.style.display = 'flex';
    el.innerHTML = `<span class="mini-spinner"></span><span>${text}</span>`;
}

function hideQueueStatus() {
    const el = document.getElementById('ocrQueueStatus');
    if (el) el.style.display = 'none';
}

// Gambar 1 kotak per kata hasil OCR, diskalakan ke ukuran tampil gambar saat ini.
// Dipanggil juga dari input_ocr_selection.js / input_ocr_navigation.js tiap kali zoom berubah.
function renderBoxesForPage(block, words) {
    block.layer.innerHTML = '';
    const scale = block.img.width / block.img.naturalWidth;

    words.forEach(w => {
        const box = document.createElement('div');
        box.className = 'ocr-word';
        const b = w.bbox;
        box.style.left = (b.x0 * scale) + 'px';
        box.style.top = (b.y0 * scale) + 'px';
        box.style.width = ((b.x1 - b.x0) * scale) + 'px';
        box.style.height = ((b.y1 - b.y0) * scale) + 'px';
        box.title = w.text;
        box.dataset.text = w.text;
        // pointer-events dimatikan di CSS supaya drag-select di layer bisa jalan mulus;
        // deteksi kata dilakukan lewat koordinat, bukan lewat event per-box.
        block.layer.appendChild(box);
    });

    setupWordSelection(block.layer); // dari input_ocr_selection.js / input_ocr_navigation.js
}