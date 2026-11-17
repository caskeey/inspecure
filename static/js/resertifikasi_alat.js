/* static/js/resertifikasi_alat.js */

htmxReady(function () {
    hitungExpired();
});

function hitungExpired() {
    const tglSertif = document.getElementById('tglSertif').value;
    const durasi = parseInt(document.getElementById('durasiAngka').value);
    const satuan = document.getElementById('durasiSatuan').value;
    const output = document.getElementById('viewExpired');
    const container = document.querySelector('.expired-display');

    if (tglSertif && durasi > 0) {
        const date = new Date(tglSertif);

        if (satuan === 'Tahun') {
            date.setFullYear(date.getFullYear() + durasi);
        } else if (satuan === 'Bulan') {
            date.setMonth(date.getMonth() + durasi);
        }

        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        output.value = date.toLocaleDateString('id-ID', options);

        output.style.color = "#B45309";
        if (container) {
            container.style.borderColor = "#F59E0B";
            container.style.background = "#FFFBEB";
        }
    } else {
        output.value = "";
        output.style.color = "#64748B";
        if (container) {
            container.style.borderColor = "#E2E8F0";
            container.style.background = "white";
        }
    }
}