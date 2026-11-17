// Dideklarasiin duluan di sini (sebelum htmxReady), tapi belum diisi nilai.
// `var` dipilih biar aman gak SyntaxError kalau file ini re-eksekusi lewat
// navigasi SPA (htmx).
var currentDt;
var selectedCalendarDate = null;

// === LOGIC KALENDER ===

function initCalendar(events) {
    selectedCalendarDate = null;
    renderGrid(events);
    renderList(events);

    window.changeMonth = (step) => {
        // Selalu pindah dari tanggal 1 agar tanggal 29-31 tidak melompati bulan.
        currentDt = new Date(currentDt.getFullYear(), currentDt.getMonth() + step, 1);
        selectedCalendarDate = null;
        renderGrid(events);
        renderList(events);
    };
}

function localDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function parseLocalDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return null;
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day ? date : null;
}

function renderGrid(events) {
    const grid = document.getElementById('calGrid');
    const label = document.getElementById('calMonthYear');
    if(!grid) return;

    grid.replaceChildren();
    const y = currentDt.getFullYear();
    const m = currentDt.getMonth();
    const months = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
    label.innerText = `${months[m]} ${y}`;

    const firstDay = new Date(y, m, 1).getDay(); // 0 = Minggu
    const daysInM = new Date(y, m+1, 0).getDate();
    const today = new Date();

    // Padding empty cells
    for(let i=0; i<firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'day-placeholder';
        empty.setAttribute('aria-hidden', 'true');
        grid.appendChild(empty);
    }

    // Days
    for(let d=1; d<=daysInM; d++) {
        const cell = document.createElement('button');
        cell.type = 'button';
        cell.className = 'day';
        cell.textContent = d;
        const dStr = `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        cell.setAttribute('aria-label', new Date(y, m, d).toLocaleDateString('id-ID', {
            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
        }));
        cell.setAttribute('aria-pressed', String(selectedCalendarDate === dStr));

        if (selectedCalendarDate === dStr) cell.classList.add('selected');
        
        // Highlight Hari Ini
        if(d === today.getDate() && m === today.getMonth() && y === today.getFullYear()) {
            cell.classList.add('today');
        }
        
        // Marker Event
        if(events.some(e => e.date === dStr)) {
            cell.classList.add('has-event');
        }

        cell.addEventListener('click', () => {
            selectedCalendarDate = dStr;
            renderGrid(events);
            renderList(events);
        });
        grid.appendChild(cell);
    }
}

function renderList(events) {
    const container = document.getElementById('eventListContainer');
    if(!container) return;

    const todayStr = localDateKey(new Date());
    const heading = document.getElementById('agendaTitle');
    if (heading) {
        const selectedDate = parseLocalDate(selectedCalendarDate);
        heading.textContent = selectedDate
            ? `Agenda ${selectedDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long' })}`
            : 'Agenda Terdekat';
    }
    // Pilih tanggal tertentu dari kalender, atau tampilkan empat agenda mendatang.
    const matching = events
        .filter(event => parseLocalDate(event.date))
        .filter(event => selectedCalendarDate
            ? event.date === selectedCalendarDate
            : event.date >= todayStr)
        .sort((a, b) => a.date.localeCompare(b.date));
    const upcoming = selectedCalendarDate ? matching : matching.slice(0, 4);

    if(upcoming.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'calendar-empty';
        const icon = document.createElement('i');
        icon.className = 'ph-duotone ph-coffee';
        icon.setAttribute('aria-hidden', 'true');
        const message = document.createElement('p');
        message.textContent = selectedCalendarDate ? 'Tidak ada agenda pada tanggal ini.' : 'Tidak ada agenda terdekat.';
        empty.append(icon, message);
        container.replaceChildren(empty);
        return;
    }

    container.replaceChildren();
    upcoming.forEach(event => {
        const date = parseLocalDate(event.date);
        const item = document.createElement('div');
        item.className = 'evt-item';

        const dateBox = document.createElement('div');
        dateBox.className = 'evt-date';
        const day = document.createElement('b');
        day.textContent = date.getDate();
        const month = document.createElement('span');
        month.textContent = date.toLocaleString('id-ID', { month: 'short' });
        dateBox.append(day, month);

        const detail = document.createElement('div');
        detail.className = 'evt-text';
        const title = document.createElement('h4');
        title.textContent = event.title || 'Agenda';
        const type = document.createElement('p');
        type.textContent = event.type === 'expired' ? 'Sertifikat kedaluwarsa' : 'Agenda';
        detail.append(title, type);
        item.append(dateBox, detail);
        container.appendChild(item);
    });
}
