// static/js/aktivasi_rfid.js

htmxReady(() => {
    // Filter tabel berdasarkan nama alat / RFID UID
    const searchInput = document.getElementById('searchAlat');
    const table = document.getElementById('alatTable');
    if (searchInput && table) {
        searchInput.addEventListener('input', () => {
            const keyword = searchInput.value.trim().toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((row) => {
                if (row.querySelector('.empty-state')) return;
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(keyword) ? '' : 'none';
            });
        });
    }
});