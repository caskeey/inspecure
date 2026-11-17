/* static/js/shell_preferences.js — lebar canvas, tema, dan cover
 * 1. Toggle lebar canvas (normal / penuh), tersimpan
 * 2. Ganti cover (jika halaman memakai cover)
 * Preferensi disimpan bersama shell_store.js. Sidebar toggle ada di app_shell.js.
 */
(function () {
    'use strict';

    const store = window.inspecureStore;

    /* ---------- 1. Lebar canvas ---------- */
    function initWidthToggle() {
        const btn = document.getElementById('widthToggle');
        if (!btn) return;
        const root = document.documentElement;
        const sync = () => {
            const full = root.classList.contains('canvas-pref-full');
            btn.setAttribute('aria-pressed', String(full));
            btn.title = full ? 'Lebar halaman: penuh (klik untuk normal)' : 'Lebar halaman: normal (klik untuk penuh)';
            const i = btn.querySelector('i');
            if (i) { i.className = 'ph-bold ' + (full ? 'ph-arrows-in-line-horizontal' : 'ph-arrows-out-line-horizontal'); }
        };
        btn.addEventListener('click', () => {
            root.classList.toggle('canvas-pref-full');
            store.set('canvasFull', root.classList.contains('canvas-pref-full') ? '1' : '0');
            sync();
        });
        sync();
    }

    /* ---------- Theme toggle ---------- */
    function initThemeToggle() {
        const btn = document.getElementById('themeToggle');
        if (!btn) return;
        const root = document.documentElement;
        const icon = document.getElementById('themeIcon');
        const label = document.getElementById('themeLabel');
        const sync = () => {
            const dark = root.getAttribute('data-theme') === 'dark';
            if (btn) btn.setAttribute('aria-pressed', String(dark));
            document.querySelectorAll('[data-theme-choice]').forEach(choice => {
                choice.setAttribute('aria-pressed', String(choice.dataset.themeChoice === (dark ? 'dark' : 'light')));
            });
            if (!btn && !document.querySelector('[data-theme-choice]')) return;
            if (!btn) return;
            btn.title = dark ? 'Ganti ke tema terang' : 'Ganti ke tema gelap';
            if (icon) icon.className = 'ph-bold ' + (dark ? 'ph-sun' : 'ph-moon');
            if (label) label.textContent = dark ? 'Gelap' : 'Terang';
        };
        const setTheme = next => {
            root.setAttribute('data-theme', next);
            store.set('theme', next);
            sync();
        };
        if (btn) btn.addEventListener('click', () => setTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));
        document.querySelectorAll('[data-theme-choice]').forEach(choice => {
            choice.addEventListener('click', () => setTheme(choice.dataset.themeChoice));
        });
        sync();
    }

    /* ---------- 2. Cover ---------- */
    function initCover() {
        const cover = document.getElementById('pageCover');
        const btn = document.getElementById('coverChange');
        if (!cover || !btn) return;
        const n = 4;
        let idx = parseInt(store.get('coverIdx', '0'), 10) || 0;
        cover.dataset.cover = idx % n;
        btn.addEventListener('click', () => {
            idx = (idx + 1) % n;
            cover.dataset.cover = idx;
            store.set('coverIdx', idx);
        });
    }


    function initPreferences() { initWidthToggle(); initThemeToggle(); initCover(); }
    initPreferences();
})();
