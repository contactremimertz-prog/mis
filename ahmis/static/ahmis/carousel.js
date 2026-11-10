/* AHMIS – carrousel de la flotte (tableau de bord).
 * Sans ce script, les appareils défilent au doigt ou à la barre de défilement,
 * et le lien « Suivant » de chaque diapositive mène à la suivante. Le script ajoute
 * les flèches, les points et le compteur. Pas de défilement automatique. */
(function () {
  "use strict";
  var root = document.querySelector("[data-carousel]");
  if (!root) return;
  var track = root.querySelector("[data-carousel-track]");
  var slides = Array.prototype.slice.call(track.children);
  var ctrl = root.querySelector("[data-carousel-ctrl]");
  if (!ctrl || slides.length < 2) return;
  var dots = Array.prototype.slice.call(root.querySelectorAll("[data-carousel-dot]"));
  var count = root.querySelector("[data-carousel-count]");
  var total = String(slides.length).padStart(2, "0");
  var index = 0;
  ctrl.hidden = false;

  function go(i) {
    index = (i + slides.length) % slides.length;
    track.scrollTo({ left: slides[index].offsetLeft - track.offsetLeft, behavior: "smooth" });
  }
  function mark(i) {
    index = i;
    dots.forEach(function (d, k) { if (k === i) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current"); });
    slides.forEach(function (s, k) { s.inert = k !== i; });
    if (count) count.textContent = String(i + 1).padStart(2, "0") + " / " + total;
  }
  root.querySelector("[data-carousel-prev]").addEventListener("click", function () { go(index - 1); });
  root.querySelector("[data-carousel-next-btn]").addEventListener("click", function () { go(index + 1); });
  dots.forEach(function (d, k) { d.addEventListener("click", function () { go(k); }); });
  Array.prototype.forEach.call(root.querySelectorAll("[data-carousel-next]"), function (a) {
    a.addEventListener("click", function (e) { e.preventDefault(); go(index + 1); });
  });
  root.addEventListener("keydown", function (e) {
    if (e.target.closest("input, select, textarea")) return;
    if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
  });
  var timer = 0;
  track.addEventListener("scroll", function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      var w = track.clientWidth || 1;
      mark(Math.max(0, Math.min(slides.length - 1, Math.round(track.scrollLeft / w))));
    }, 60);
  }, { passive: true });
  mark(0);
})();
