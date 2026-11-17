/* ---- CSRF: sisipkan header X-CSRFToken otomatis ke semua fetch non-GET ke situs sendiri ---- */
(function () {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.content : '';
    const origFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        const method = (init.method || (input && input.method) || 'GET').toUpperCase();
        if (token && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
            const headers = new Headers(init.headers || (input && input.headers) || {});
            if (!headers.has('X-CSRFToken')) headers.set('X-CSRFToken', token);
            init.headers = headers;
        }
        return origFetch.call(this, input, init);
    };
})();
