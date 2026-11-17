(function () {
    'use strict';

    function initSidebarTips() {
        const sb = document.getElementById('sidebar');
        if (!sb) return;
        const tip = document.createElement('div');
        tip.className = 'sb-tip'; tip.setAttribute('role', 'tooltip');
        document.body.appendChild(tip);
        const hide = () => tip.classList.remove('show');
        function show(el) {
            const always = el.classList.contains('logout-btn');
            if (!always && (!sb.classList.contains('collapsed') || window.innerWidth <= 1024)) return;
            const node = el.querySelector('.link-text') || el.querySelector('.u-name');
            const text = (el.dataset.tip || (node && node.textContent) || '').trim();
            if (!text) return;
            const r = el.getBoundingClientRect();
            tip.textContent = text;
            tip.style.top = (r.top + r.height / 2) + 'px';
            tip.style.left = (r.right + 10) + 'px';
            tip.classList.add('show');
        }
        sb.querySelectorAll('.menu-item, .user-card, .logout-btn').forEach(el => {
            el.addEventListener('mouseenter', () => show(el));
            el.addEventListener('mouseleave', hide);
            el.addEventListener('focus', () => show(el));
            el.addEventListener('blur', hide);
        });
        new MutationObserver(hide).observe(sb, { attributes: true, attributeFilter: ['class'] });
        sb.addEventListener('scroll', hide, true);
    }

    initSidebarTips();
})();
