// Search-as-you-type for every <form class="js-search">: results, keyboard navigation,
// Enter opens the highlighted (or best) result.
(function () {
    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function init(form) {
        var input = form.querySelector("input[name=q]");
        var list = form.querySelector(".search-results");
        var timer = null, controller = null, items = [], active = -1;

        function close() {
            list.hidden = true;
            input.setAttribute("aria-expanded", "false");
            active = -1;
        }

        function highlight(index) {
            items.forEach(function (a, i) { a.setAttribute("aria-selected", i === index ? "true" : "false"); });
            active = index;
            if (items[index]) items[index].scrollIntoView({ block: "nearest" });
        }

        function render(results) {
            list.textContent = "";
            items = [];
            if (!results.length) {
                list.appendChild(el("li", "search-empty", "No match. Spelling doesn't have to be exact — try fewer letters."));
            }
            results.forEach(function (r) {
                var li = el("li");
                li.setAttribute("role", "presentation");
                var a = el("a", "search-item");
                a.href = r.url;
                a.setAttribute("role", "option");
                a.appendChild(el("span", "search-kind", r.type));
                var main = el("span", "search-main");
                main.appendChild(el("strong", "", r.label));
                main.appendChild(el("small", "", r.label_gr + " · " + r.sub));
                a.appendChild(main);
                li.appendChild(a);
                list.appendChild(li);
                items.push(a);
            });
            list.hidden = false;
            input.setAttribute("aria-expanded", "true");
            active = -1;
        }

        function run() {
            var term = input.value.trim();
            if (term.length < 2) { close(); return; }
            if (controller) controller.abort();
            controller = new AbortController();
            fetch("/search?term=" + encodeURIComponent(term) + "&limit=8", { signal: controller.signal })
                .then(function (r) { return r.ok ? r.json() : []; })
                .then(function (data) { if (input.value.trim() === term) render(data); })
                .catch(function () { /* aborted or offline: keep the form usable */ });
        }

        input.addEventListener("input", function () {
            clearTimeout(timer);
            timer = setTimeout(run, 120);
        });
        input.addEventListener("keydown", function (e) {
            if (e.key === "Escape") { close(); return; }
            if (list.hidden || !items.length) return;
            if (e.key === "ArrowDown") { e.preventDefault(); highlight((active + 1) % items.length); }
            else if (e.key === "ArrowUp") { e.preventDefault(); highlight((active - 1 + items.length) % items.length); }
        });
        // Enter / Search button opens the best match straight away; /find is only the no-JS and no-match fallback.
        form.addEventListener("submit", function (e) {
            if (!list.hidden && items.length && input.value.trim().length >= 2) {
                e.preventDefault();
                window.location.href = items[active >= 0 ? active : 0].href;
            }
        });
        document.addEventListener("click", function (e) { if (!form.contains(e.target)) close(); });
        input.addEventListener("focus", function () { if (items.length) { list.hidden = false; input.setAttribute("aria-expanded", "true"); } });
    }

    document.querySelectorAll("form.js-search").forEach(init);
})();
