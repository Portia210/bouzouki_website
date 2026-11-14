// Artist page: the song list drives one shared player. A click, a #song-slug in the URL
// (from search results) or a hash change loads that song; there are no per-song pages.
(function () {
    var wide = window.matchMedia("(min-width: 768px)");
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    var list = document.getElementById("song-list");
    var panel = document.getElementById("player-panel");
    var rows = Array.prototype.slice.call(list.querySelectorAll(".song-row"));
    var embed = "https://www.youtube-nocookie.com/embed/";
    var watch = "https://www.youtube.com/watch?v=";
    var baseTitle = document.title;

    function byId(id) { return document.getElementById(id); }

    function select(row) {
        rows.forEach(function (r) { r.removeAttribute("aria-current"); });
        row.setAttribute("aria-current", "true");
        byId("player-title").textContent = row.dataset.title;
        byId("player-title-gr").textContent = row.dataset.titleGr;
        byId("player-original").src = embed + row.dataset.original;
        byId("player-lesson").src = embed + row.dataset.lesson;
        byId("player-original-link").href = watch + row.dataset.original;
        byId("player-lesson-link").href = watch + row.dataset.lesson;
        byId("player-more").href = "https://www.youtube.com/results?search_query=" + encodeURIComponent(row.dataset.query);
        document.title = row.dataset.title + " — " + list.dataset.artistName + " — Rebetiko Music";
    }

    function fromHash() {
        var slug = decodeURIComponent(location.hash.slice(1));
        return rows.filter(function (r) { return r.dataset.slug === slug; })[0];
    }

    function applyHash() {
        var row = fromHash();
        if (!row) return;
        select(row);
        // Wide: keep the chosen row in view next to the player. Phone: the player sits above the list.
        if (wide.matches) row.scrollIntoView({ block: "center" });
        else panel.scrollIntoView({ block: "start" });
    }

    list.addEventListener("click", function (e) {
        var row = e.target.closest(".song-row");
        if (!row || e.metaKey || e.ctrlKey || e.shiftKey) return;
        e.preventDefault();
        select(row);
        history.replaceState(null, "", "#" + row.dataset.slug);
        if (!wide.matches) panel.scrollIntoView({ behavior: reduce.matches ? "auto" : "smooth", block: "start" });
    });

    window.addEventListener("hashchange", applyHash);
    if (fromHash()) applyHash();
    else if (rows.length) { rows[0].setAttribute("aria-current", "true"); document.title = baseTitle; }

    var filter = byId("song-filter");
    if (!filter) return;
    var empty = byId("filter-empty");
    var timer = null, controller = null;

    function show(slugs) {
        var visible = 0;
        list.querySelectorAll("li").forEach(function (li) {
            var ok = slugs === null || slugs.indexOf(li.dataset.slug) !== -1;
            li.hidden = !ok;
            if (ok) visible++;
        });
        empty.hidden = visible > 0;
    }

    filter.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
            var term = filter.value.trim();
            if (term.length < 2) { show(null); return; }
            if (controller) controller.abort();
            controller = new AbortController();
            fetch("/search?term=" + encodeURIComponent(term) + "&artist=" + encodeURIComponent(filter.dataset.artist) + "&limit=200",
                { signal: controller.signal })
                .then(function (r) { return r.ok ? r.json() : []; })
                .then(function (data) { show(data.map(function (s) { return s.slug; })); })
                .catch(function () { /* aborted */ });
        }, 120);
    });
})();
