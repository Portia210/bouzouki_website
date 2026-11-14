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
    var home = byId("player-home");

    // Phones: the player opens inside the list, right under the tapped song, so the list
    // never gets pushed down. Wide screens: it lives in the side column.
    function place() {
        var current = list.querySelector('.song-row[aria-current="true"]');
        if (wide.matches) {
            home.appendChild(panel);
            panel.hidden = false;
        } else if (current) {
            current.parentElement.appendChild(panel);
            panel.hidden = false;
        } else {
            home.appendChild(panel);
            panel.hidden = true;
        }
    }

    function stopVideos() {
        // Replacing the iframes (without src) is the only way to stop playback of a hidden player.
        ["player-original", "player-lesson"].forEach(function (id) {
            var frame = byId(id), blank = frame.cloneNode(false);
            blank.removeAttribute("src");
            frame.replaceWith(blank);
        });
    }

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
        document.title = row.dataset.title + " — " + list.dataset.artistName + " — Bouzouki Rebetico";
        place();
    }

    function close() {
        rows.forEach(function (r) { r.removeAttribute("aria-current"); });
        stopVideos();
        document.title = baseTitle;
        history.replaceState(null, "", location.pathname + location.search);
        place();
    }

    function fromHash() {
        var slug = decodeURIComponent(location.hash.slice(1));
        return rows.filter(function (r) { return r.dataset.slug === slug; })[0];
    }

    function bringIntoView(row, smooth) {
        row.scrollIntoView({ behavior: smooth && !reduce.matches ? "smooth" : "auto", block: wide.matches ? "center" : "start" });
    }

    function applyHash() {
        var row = fromHash();
        if (!row) return;
        select(row);
        bringIntoView(row, false);
    }

    list.addEventListener("click", function (e) {
        var row = e.target.closest(".song-row");
        if (!row || e.metaKey || e.ctrlKey || e.shiftKey) return;
        e.preventDefault();
        if (!wide.matches && row.getAttribute("aria-current") === "true") { close(); return; }  // tap again = fold away
        select(row);
        history.replaceState(null, "", "#" + row.dataset.slug);
        if (!wide.matches) bringIntoView(row, true);
    });

    byId("player-close").addEventListener("click", function () {
        var row = list.querySelector('.song-row[aria-current="true"]');
        close();
        if (row) bringIntoView(row, true);
    });

    wide.addEventListener("change", place);
    window.addEventListener("hashchange", applyHash);

    if (fromHash()) applyHash();
    else {
        if (wide.matches && rows.length) rows[0].setAttribute("aria-current", "true");  // side player already shows song 1
        document.title = baseTitle;
        place();
    }

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
