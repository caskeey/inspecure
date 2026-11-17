/* Apply saved canvas width before the page paints. */
try {
    if (localStorage.getItem('canvasFull') === '1') {
        document.documentElement.classList.add('canvas-pref-full');
    }
} catch (error) {}
