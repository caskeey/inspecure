document.addEventListener('DOMContentLoaded', () => {

    // 1. Toggle tema (disimpan di localStorage 'theme', sama dengan dashboard)
    const root = document.documentElement;
    const themeBtn = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const syncIcon = () => {
        if (themeIcon) themeIcon.className = 'ph-bold ' + (root.getAttribute('data-theme') === 'dark' ? 'ph-sun' : 'ph-moon');
    };
    syncIcon();
    if (themeBtn) themeBtn.addEventListener('click', () => {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) {}
        syncIcon();
    });

    // 2. Garis bawah navbar muncul setelah di-scroll
    const nav = document.getElementById('nav');
    const onScroll = () => nav && nav.classList.toggle('scrolled', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    // 3. Elemen .reveal muncul halus saat masuk layar
    const items = document.querySelectorAll('.reveal');
    if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
        items.forEach((el) => io.observe(el));
    } else {
        items.forEach((el) => el.classList.add('in'));
    }

    // 4. Smooth scroll untuk link anchor
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
        a.addEventListener('click', (e) => {
            const target = document.querySelector(a.getAttribute('href'));
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        });
    });
});