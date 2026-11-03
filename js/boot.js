/**
 * @file Script loader.
 *
 * Loads the scripts one after another, in dependency order. When the page is
 * served over http(s), each script is checked with Subresource Integrity
 * (sha384); a modified file stops the start-up. Opened directly from disk
 * (file://), browsers do not allow SRI, so scripts load without it.
 * Hashes are kept up to date by tools/update-sri.py.
 */
(function () {
  "use strict";
  var SCRIPTS = [
    // Third-party libraries (vendored, see vendor/*LICENSE*)
    ["vendor/sql-wasm.js", "sha384-8D3Rsfo535FqoC1pHCCQMrNf75UgzyoG/HQm9zOzITRrz3QKzecc2E7JXKGCXoWu"],
    ["vendor/jspdf.umd.min.js", "sha384-qovJwSBbRDPP5cEjCp8S0UP66wrvnjaa60XMOGzTNanrThcrGfXfnZkvgY8N1KT3"],
    ["vendor/jspdf.plugin.autotable.min.js", "sha384-A77YsHWitrPuAj8E0AuB033EXzymUxIajnWKPzrrzqFoYYSCEpFennDUjMG2R1L3"],
    // Translations and demo data
    ["js/i18n/fr.js", "sha384-1yGHMmpNbhTaOz6Pmoz2AtO5CkIz8a1uYsc6umVuwO4VSpt8lK9S1ImjJGuWVKCW"],
    ["js/i18n/en.js", "sha384-rxtHZwPQ4QDFIZm2ZSa2rzTc3sm06w2HAtb36hblxjzlPQRoXnCp+2tjjPSg+KFn"],
    ["js/i18n/es.js", "sha384-ZHjIgvoQ2eEKFqbt50VDE+dFr3pRbKK9q13ZM1NVxa3Qoxea3wxU6jNBtvQ40V+2"],
    ["js/i18n/de.js", "sha384-iX59fYfltkwYmdppeIy2rGoBt2Jzkjsj39wM3UTQqwq+ny0bubKU5Vu7DTWVh3Ql"],
    ["js/seed.js", "sha384-JqOb1PEz6sPag0Zwx9S5znsjP84+r+LwdzJbmgAgYyw9nArThXWDvUEVIcKJB8q8"],
    // Core: namespace and state, i18n, rights, database, audit log, business rules
    ["js/core/util.js", "sha384-IYw9Pe4IwQfV0fI5cqJcuKHZuHyBE1wWVQM9n1ufhN7goTl69nz//50SOQ3AWLpo"],
    ["js/core/i18n.js", "sha384-YHD6XGeteSx1zB8LA//lnCloOfFQiiNy4a6fdKNUniG9dHGfGH/re7fG4+NlMHB4"],
    ["js/core/rights.js", "sha384-KOPobmUhf6WGyYnGOb1Lb5xL1glWQ8FlwWwF/Gs4jgSV81uev2RUtCX7iyK06WpZ"],
    ["js/core/db.js", "sha384-mXjTuiUhkUQt/TKSjuct4y4mgL8aq96VtHWeXZ+m90cmU+/SJa2K+2XSK8OvdYIL"],
    ["js/core/journal.js", "sha384-kvlY3cfv+B5iKPH3f79lgPLEdAjehHlGVwTrHB9nGPl7cKvWbI11ukav5x8eOcL+"],
    ["js/core/rules.js", "sha384-+mH2HFRVLv9rTyQakDcjCrj5ehH3i8J+GA/dFf48yvVUfcM4V+UMnm8t0kDLnwHQ"],
    // User interface: components, screens, record dialogs, signature
    ["js/ui/components.js", "sha384-vb5+VTE21+M1z22bM8kW3mBEatiiiw5sazFZ9CLDzDR8w0j4zMgaqcLqMj8mixHm"],
    ["js/ui/views.js", "sha384-vL9jGyXA3EFTyWJy0KCDQKQ/dSLW00tkn86QskNYR9g8OuMOY0QxUbtsAdyAxKbN"],
    ["js/ui/sheets.js", "sha384-5RdbQWJ9+2FiWhXJFS7RZNjiXST4VjK5tLklN9oNALbS7wE2zjD5J4rSxKpdmttQ"],
    ["js/ui/sign.js", "sha384-vGSOjOGp5TUGvwddScuJSkBvi+tVgGmPdFbj1l2YIDZ4DhQNOIxbgV0wntzQjb3A"],
    // Actions (data-act handlers) and exports
    ["js/actions/workorders.js", "sha384-9bewqWREUmWxiCJevtv+S1YIlew3oZYnIHZ0va/IotFMukjBUtUodAbxT/Gtk48n"],
    ["js/actions/stock.js", "sha384-riUhWM6s5rXHPYdShjbfwJ1f1CVuXhQjBDxWTziOeEt5b5ZqsIjhgR6Z46jgnmR0"],
    ["js/actions/quality.js", "sha384-mXSILRwdUGZoIU7IJK3fV3Ltdb6+YypA72FxeYQd+GwS9N90GpxxMkWlS+V085bB"],
    ["js/actions/admin.js", "sha384-oDOyMPWD84qu6IuhNcief/VrcoBGnmL5p9vpPBR/0+cRazYrDdY5ny2GmzGNnLzm"],
    ["js/export/csv.js", "sha384-fJhEgVhMyA9zPX0o6k5M9PFeRJzXTm5IVZlYGLs2TzzFRr5t8jMzWiSs3VBeJYNd"],
    ["js/export/pdf.js", "sha384-6VDfJJtXWVKtP8AUHZLlvi0RxrUXNObdhYdhgQ72WO+X4Ck1kHNUZLzaZNaQZN8x"],
    // Entry point: rendering, events, start-up
    ["js/main.js", "sha384-XEsstIsjlDouAo7JvokXCHCVozMeZDBLxdw3kKP4Lgl+WbGLGp1QxMtGyh3iMaFR"]
  ];
  var useSri = location.protocol === "http:" || location.protocol === "https:";

  function showError(path) {
    var boot = document.getElementById("boot");
    // User-facing message, in French like the default UI language.
    if (boot) boot.innerHTML = "<p>Erreur de chargement ou d'intégrité : " + path + "</p>";
  }

  function next(i) {
    if (i >= SCRIPTS.length) return;
    var s = document.createElement("script");
    s.src = SCRIPTS[i][0];
    if (useSri && SCRIPTS[i][1]) s.integrity = SCRIPTS[i][1];
    s.onload = function () { next(i + 1); };
    s.onerror = function () { showError(SCRIPTS[i][0]); };
    document.body.appendChild(s);
  }

  next(0);
})();
