/* Apply the saved theme before the page paints to avoid a flash. */
(function () {
    var root = document.documentElement;
    root.classList.add('js');
    try {
        var theme = localStorage.getItem('theme');
        if (theme) root.setAttribute('data-theme', theme);
    } catch (error) {}
})();
