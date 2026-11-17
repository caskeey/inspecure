document.addEventListener('DOMContentLoaded', () => {

    // Toggle tema (disimpan di localStorage 'theme', sama dengan dashboard)
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

    // Lihat / sembunyikan password (berlaku untuk semua tombol .toggle-pass)
    document.querySelectorAll('.toggle-pass').forEach((btn) => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input');
            const icon = btn.querySelector('i');
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            icon.classList.toggle('ph-eye', !show);
            icon.classList.toggle('ph-eye-slash', show);
        });
    });

    // Tombol submit menampilkan spinner supaya tidak diklik dua kali
    document.querySelectorAll('form').forEach((form) => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('.btn-login');
            if (btn) { btn.classList.add('loading'); setTimeout(() => { btn.disabled = true; }, 0); }
        });
    });
});