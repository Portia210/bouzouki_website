// Artist page: on wide screens a click on a song loads it in the side player instead of
// navigating; on phones the link opens the song page. Also filters the song list.
(function () {
    var wide = window.matchMedia("(min-width: 768px)");
    var list = document.getElementById("song-list");
    var rows = Array.prototype.slice.call(list.querySelectorAll(".song-row"));
    var embed = "https://www.youtube-nocookie.com/embed/";

    function select(row) {
        rows.forEach(function (r) { r.removeAttribute("aria-current"); });
        row.setAttribute("aria-current", "true");
        document.getElementById("player-title").textContent = row.dataset.title;
        document.getElementById("player-original").src = embed + row.dataset.original;
        document.getElementById("player-lesson").src = embed + row.dataset.lesson;
        document.getElementById("player-link").href = row.href;
    }

    list.addEventListener("click", function (e) {
        var row = e.target.closest(".song-row");
        if (!row || !wide.matches || e.metaKey || e.ctrlKey || e.shiftKey) return;
        e.preventDefault();
        select(row);
        history.replaceState(null, "", "#" + row.dataset.slug);
    });

    var fromHash = rows.filter(function (r) { return "#" + r.dataset.slug === location.hash; })[0];
    if (rows.length) {
        if (fromHash) {
            select(fromHash);
            fromHash.scrollIntoView({ block: "center" });
        } else {
            rows[0].setAttribute("aria-current", "true");
        }
    }

    var filter = document.getElementById("song-filter");
    if (!filter) return;
    var empty = document.getElementById("filter-empty");
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
