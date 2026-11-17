/* static/js/app_shell.js
 * Navigasi sekarang full page reload biasa (htmx sudah dilepas), jadi
 * seluruh file ini dieksekusi ulang dari awal tiap kali pindah halaman --
 * itu normal dan aman, karena browser sendiri yang reset semua state JS
 * tiap reload. Listener yang nempel ke `document` (keydown NFC, dst) juga
 * otomatis ke-reset bersih setiap load, gak akan pernah numpuk.
 *
 * htmxReady() dipakai sebagai pembungkus init function -- fungsinya murni
 * sama dengan `DOMContentLoaded` biasa. Nama lama dipertahankan supaya
 * file JS per-halaman lain (tambah_alat.js, edit_alat.js, dst) gak perlu
 * diubah satu-satu. File ini dimuat di <head>, sedangkan script per-halaman
 * dimuat di akhir <body>, jadi fungsi ini pasti sudah tersedia untuk mereka.
 */

function htmxReady(fn) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fn);
    } else {
        fn();
    }
}

// === SIDEBAR TOGGLE (DESKTOP & MOBILE) ===
function toggleSidebar() {
    const s = document.getElementById('sidebar');
    if (!s) return;
    const icon = document.querySelector('.toggle-btn i');
    if (window.innerWidth <= 1024) {
        toggleMobileSidebar();
    } else {
        s.classList.toggle('collapsed');
        const closed = s.classList.contains('collapsed');
        if (icon) {
            icon.classList.toggle('ph-caret-right', closed);
            icon.classList.toggle('ph-caret-left', !closed);
        }
        try { localStorage.setItem('sidebarState', closed ? 'closed' : 'open'); } catch (e) {}
    }
    syncSidebarToggleAria();
}

// Dipanggil dari <div class="sidebar-header" onclick="expandSidebar()">.
// Dulu fungsi ini tidak pernah didefinisikan -> sidebar yang sudah
// collapsed tidak bisa dibuka lagi lewat klik header.
function expandSidebar() {
    const s = document.getElementById('sidebar');
    if (s && window.innerWidth > 1024 && s.classList.contains('collapsed')) toggleSidebar();
}

function syncSidebarToggleAria() {
    const s = document.getElementById('sidebar');
    if (!s) return;
    const open = window.innerWidth <= 1024 ? s.classList.contains('open') : !s.classList.contains('collapsed');
    document.querySelectorAll('[data-sidebar-toggle]').forEach(b => b.setAttribute('aria-expanded', String(open)));
}

// Pintasan keyboard ala Notion: Ctrl/Cmd + \
document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === '\\') { e.preventDefault(); toggleSidebar(); }
});

function toggleMobileSidebar() {
    const s = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    if (s) s.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
    syncSidebarToggleAria();
}

function initSidebarUiState() {
    let state = null;
    try { state = localStorage.getItem('sidebarState'); } catch (e) {}
    const icon = document.querySelector('.toggle-btn i');
    const sidebar = document.getElementById('sidebar');
    if (state === 'closed' && window.innerWidth > 1024 && sidebar) {
        // matikan transisi sesaat supaya tidak "menutup sendiri" saat halaman dibuka
        sidebar.style.transition = 'none';
        sidebar.classList.add('collapsed');
        if (icon) { icon.classList.remove('ph-caret-left'); icon.classList.add('ph-caret-right'); }
        requestAnimationFrame(() => requestAnimationFrame(() => { sidebar.style.transition = ''; }));
    }
    syncSidebarToggleAria();

    const topHeader = document.querySelector('.header-text');
    const existingBtn = document.querySelector('.mobile-menu-btn');
    if (topHeader && !existingBtn) {
        const btn = document.createElement('button');
        btn.className = 'mobile-menu-btn';
        btn.innerHTML = '<i class="ph-bold ph-list"></i>';
        btn.onclick = toggleMobileSidebar;
        const topBar = document.querySelector('.top-bar');
        if (topBar) topBar.insertBefore(btn, topBar.firstChild);
    }
}

// Modal backdrop (klik area luar modal buat nutup).
function initModalBackdrops() {
    const scanBackdrop = document.getElementById('scanResultModal');
    if (scanBackdrop && !scanBackdrop.dataset.boundClose) {
        scanBackdrop.dataset.boundClose = '1';
        scanBackdrop.addEventListener('click', (e) => { if (e.target === scanBackdrop) closeScanModal(); });
    }
    const btBackdrop = document.getElementById('btScanModal');
    if (btBackdrop && !btBackdrop.dataset.boundClose) {
        btBackdrop.dataset.boundClose = '1';
        btBackdrop.addEventListener('click', (e) => { if (e.target === btBackdrop) closeBtModal(); });
    }
}

function initGlobalUi() {
    initSidebarUiState();
    initModalBackdrops();
}
htmxReady(initGlobalUi);
