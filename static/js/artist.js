// Artist page: the song list drives one shared player. A click, a #song-slug in the URL
// (from search results) or a hash change loads that song; there are no per-song pages.
(function () {
    var wide = window.matchMedia("(min-width: 768px)");
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    var list = document.getElementById("song-list");
    var panel = document.getElementById("player-panel");
    var home = document.getElementById("player-home");
    var rows = Array.prototype.slice.call(list.querySelectorAll(".song-row"));
    var watch = "https://www.youtube.com/watch?v=";
    var search = "https://www.youtube.com/results?search_query=";
    var baseTitle = document.title;
    var frame = document.getElementById("player-frame");
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".player-tab"));
    var tab = "lesson";  // "lesson" | "original": one big video at a time, the choice is remembered
    try { if (localStorage.getItem("playerTab") === "original") tab = "original"; } catch (e) { /* storage blocked */ }

    function byId(id) { return document.getElementById(id); }
    function current() { return list.querySelector('.song-row[aria-current="true"]'); }

    // ---- YouTube players ------------------------------------------------------------
    // The iframe API tells us when a video can't be played for this viewer (region block,
    // embedding disabled, removed); then a card with other ways to watch replaces the grey error.
    var apiPromise = null;
    function loadApi() {
        if (apiPromise) return apiPromise;
        apiPromise = new Promise(function (resolve, reject) {
            if (window.YT && window.YT.Player) { resolve(window.YT); return; }
            window.onYouTubeIframeAPIReady = function () { resolve(window.YT); };
            var script = document.createElement("script");
            script.src = "https://www.youtube.com/iframe_api";
            script.onerror = reject;
            document.head.appendChild(script);
            setTimeout(reject, 8000);
        });
        return apiPromise;
    }

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    // Fixed markup, no user data: safe to set as HTML.
    var ICON_PLAY = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>';
    var ICON_SEARCH = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m16 16 4.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    var ICON_OFF = '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><rect x="3" y="5.5" width="18" height="13" rx="3.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10 9.5v5l4.2-2.5z" fill="currentColor"/><path d="M4 4l16 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

    function button(icon, text, href, className) {
        var a = el("a", "fb-btn " + className);
        a.href = href; a.target = "_blank"; a.rel = "noopener";
        a.insertAdjacentHTML("afterbegin", icon);
        a.appendChild(el("span", "", text));
        return a;
    }

    function showFallback(frame, videoId, query, original) {
        frame.textContent = "";
        var card = el("div", "player-fallback");
        var badge = el("div", "fb-badge");
        badge.insertAdjacentHTML("afterbegin", ICON_OFF);
        badge.appendChild(el("span", "", "Can't play here"));
        var actions = el("div", "fb-actions");
        actions.appendChild(button(ICON_PLAY, "Watch on YouTube", watch + videoId, "fb-primary"));
        if (original) actions.appendChild(button(ICON_SEARCH, "Find other recordings", search + encodeURIComponent(query), "fb-ghost"));
        card.appendChild(badge);
        card.appendChild(actions);
        frame.appendChild(card);
    }

    function mount(frame, videoId, query, original) {
        var token = String(Number(frame.dataset.token || 0) + 1);
        frame.dataset.token = token;
        frame.textContent = "";
        loadApi().then(function (YT) {
            if (frame.dataset.token !== token) return;  // a newer song replaced this one
            var holder = el("div");
            frame.appendChild(holder);
            new YT.Player(holder, {
                host: "https://www.youtube-nocookie.com",
                videoId: videoId,
                playerVars: { rel: 0, playsinline: 1 },
                events: {
                    onError: function () {
                        if (frame.dataset.token === token) showFallback(frame, videoId, query, original);
                    }
                }
            });
        }, function () {  // API blocked or offline: plain iframe, no error detection
            if (frame.dataset.token !== token) return;
            var iframe = el("iframe");
            iframe.src = "https://www.youtube-nocookie.com/embed/" + videoId;
            iframe.title = original ? "Original recording" : "Sheet-music lesson";
            iframe.allow = "encrypted-media; picture-in-picture";
            iframe.allowFullscreen = true;
            frame.appendChild(iframe);
        });
    }

    function stopVideos() {  // removing the iframe is the only way to stop a hidden player
        frame.dataset.token = String(Number(frame.dataset.token || 0) + 1);
        frame.textContent = "";
    }

    // ---- sheet-music PDFs (admin only) ----------------------------------------------
    // The page is the same for everybody (it may sit in a shared cache), so whether the
    // visitor is the admin is asked separately. Until then, and for everyone else, the buttons
    // show a lock and lead to the sign-in page, which returns to this song.
    var pdfBox = byId("player-pdfs");
    var pdfButtons = [[byId("pdf-sheet"), "sheet"], [byId("pdf-tab"), "tabPdf"]];
    var isAdmin = false;
    var viewing = null;  // "sheet" | "tabPdf" while a PDF is shown in the page instead of the video
    var viewer = byId("pdf-viewer");

    // The PDF replaces the video in the same panel (it is too tall to sit next to it); the video tabs bring it back.
    function openPdf(key) {
        var row = current(), url = row && row.dataset[key];
        if (!url) return;
        viewing = key;
        stopVideos();
        frame.hidden = true;
        byId("player-more").parentElement.hidden = true;
        tabs.forEach(function (t) { t.setAttribute("aria-selected", "false"); });
        byId("pdf-viewer-title").textContent = key === "sheet" ? "Sheet music" : "Tablature";
        byId("pdf-newtab").href = url;
        byId("pdf-frame").src = url;
        viewer.hidden = false;
        markPdfButtons();
    }

    function closePdf() {
        if (!viewing) return;
        viewing = null;
        byId("pdf-frame").removeAttribute("src");  // stops loading and frees the viewer
        viewer.hidden = true;
        frame.hidden = false;
        markPdfButtons();
    }

    function markPdfButtons() {
        pdfButtons.forEach(function (pair) { pair[0].setAttribute("aria-pressed", String(viewing === pair[1])); });
    }

    pdfButtons.forEach(function (pair) {
        if (!pair[0]) return;
        pair[0].addEventListener("click", function (e) {
            if (!isAdmin || !wide.matches || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;  // locked: sign-in; phone: new tab; modifier: new tab
            e.preventDefault();
            if (viewing === pair[1]) { showTab(current()); return; }  // pressing the open one closes it
            openPdf(pair[1]);
        });
    });

    function showPdfs(row) {
        if (!pdfBox || !row) return;
        var any = false;
        pdfButtons.forEach(function (pair) {
            var link = pair[0], url = row.dataset[pair[1]];
            link.hidden = !url;
            if (!url) return;
            any = true;
            link.href = isAdmin ? url : "/admin?next=" + encodeURIComponent(location.pathname + "#" + row.dataset.slug);
            // Phones show PDFs badly inside a page, so there the button simply opens a new tab.
            var inPage = isAdmin && wide.matches;
            if (inPage || !isAdmin) link.removeAttribute("target"); else link.target = "_blank";
            link.rel = "noopener";
            link.title = !isAdmin ? "Sign in to open" : inPage ? "Show here (Ctrl/Cmd-click: new tab)" : "Opens in a new tab";
        });
        pdfBox.hidden = !any;
        panel.dataset.admin = String(isAdmin);
    }

    if (pdfBox && list.querySelector("[data-sheet], [data-tab-pdf]")) {
        fetch("/admin/session", { cache: "no-store" })
            .then(function (r) { return r.ok ? r.json() : { admin: false }; })
            .then(function (data) { isAdmin = !!data.admin; showPdfs(current()); })
            .catch(function () { /* stays locked */ });
    }

    function showTab(row) {
        closePdf();
        tabs.forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.tab === tab)); });
        byId("player-more").parentElement.hidden = tab !== "original";  // other recordings only make sense for the song, not for the sheet-music lesson
        if (!row) return;
        var id = tab === "original" ? row.dataset.original : row.dataset.lesson;
        mount(frame, id, row.dataset.query, tab === "original");
    }

    // ---- placement ------------------------------------------------------------------
    // Phones: the player opens inside the list, right under the tapped song, so the list
    // never gets pushed down. Wide screens: it lives in the side column.
    function place() {
        var row = current();
        if (wide.matches) {
            home.appendChild(panel);
            panel.hidden = false;
        } else if (row) {
            row.parentElement.appendChild(panel);
            panel.hidden = false;
        } else {
            home.appendChild(panel);
            panel.hidden = true;
        }
    }

    function select(row, keepTitle) {
        rows.forEach(function (r) { r.removeAttribute("aria-current"); });
        row.setAttribute("aria-current", "true");
        byId("player-title").textContent = row.dataset.title;
        byId("player-title-gr").textContent = row.dataset.titleGr;
        byId("player-more").href = search + encodeURIComponent(row.dataset.query);
        if (!keepTitle) document.title = row.dataset.title + " — " + list.dataset.artistName + " — Bouzouki Rebetico";
        place();  // move first: moving an iframe reloads it
        showTab(row);
        showPdfs(row);
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

    // ---- share ----------------------------------------------------------------------
    // The link is the page itself plus #song-slug, which this script already opens. Phones get the
    // system share sheet (WhatsApp etc.); on wide screens the OS dialog is clumsy, so the link is copied.
    var shareBtn = byId("player-share");
    var shareText = shareBtn.querySelector("span");
    var shareTimer = null;

    function shareNote(text) {
        shareText.textContent = text;
        clearTimeout(shareTimer);
        shareTimer = setTimeout(function () { shareText.textContent = "Share"; }, 2000);
    }

    shareBtn.addEventListener("click", function () {
        var row = current();
        if (!row) return;
        var url = location.origin + location.pathname + "#" + encodeURIComponent(row.dataset.slug);
        var title = row.dataset.title + " — " + list.dataset.artistName;
        if (navigator.share && !wide.matches) {
            navigator.share({ title: title, url: url }).catch(function () { /* cancelled */ });
            return;
        }
        var copied = navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject();
        copied.then(function () { shareNote("Copied ✓"); }, function () { window.prompt("Copy this link:", url); });
    });

    tabs.forEach(function (t) {
        t.addEventListener("click", function () {
            tab = t.dataset.tab;
            try { localStorage.setItem("playerTab", tab); } catch (e) { /* ignore */ }
            showTab(current());
        });
    });

    wide.addEventListener("change", function () {
        var row = current() || (wide.matches ? rows[0] : null);
        if (row) select(row, true); else place();
    });
    window.addEventListener("hashchange", applyHash);

    showTab(null);  // reflect the remembered tab even if no song is open yet (phones)
    if (fromHash()) applyHash();
    else if (wide.matches && rows.length) select(rows[0], true);  // side player starts on the first song
    else place();

    // ---- filter ---------------------------------------------------------------------
    var filter = byId("song-filter");
    if (!filter) return;
    var empty = byId("filter-empty");
    var count = byId("filter-count");
    var timer = null, controller = null;

    function show(slugs) {
        var visible = 0;
        list.querySelectorAll("li").forEach(function (li) {
            var ok = slugs === null || slugs.indexOf(li.dataset.slug) !== -1;
            li.hidden = !ok;
            if (ok) visible++;
        });
        empty.hidden = visible > 0;
        count.hidden = slugs === null;
        count.textContent = visible + " of " + rows.length + " songs match";
    }

    filter.addEventListener("keydown", function (e) {  // Enter opens the first match, like a search box should
        if (e.key !== "Enter") return;
        e.preventDefault();
        var first = rows.filter(function (r) { return !r.parentElement.hidden; })[0];
        if (first) { first.click(); filter.blur(); }
    });

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
