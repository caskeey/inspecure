$(function () {
    const tableElement = document.getElementById('masterTable');
    const $table = $('#masterTable');
    const esc = $.fn.dataTable.render.text().display;
    const urlForId = (template, id) => template.replace(/0$/, encodeURIComponent(id));
    const admin = tableElement.dataset.isAdmin === 'true';

    for (let day = 1; day <= 31; day += 1) {
        const value = String(day).padStart(2, '0');
        $('#f-day').append(new Option(value, value));
    }

    const columns = [
        { data: 0, render: (value, type) => type !== 'display' ? value : `<div class="uid-pill"><i class="ph-bold ph-scan"></i> ${esc(value || '')}</div>` },
        { data: 1, render: (value, type, row) => type !== 'display' ? value : `<a href="${urlForId(tableElement.dataset.detailUrl, row[8] ?? row.id)}" class="detail-link" title="Lihat Detail">${esc(value || '')}</a>`, className: 'fw-bold' },
        { data: 2, render: (value, type) => type !== 'display' ? value : `<span class="text-mono">${esc(value || '')}</span>` },
        { data: 3 }, { data: 4 }, { data: 5 },
        { data: 6, render: (value, type) => type !== 'display' ? value : `<div class="date-chip">${esc(value || '')}</div>` },
        { data: 7, render: (value, type) => {
            if (type !== 'display') return value;
            const color = value === 'Aktif' ? 'green' : value === 'Expired' ? 'red' : 'orange';
            const label = value === 'Masa Resertifikasi' ? 'Warning' : (value || '');
            return `<span class="status-badge ${color}">${esc(label)}</span>`;
        } }
    ];

    if (admin) {
        columns.push({
            data: 8, orderable: false, searchable: false, className: 'text-center',
            render: (id, type) => {
                if (type !== 'display') return id;
                return `<div class="action-row center">
                    <a href="${urlForId(tableElement.dataset.editUrl, id)}" class="btn-action edit" title="Edit Data"><i class="ph-bold ph-pencil-simple"></i></a>
                    <a href="${urlForId(tableElement.dataset.resertifikasiUrl, id)}" class="btn-action" title="Resertifikasi"><i class="ph-bold ph-certificate"></i></a>
                    <form action="${urlForId(tableElement.dataset.deleteUrl, id)}" method="POST" onsubmit="return confirm('Hapus permanen?');">
                        <input type="hidden" name="csrf_token" value="${esc(tableElement.dataset.csrfToken)}">
                        <button type="submit" class="btn-action delete" title="Hapus"><i class="ph-bold ph-trash"></i></button>
                    </form>
                </div>`;
            }
        });
    }

    const table = $table.DataTable({
        processing: true,
        serverSide: true,
        deferRender: true,
        ajax: {
            url: tableElement.dataset.apiUrl,
            data: request => {
                request.job = $('#f-pekerjaan').val();
                request.tool = $('#f-alat').val();
                request.company = $('#f-perusahaan').val();
                request.status = $('#f-status').val();
                request.day = $('#f-day').val();
                request.month = $('#f-month').val();
                request.year = $('#f-year').val();
            }
        },
        columns,
        order: [[0, 'desc']],
        dom: '<"dt-top"Bf>rt<"dt-bottom"lp><"clear">',
        buttons: [
            { extend: 'excel', text: '<i class="ph-bold ph-file-xls"></i> Excel', className: 'btn-export' },
            { extend: 'print', text: '<i class="ph-bold ph-printer"></i> Print', className: 'btn-export' }
        ],
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        responsive: false,
        language: {
            processing: 'Memuat data...',
            search: '_INPUT_',
            searchPlaceholder: 'Cari data...',
            lengthMenu: 'Tampil _MENU_',
            info: 'Menampilkan _START_–_END_ dari _TOTAL_ data',
            infoEmpty: 'Tidak ada data',
            zeroRecords: 'Data tidak ditemukan',
            paginate: { next: '›', previous: '‹' }
        }
    });

    $('.inp-f').on('change keyup', () => table.ajax.reload());
    $('#resetFilter').on('click', () => {
        $('.inp-f').val('');
        table.search('').draw();
    });

    $.getJSON(tableElement.dataset.filterOptionsUrl).done(options => {
        const populate = (selector, values) => values.forEach(value => $(selector).append(new Option(value, value)));
        populate('#f-pekerjaan', options.jobs || []);
        populate('#f-alat', options.tools || []);
        populate('#f-perusahaan', options.companies || []);
    });
});

function toggleFilter() {
    document.getElementById('filterBody').classList.toggle('show');
    document.querySelector('.toggle-icon').classList.toggle('rotate');
}
