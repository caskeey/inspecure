/* static/js/data_master.js */

$(document).ready(function() {
    
    // 1. INIT DATATABLES
    var table = $('#masterTable').DataTable({
        dom: '<"dt-top"Bf>rt<"dt-bottom"lp><"clear">', // Layout custom
        buttons: [
            { extend: 'excel', text: '<i class="ph-bold ph-file-xls"></i> Excel', className: 'btn-export' },
            { extend: 'print', text: '<i class="ph-bold ph-printer"></i> Print', className: 'btn-export' }
        ],
        pageLength: 10,
        responsive: false, // Kita handle manual pakai overflow-x biar lebih kontrol
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Cari data...",
            lengthMenu: "Tampil _MENU_",
            info: "Hal _PAGE_ dari _PAGES_",
            paginate: { next: "›", previous: "‹" }
        }
    });

    // 2. ISI DROPDOWN TANGGAL (1-31)
    for(let i=1; i<=31; i++){
        let val = i < 10 ? '0'+i : i;
        $('#f-day').append(`<option value="${val}">${val}</option>`);
    }

    // 3. AUTO-POPULATE FILTER DARI DATA TABEL
    // Mengambil data unik dari kolom tabel untuk isi dropdown filter
    function populateFilter(colIndex, selectId) {
        table.column(colIndex).data().unique().sort().each(function(d, j) {
            // Bersihkan HTML tag jika ada (misal span badge)
            let text = $('<div>').html(d).text().trim(); 
            if(text && text !== "") {
                $(selectId).append('<option value="'+text+'">'+text+'</option>');
            }
        });
    }

    // Index kolom (sesuaikan dengan thead HTML): 3=Pekerjaan, 4=Jenis, 5=Perusahaan
    populateFilter(3, '#f-pekerjaan'); 
    populateFilter(4, '#f-alat');      
    populateFilter(5, '#f-perusahaan'); 

    // 4. LOGIKA FILTERING
    $('.inp-f').on('change keyup', function() {
        var day = $('#f-day').val();
        var month = $('#f-month').val();
        var year = $('#f-year').val();
        
        var job = $('#f-pekerjaan').val();
        var tool = $('#f-alat').val();
        var company = $('#f-perusahaan').val();
        var status = $('#f-status').val();

        // Search kolom teks
        table.column(3).search(job).draw();
        table.column(4).search(tool).draw();
        table.column(5).search(company).draw();
        
        // Search kolom status (Index 7)
        // Kita cari text-nya saja karena di HTML ada span class
        table.column(7).search(status).draw(); 

        // Custom Filter Tanggal (Index 6)
        $.fn.dataTable.ext.search.push(
            function(settings, data, dataIndex) {
                var dateStr = data[6]; // Ambil string tanggal
                if (!dateStr) return true; 

                if (year && !dateStr.includes(year)) return false;
                if (month && !dateStr.includes('-' + month + '-')) return false;
                if (day && !dateStr.endsWith('-' + day)) return false;

                return true;
            }
        );
        
        table.draw(); 
        $.fn.dataTable.ext.search.pop(); 
    });

    // 5. TOMBOL RESET
    $('#resetFilter').on('click', function(){
        $('.inp-f').val(''); // Kosongkan input
        table.search('').columns().search('').draw(); // Reset tabel
    });
});

/* Buka/tutup panel filter (dipanggil lewat onclick="toggleFilter()" di data_master.html).
 * Dulu <script> inline di template itu. */
function toggleFilter() {
    document.getElementById('filterBody').classList.toggle('show');
    document.querySelector('.toggle-icon').classList.toggle('rotate');
}