/* static/js/input_ocr_render.js
 * Tanggung jawab file ini CUMA: baca file yang diupload (PDF/gambar) &
 * render tiap halamannya ke layar (jadi bisa discroll semua sekaligus).
 * Gak ada logic OCR/Tesseract di sini -- itu di input_ocr_tesseract.js.
 * Gak ada logic zoom/drag-select -- itu di input_ocr_selection.js / input_ocr_navigation.js.
 *
 * File ini yang PEGANG variabel shared soal state halaman (pdfDoc, pageNum,
 * pageBlocks, pageWordsCache), makanya harus di-load PALING DULU dari
 * ketiga file "engine" (form.js tetap paling awal dari semuanya).
 */

// VARIABLES (dipakai bareng sama input_ocr_tesseract.js & input_ocr_selection.js / input_ocr_navigation.js)
// Sengaja pakai `var` (bukan `let`) buat semua variabel di bawah ini.
// `var` aman & otomatis ke-reset ke nilai awal tiap kunjungan halaman
// (perilaku yang memang kita mau).
var pdfDoc = null;
var pageNum = 1;               // halaman yang lagi "aktif" (dipakai indikator & tombol prev/next)
var pageBlocks = [];           // [{ wrapper, img, layer, num }] untuk tiap halaman
var pageWordsCache = [];       // hasil OCR per halaman (index sama dengan pageBlocks)

// Pastikan library PDF.js worker terload dengan benar sebelum dipakai --
// polling ringan sebagai jaga-jaga kalau <script src="pdf.min.js"> belum
// selesai dieksekusi di titik ini (mis. attribute defer/async di masa
// depan). Kalau langsung dipakai tanpa nunggu dan ternyata belum siap,
// bakal "Uncaught ReferenceError: pdfjsLib is not defined" dan itu bikin
// SISA SCRIPT INI (termasuk htmxReady(setupOCR) di bawah) ikut GAGAL
// dieksekusi -- jadi fitur upload/OCR keliatan mati total.
function initPdfWorkerWhenReady() {
    if (typeof pdfjsLib !== 'undefined') {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';
    } else {
        setTimeout(initPdfWorkerWhenReady, 50);
    }
}
initPdfWorkerWhenReady();

htmxReady(() => {
    setupOCR();
});

// SETUP: DENGERIN FILE YANG DIUPLOAD
function setupOCR() {
    const fileInput = document.getElementById('fileScan');
    const fileInfo = document.getElementById('fileInfo');

    const pagesContainer = document.getElementById('pages-container');
    const loading = document.getElementById('loadingOcr');
    const statusText = document.getElementById('statusOcr');
    const placeholder = document.getElementById('ocr-placeholder');
    const docPreview = document.getElementById('doc-preview');
    const docName = document.getElementById('doc-name');

    if(!fileInput) return;

    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        fileInfo.style.display = 'block';
        fileInfo.innerText = "File: " + file.name;

        // Reset UI
        pagesContainer.style.display = 'none';
        pagesContainer.innerHTML = '';
        pageBlocks = [];
        pageWordsCache = [];
        docPreview.style.display = 'none';
        placeholder.style.display = 'none';
        hideQueueStatus(); // dari input_ocr_tesseract.js

        loading.style.display = 'flex';
        statusText.innerText = "Membaca File...";

        if (file.type === 'application/pdf') {
            statusText.innerText = "Merender PDF...";
            const fileReader = new FileReader();
            fileReader.onload = async function() {
                try {
                    const typedarray = new Uint8Array(this.result);
                    pdfDoc = await pdfjsLib.getDocument(typedarray).promise;
                    pageNum = 1;

                    // Render SEMUA halaman langsung, biar bisa discroll semua sekaligus
                    await renderAllPdfPages();

                } catch (err) {
                    console.error(err);
                    alert("Gagal membaca PDF.");
                    loading.style.display = 'none';
                }
            };
            fileReader.readAsArrayBuffer(file);

        } else if (file.type.startsWith('image/')) {
            pdfDoc = null;
            pageNum = 1;

            const url = URL.createObjectURL(file);
            const block = await createPageBlock(url, 1);
            pagesContainer.appendChild(block.wrapper);
            pageBlocks = [block];
            pageWordsCache = [null];

            pagesContainer.style.display = 'flex';
            loading.style.display = 'none';
            updatePageIndicator();   // dari input_ocr_selection.js / input_ocr_navigation.js
            applyZoomAll();          // dari input_ocr_selection.js / input_ocr_navigation.js

            // 1 gambar = 1 halaman, langsung di-OCR utuh (bukan per-baris/per-kata)
            runOcrQueue();           // dari input_ocr_tesseract.js
        } else {
            loading.style.display = 'none';
            docPreview.style.display = 'block';
            docName.innerText = file.name;
        }
    });
}

// Render seluruh halaman PDF ke #pages-container (jadi bisa langsung discroll semua)
async function renderAllPdfPages() {
    const pagesContainer = document.getElementById('pages-container');
    const loading = document.getElementById('loadingOcr');
    const statusText = document.getElementById('statusOcr');
    const total = pdfDoc.numPages;

    for (let i = 1; i <= total; i++) {
        statusText.innerText = `Merender Halaman ${i}/${total}...`;
        const imgUrl = await renderPdfPageToDataUrl(i);
        const block = await createPageBlock(imgUrl, i);
        pagesContainer.appendChild(block.wrapper);
        pageBlocks.push(block);
        pageWordsCache.push(null);
    }

    pagesContainer.style.display = 'flex';
    loading.style.display = 'none';
    updatePageIndicator();   // dari input_ocr_selection.js / input_ocr_navigation.js
    applyZoomAll();          // dari input_ocr_selection.js / input_ocr_navigation.js

    // Setelah semua halaman tampil, baru OCR jalan di background per halaman
    // (bukan blocking UI, dan tetap 1 halaman penuh sekali proses, bukan per-baris)
    runOcrQueue();            // dari input_ocr_tesseract.js
}

// Render 1 halaman PDF ke canvas tersembunyi, hasilnya dataURL gambar
async function renderPdfPageToDataUrl(num) {
    const canvas = document.getElementById('pdf-render');
    const ctx = canvas.getContext('2d');

    const page = await pdfDoc.getPage(num);
    const scale = 2.0;
    const viewport = page.getViewport({ scale: scale });
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    await page.render({ canvasContext: ctx, viewport: viewport }).promise;
    return canvas.toDataURL('image/png');
}

// Bikin 1 blok halaman (label + gambar + layer OCR), return setelah gambar selesai dimuat
function createPageBlock(imgUrl, num) {
    return new Promise((resolve) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'page-block';

        const label = document.createElement('div');
        label.className = 'page-label';
        label.innerText = `Halaman ${num}`;

        const img = document.createElement('img');
        img.alt = `Halaman ${num}`;

        const layer = document.createElement('div');
        layer.className = 'page-ocr-layer';

        wrapper.appendChild(label);
        wrapper.appendChild(img);
        wrapper.appendChild(layer);

        img.onload = () => resolve({ wrapper, img, layer, num });
        img.onerror = () => resolve({ wrapper, img, layer, num });
        img.src = imgUrl;
    });
}