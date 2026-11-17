(function () {
    'use strict';

    const VIEW_META = {
        table:   { label: 'Table',   icon: 'ph-table' },
        list:    { label: 'List',    icon: 'ph-list-bullets' },
        gallery: { label: 'Gallery', icon: 'ph-squares-four' }
    };

    function labelCells(box) {
        box.querySelectorAll('table').forEach(t => {
            const heads = [...t.querySelectorAll('thead th')].map(th => th.textContent.trim());
            t.querySelectorAll('tbody tr').forEach(tr => {
                [...tr.children].forEach((td, i) => {
                    if (td.tagName === 'TD' && !td.hasAttribute('data-label') && heads[i]) td.setAttribute('data-label', heads[i]);
                });
            });
        });
    }

    function initDbViews() {
        document.querySelectorAll('.db-view').forEach(box => {
            if (box.dataset.ready) return;
            box.dataset.ready = '1';

            const views = (box.dataset.views || 'table,list,gallery').split(',').filter(v => VIEW_META[v]);
            const key = 'dbview:' + location.pathname + ':' + (box.dataset.key || '');
            let view = window.inspecureStore.get(key, box.dataset.view || 'table');
            if (!views.includes(view)) view = views[0];

            const bar = document.createElement('div');
            bar.className = 'db-toolbar';

            if (views.length > 1) {
                const seg = document.createElement('div');
                seg.className = 'db-seg'; seg.setAttribute('role', 'tablist');
                views.forEach(v => {
                    const b = document.createElement('button');
                    b.type = 'button'; b.dataset.v = v; b.setAttribute('role', 'tab');
                    b.innerHTML = '<i class="ph-bold ' + VIEW_META[v].icon + '"></i><span>' + VIEW_META[v].label + '</span>';
                    b.addEventListener('click', () => setView(v));
                    seg.appendChild(b);
                });
                bar.appendChild(seg);
            }

            let searchInput = null;
            if (box.dataset.search === '1') {
                const wrap = document.createElement('label');
                wrap.className = 'db-search';
                wrap.innerHTML = '<i class="ph-bold ph-magnifying-glass"></i><input type="search" placeholder="Cari di tabel…" aria-label="Cari di tabel">';
                searchInput = wrap.querySelector('input');
                bar.appendChild(wrap);
                searchInput.addEventListener('input', () => {
                    const q = searchInput.value.trim().toLowerCase();
                    box.querySelectorAll('tbody tr').forEach(tr => {
                        const hit = !q || tr.textContent.toLowerCase().includes(q);
                        tr.classList.toggle('db-hidden', !hit);
                    });
                });
            }

            box.insertBefore(bar, box.firstChild);

            function setView(v) {
                view = v; box.dataset.view = v; window.inspecureStore.set(key, v);
                bar.querySelectorAll('.db-seg button').forEach(b => {
                    const on = b.dataset.v === v;
                    b.classList.toggle('active', on); b.setAttribute('aria-selected', String(on));
                });
                labelCells(box);
            }
            setView(view);

            // DataTables / filter menggambar ulang baris -> beri label lagi
            let t = null;
            new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => labelCells(box), 60); })
                .observe(box, { childList: true, subtree: true });
        });
    }

    initDbViews();
})();
