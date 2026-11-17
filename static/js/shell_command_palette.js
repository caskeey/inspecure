(function () {
    'use strict';

    function initPalette() {
        const root = document.getElementById('cmdk');
        const input = document.getElementById('cmdkInput');
        const list = document.getElementById('cmdkList');
        const openBtn = document.getElementById('cmdkOpen');
        if (!root || !input || !list) return;

        let items = [], shown = [], active = 0, lastFocus = null;

        function collect() {
            items = [];
            document.querySelectorAll('.sidebar .menu-item').forEach(a => {
                const label = (a.querySelector('.link-text') || a).textContent.trim();
                const icon = a.querySelector('i');
                if (!label || !a.getAttribute('href')) return;
                items.push({ label, href: a.getAttribute('href'), icon: icon ? icon.className : 'ph-bold ph-file', hint: 'Halaman' });
            });
            items.push({ label: 'Buka / tutup sidebar', action: () => window.toggleSidebar && window.toggleSidebar(), icon: 'ph-bold ph-sidebar-simple', hint: 'Aksi' });
            items.push({ label: 'Lebar halaman: normal / penuh', action: () => document.getElementById('widthToggle')?.click(), icon: 'ph-bold ph-arrows-out-line-horizontal', hint: 'Aksi' });
            if (typeof window.openBtModal === 'function') {
                items.push({ label: 'Scan Portable RFID/NFC (modal)', action: () => window.openBtModal(), icon: 'ph-bold ph-scan', hint: 'Aksi' });
            }
        }

        function render() {
            const q = input.value.trim().toLowerCase();
            shown = items.filter(it => !q || it.label.toLowerCase().includes(q));
            active = Math.min(active, Math.max(shown.length - 1, 0));
            list.innerHTML = '';
            if (!shown.length) {
                const li = document.createElement('li');
                li.className = 'cmdk-empty';
                li.textContent = 'Tidak ada hasil';
                list.appendChild(li);
                return;
            }
            shown.forEach((it, i) => {
                const li = document.createElement('li');
                li.className = 'cmdk-item' + (i === active ? ' active' : '');
                li.setAttribute('role', 'option');
                li.innerHTML = '<i class="' + it.icon + '"></i><span class="cmdk-label"></span><span class="cmdk-hint"></span>';
                li.querySelector('.cmdk-label').textContent = it.label;
                li.querySelector('.cmdk-hint').textContent = it.hint;
                li.addEventListener('mousemove', () => { active = i; mark(); });
                li.addEventListener('click', () => run(it));
                list.appendChild(li);
            });
        }
        function mark() {
            [...list.children].forEach((li, i) => li.classList.toggle('active', i === active));
            const el = list.children[active]; if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
        }
        function run(it) {
            close();
            if (it.action) it.action(); else if (it.href) window.location.href = it.href;
        }
        function open() {
            lastFocus = document.activeElement;
            collect(); input.value = ''; active = 0; render();
            root.hidden = false;
            requestAnimationFrame(() => root.classList.add('show'));
            input.focus();
        }
        function close() {
            root.classList.remove('show'); root.hidden = true;
            if (lastFocus && lastFocus.focus) lastFocus.focus();
        }

        input.addEventListener('input', () => { active = 0; render(); });
        input.addEventListener('keydown', e => {
            if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, shown.length - 1); mark(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); mark(); }
            else if (e.key === 'Enter') { e.preventDefault(); if (shown[active]) run(shown[active]); }
            else if (e.key === 'Escape') { e.preventDefault(); close(); }
        });
        root.addEventListener('mousedown', e => { if (e.target === root) close(); });
        if (openBtn) openBtn.addEventListener('click', open);
        document.addEventListener('keydown', e => {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
                e.preventDefault(); root.hidden ? open() : close();
            }
        });
    }

    initPalette();
})();
