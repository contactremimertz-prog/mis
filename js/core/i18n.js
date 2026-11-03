/**
 * @file Translation and locale formatting.
 *
 * Texts live in js/i18n/<lang>.js (window.I18N[lang]). A data value that starts
 * with "@" (for example "@part.starter") is a translation key stored in the
 * database, so that seeded data follows the selected language.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;

  /** Languages offered in the header selector: [code, native name]. */
  const LANGS = [["fr", "Français"], ["en", "English"], ["es", "Español"], ["de", "Deutsch"]];
  const LOCALES = { fr: "fr-FR", en: "en-GB", es: "es-ES", de: "de-DE" };

  // Restore the saved language; French is the default (not the browser language).
  try {
    const saved = localStorage.getItem(MIS.KEYS.lang);
    if (saved && window.I18N[saved]) S.lang = saved;
  } catch (e) { /* storage unavailable: keep the default */ }

  /**
   * Translates a key, falling back to French, then to the key itself.
   * `{name}` placeholders are replaced by `params.name`; a parameter that is
   * itself an "@key" string is translated too.
   */
  function t(key, params) {
    const dict = window.I18N[S.lang];
    let text = (dict && dict[key]) ?? window.I18N.fr[key] ?? key;
    if (params) {
      text = text.replace(/\{(\w+)\}/g, (match, name) => {
        const value = params[name];
        if (value === undefined) return match;
        return typeof value === "string" && value[0] === "@" ? t(value.slice(1)) : value;
      });
    }
    return text;
  }

  /** Translates a data value when it is an "@key", returns it unchanged otherwise. */
  const tx = value => (typeof value === "string" && value[0] === "@" ? t(value.slice(1)) : (value ?? ""));

  /** BCP 47 locale of the current language. */
  const loc = () => LOCALES[S.lang];

  /** Short date, e.g. "02 nov. 2026" ("-" when empty). */
  function fD(day) {
    if (!day) return "-";
    const d = new Date(day.length > 10 ? day : day + "T00:00:00");
    return d.toLocaleDateString(loc(), { day: "2-digit", month: "short", year: "numeric" });
  }

  /** Date and time, e.g. "02/11/2026 21:00" ("-" when empty). */
  function fTs(ts) {
    if (!ts) return "-";
    return new Date(ts).toLocaleString(loc(), { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  /** Hours with one decimal ("-" when null). */
  function fH(n) {
    if (n === null || n === undefined) return "-";
    return Number(n).toLocaleString(loc(), { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  /** Integer with locale grouping ("-" when null). */
  function fN(n) {
    if (n === null || n === undefined) return "-";
    return Number(n).toLocaleString(loc());
  }

  /** Changes the UI language and remembers it. */
  function setLang(code) {
    S.lang = code;
    try { localStorage.setItem(MIS.KEYS.lang, code); } catch (e) { /* ignore */ }
  }

  Object.assign(MIS, { LANGS, t, tx, fD, fTs, fH, fN, setLang });
})();
