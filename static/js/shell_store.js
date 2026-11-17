/* Penyimpanan preferensi browser yang dipakai oleh app shell. */
window.inspecureStore = {
    get(key, fallback) {
        try { const value = localStorage.getItem(key); return value === null ? fallback : value; }
        catch (error) { return fallback; }
    },
    set(key, value) {
        try { localStorage.setItem(key, value); } catch (error) { /* penyimpanan browser opsional */ }
    }
};
