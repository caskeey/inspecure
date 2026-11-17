/* Navigasi, zoom, dan indikator halaman di Smart Input OCR. */
var currentZoom = 1.0;

htmxReady(() => {
    setupControls();
    setupScrollTracking();
});

// KONTROL ZOOM & NAVIGASI HALAMAN
function setupControls() {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const zoomIn = document.getElementById('zoomIn');
    const zoomOut = document.getElementById('zoomOut');

    // Prev/Next tinggal loncat (scroll) ke blok halaman terkait, karena semua
    // halaman sudah dirender & bisa discroll langsung (`pageBlocks` dari
    // input_ocr_render.js).
    if(prevBtn) prevBtn.addEventListener('click', () => { if(pageNum > 1) { pageNum--; scrollToPage(pageNum); } });
    if(nextBtn) nextBtn.addEventListener('click', () => { if(pageNum < pageBlocks.length) { pageNum++; scrollToPage(pageNum); } });
    if(zoomIn) zoomIn.addEventListener('click', () => { currentZoom += 0.2; applyZoomAll(); });
    if(zoomOut) zoomOut.addEventListener('click', () => { if(currentZoom > 0.4) { currentZoom -= 0.2; applyZoomAll(); } });
}

function scrollToPage(num) {
    const block = pageBlocks[num - 1];
    if (block) block.wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Zoom diterapkan ke semua halaman sekaligus biar konsisten
function applyZoomAll() {
    const indicator = document.getElementById('zoomIndicator');
    if (indicator) indicator.innerText = Math.round(currentZoom * 100) + "%";

    pageBlocks.forEach((block, idx) => {
        const imgEl = block.img;
        if (imgEl && imgEl.naturalWidth > 0) {
            const newWidth = imgEl.naturalWidth * currentZoom;
            imgEl.style.width = newWidth + "px";
            imgEl.style.maxWidth = "none";

            // Gambar ulang box OCR sesuai skala baru (kalau halaman ini sudah pernah di-OCR)
            if (pageWordsCache[idx]) {
                renderBoxesForPage(block, pageWordsCache[idx]); // dari input_ocr_tesseract.js
            }
        }
    });
}

// Deteksi halaman mana yang lagi keliatan pas discroll, buat update indikator "Page X/Y"
function setupScrollTracking() {
    const viewport = document.querySelector('.ocr-viewport');
    if (!viewport) return;

    viewport.addEventListener('scroll', () => {
        if (!pageBlocks.length) return;
        const viewportTop = viewport.getBoundingClientRect().top;

        let closestIdx = 0;
        let closestDist = Infinity;
        pageBlocks.forEach((block, i) => {
            const dist = Math.abs(block.wrapper.getBoundingClientRect().top - viewportTop);
            if (dist < closestDist) { closestDist = dist; closestIdx = i; }
        });

        pageNum = closestIdx + 1;
        updatePageIndicator();
    });
}

function updatePageIndicator() {
    const total = pageBlocks.length;
    const ind = document.getElementById('pageIndicator');
    if(ind) ind.innerText = `Page ${total ? pageNum : 0} / ${total}`;
}
