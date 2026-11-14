// Runs in <head> so the saved theme is applied before first paint.
(function () {
    var root = document.documentElement;
    var saved = null;
    try { saved = localStorage.getItem("theme"); } catch (e) { /* storage blocked */ }
    var dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.setAttribute("data-bs-theme", saved || (dark ? "dark" : "light"));

    document.addEventListener("DOMContentLoaded", function () {
        var button = document.getElementById("theme-toggle");
        if (!button) return;
        button.addEventListener("click", function () {
            var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
            root.setAttribute("data-bs-theme", next);
            try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
        });
    });
})();
