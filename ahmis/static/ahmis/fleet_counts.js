/* AHMIS – flotte : un clic sur un compteur d'éléments ouvre, sous la ligne, la liste
 * des éléments concernés. Sans ce script, le compteur mène à la vue 3D de l'appareil. */
(function () {
  "use strict";
  var links = Array.prototype.slice.call(document.querySelectorAll("[data-heli-count]"));
  links.forEach(function (a) {
    a.setAttribute("role", "button");
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var group = document.getElementById(a.getAttribute("data-heli-count"));
      var row = document.getElementById(a.getAttribute("aria-controls"));
      if (!group || !row) return;
      var open = a.getAttribute("aria-expanded") !== "true";
      links.forEach(function (o) {
        if (o.getAttribute("aria-controls") === row.id) o.setAttribute("aria-expanded", "false");
      });
      Array.prototype.forEach.call(row.querySelectorAll("[data-heli-group]"), function (g) { g.hidden = true; });
      a.setAttribute("aria-expanded", String(open));
      group.hidden = !open;
      row.hidden = !open;
    });
    a.addEventListener("keydown", function (e) {
      if (e.key === " ") { e.preventDefault(); a.click(); }
    });
  });
})();
