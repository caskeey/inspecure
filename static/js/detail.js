/* static/js/detail.js */

// 1. TAB SYSTEM LOGIC
function switchTab(tabName) {
    // Hide all contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(el => el.classList.remove('active'));

    // Remove active class from buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(el => el.classList.remove('active'));

    // Activate specific tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Highlight button (Mencari tombol yang diklik berdasarkan onclick attribute agak tricky, 
    // jadi kita loop manual atau kirim 'this' sebagai parameter. 
    // Cara mudah: loop cari text/index. Tapi mari kita pakai event delegation sederhana di HTML)
    
    // *Correction*: Biar simple, kita cari button yang punya onclick sesuai nama tab
    const activeBtn = Array.from(buttons).find(btn => btn.getAttribute('onclick').includes(tabName));
    if(activeBtn) activeBtn.classList.add('active');
}

// 2. MODAL UPLOAD HANDLER
function openUploadModal() {
    document.getElementById('uploadModal').classList.add('active');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('active');
}

// Tutup modal jika klik di luar box (backdrop)
window.onclick = function(event) {
    const modal = document.getElementById('uploadModal');
    if (event.target == modal) {
        closeUploadModal();
    }
}

// 3. CONFIRM DELETE ACTION
function confirmDelete(id) {
    // Bisa diganti SweetAlert jika mau lebih bagus
    if(confirm("PERINGATAN: Apakah Anda yakin ingin menghapus aset ini beserta seluruh riwayat dan dokumennya? Tindakan ini tidak dapat dibatalkan.")) {
        // Buat form submit secara dinamis atau redirect
        // Asumsi route flask: /alat/hapus/<id> menerima POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/hapus_alat/${id}`;
        const t = document.createElement('input');
        t.type = 'hidden'; t.name = 'csrf_token';
        t.value = document.querySelector('meta[name="csrf-token"]').content;
        form.appendChild(t);
        document.body.appendChild(form);
        form.submit();
    }
}

// 4. AUTO SCROLL KE ATAS SAAT LOAD
// Berguna untuk tampilan Mobile/NFC agar user langsung lihat header
htmxReady(function() {
    window.scrollTo(0, 0);
});