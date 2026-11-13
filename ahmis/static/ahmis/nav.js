/* AHMIS – menu du haut : une seule rubrique ouverte à la fois, fermeture au clic
 * extérieur ou par Échap, bouton « Menu » sur petit écran, envoi automatique du
 * choix de langue. Sans ce script, les rubriques s'ouvrent et se ferment au clic. */
(function () {
  "use strict";
  var groups = Array.prototype.slice.call(document.querySelectorAll("[data-nav-group]"));
  function closeAll(except) {
    groups.forEach(function (g) { if (g !== except) g.open = false; });
  }
  groups.forEach(function (g) {
    g.addEventListener("toggle", function () { if (g.open) closeAll(g); });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-nav-group]")) closeAll(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var open = groups.filter(function (g) { return g.open; })[0];
    if (open) { open.open = false; open.querySelector("summary").focus(); }
  });
  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.getElementById("topnav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = !document.body.classList.contains("nav-open");
      document.body.classList.toggle("nav-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll("select[data-autosubmit]"), function (s) {
    s.addEventListener("change", function () { s.form.submit(); });
  });
})();
