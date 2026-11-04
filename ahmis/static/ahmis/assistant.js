/* Assistant AHMIS : affiche les réponses validées renvoyées par /assistant/ (aucun HTML injecté). */
(function () {
  "use strict";
  var root = document.getElementById("assistant");
  if (!root) return;
  var btn = document.getElementById("assistant-toggle");
  var panel = document.getElementById("assistant-panel");
  var form = document.getElementById("assistant-form");
  var input = document.getElementById("assistant-q");
  var out = document.getElementById("assistant-out");
  var url = root.getAttribute("data-url");
  var L = { open: root.getAttribute("data-l-open"), tuto: root.getAttribute("data-l-tuto"), more: root.getAttribute("data-l-more"),
            error: root.getAttribute("data-l-error") };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }
  function link(href, text) {
    var a = el("a", "btn small", text);
    if (href && href.charAt(0) === "/") a.href = href;
    return a;
  }
  function askButton(item) {
    var b = el("button", "linklike small", item.q);
    b.type = "button";
    b.addEventListener("click", function () { input.value = item.q; ask(item.q); });
    return b;
  }
  function render(data) {
    out.textContent = "";
    if (data.answer) {
      var a = data.answer, box = el("div", "assistant-answer" + (a.refusal ? " refusal" : ""));
      box.appendChild(el("strong", null, a.q));
      box.appendChild(el("p", null, a.a));
      var acts = el("div", "actions");
      if (a.url) acts.appendChild(link(a.url, L.open));
      if (a.tuto) acts.appendChild(link(a.tuto, L.tuto));
      box.appendChild(acts);
      out.appendChild(box);
    } else if (data.fallback) {
      out.appendChild(el("p", "muted small", data.fallback));
    }
    var list = (data.suggestions && data.suggestions.length) ? data.suggestions : data.questions;
    if (list && list.length) {
      out.appendChild(el("div", "small muted", L.more));
      var ul = el("ul", "assistant-list");
      list.forEach(function (item) { var li = el("li"); li.appendChild(askButton(item)); ul.appendChild(li); });
      out.appendChild(ul);
    }
  }
  function ask(q) {
    var x = new XMLHttpRequest();
    x.open("GET", url + "?q=" + encodeURIComponent(q || ""));
    x.setRequestHeader("Accept", "application/json");
    x.onload = function () {
      if (x.status !== 200) { out.textContent = L.error; return; }
      try { render(JSON.parse(x.responseText)); } catch (e) { out.textContent = L.error; }
    };
    x.onerror = function () { out.textContent = L.error; };
    x.send();
  }
  btn.addEventListener("click", function () {
    var open = panel.hasAttribute("hidden");
    if (open) { panel.removeAttribute("hidden"); btn.setAttribute("aria-expanded", "true"); input.focus(); if (!out.childNodes.length) ask(""); }
    else { panel.setAttribute("hidden", ""); btn.setAttribute("aria-expanded", "false"); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !panel.hasAttribute("hidden")) { panel.setAttribute("hidden", ""); btn.setAttribute("aria-expanded", "false"); btn.focus(); }
  });
  form.addEventListener("submit", function (e) { e.preventDefault(); ask(input.value); });
})();
