/* Chargeur : charge les scripts dans l'ordre, avec contrôle d'intégrité (SRI sha384) lorsque la page est servie en http(s).
   En ouverture directe du fichier (démo locale), le navigateur n'autorise pas le SRI : les scripts sont chargés sans. */
(function () {
  "use strict";
  var SCRIPTS = [
    ["vendor/sql-wasm.js", "sha384-8D3Rsfo535FqoC1pHCCQMrNf75UgzyoG/HQm9zOzITRrz3QKzecc2E7JXKGCXoWu"],
    ["vendor/jspdf.umd.min.js", "sha384-qovJwSBbRDPP5cEjCp8S0UP66wrvnjaa60XMOGzTNanrThcrGfXfnZkvgY8N1KT3"],
    ["vendor/jspdf.plugin.autotable.min.js", "sha384-A77YsHWitrPuAj8E0AuB033EXzymUxIajnWKPzrrzqFoYYSCEpFennDUjMG2R1L3"],
    ["js/i18n/fr.js", "sha384-KQRrgaE1rD0ZGjoklCeKEJING9mowufCnEfs2Rd/1/SzDRCfcFVIwYL5kWBhwg7j"],
    ["js/i18n/en.js", "sha384-WAdCWRJ91l5Xy2DkD5p+TErkC+SEr81QmlWUd02ESOZSxMutHLdhB/q6YPAU9HZA"],
    ["js/i18n/es.js", "sha384-FOzW1VV22An74REAng54HlBP+paDmkbEmKYFeRNz0a5lXGNr9KX14vsb9261urCJ"],
    ["js/i18n/de.js", "sha384-8mf8ihCfGI9IqLIojhW5cgqmQ4/XtSliYtCiraMpbrQG5sqNNCDGGgKd7UtHL+4K"],
    ["js/seed.js", "sha384-4xlR2TdAJrxwERAAu4l7Xj/wivt6KM+UOWDQs5kUtCRzd2foeg9lCJfo3TTwcz1r"],
    ["js/app.js", "sha384-y1Z3ebYszsIiJihgDCotjKIF/5qVjYL4hpBFMeRYluj2yx4PVQEGyInD8l/80zLy"]
  ];
  var useSri = location.protocol === "http:" || location.protocol === "https:";
  function next(i) {
    if (i >= SCRIPTS.length) return;
    var s = document.createElement("script");
    s.src = SCRIPTS[i][0];
    if (useSri && SCRIPTS[i][1]) s.integrity = SCRIPTS[i][1];
    s.onload = function () { next(i + 1); };
    s.onerror = function () {
      var b = document.getElementById("boot");
      if (b) b.innerHTML = "<p>Erreur de chargement ou d'intégrité : " + SCRIPTS[i][0] + "</p>";
    };
    document.body.appendChild(s);
  }
  next(0);
})();
