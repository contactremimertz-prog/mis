/**
 * @file Application entry point: rendering, routing, event binding, start-up.
 *
 * Routing uses the URL hash (#dashboard, #fleet, ...). Nothing is shown before
 * sign-in. A screen the profile may not see renders the "access denied" view
 * and the attempt is logged once.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    $, esc, t, q, one, logNow, verifyLog, canSee, persist, loadSaved, freshDb, renderSaveState,
    selfTestSha, LANGS, SCREENS, VIEWS, ACTIONS, setLang, closeDlg, dlg, reopen, openRecord,
    loginView, bindLoginView, askProfileSwitch
  } = MIS;

  const isHttp = () => location.protocol === "http:" || location.protocol === "https:";

  /* =========================================================
     Rendering
     ========================================================= */

  /** Current screen id from the URL hash (dashboard by default). */
  function route() {
    const r = location.hash.slice(1);
    return VIEWS[r] && r !== "denied" ? r : "dashboard";
  }

  /** Expected schema version: an older saved database is replaced by the demo data. */
  const SCHEMA_VERSION = "5";

  /** Header elements that only make sense once signed in. */
  const SIGNED_IN_ONLY = ["#search-form", "#user", "#user-label", "#avatar", "#compliance"];

  /** Static texts of the header, language and profile selectors. */
  function renderHeader() {
    document.documentElement.lang = S.lang;
    document.title = t("app.title");
    $("#brand-name").textContent = t("app.name");
    $("#brand-sub").textContent = t("app.sub");
    $("#demo-banner").textContent = t("app.demo");
    $("#lang-label").textContent = t("hdr.lang");
    $("#user-label").textContent = t("hdr.profile");
    $("#gsearch").placeholder = t("hdr.search");
    $("#gsearch").setAttribute("aria-label", t("hdr.search"));
    $("#lang").innerHTML = LANGS.map(([code, name]) => `<option value="${code}" ${code === S.lang ? "selected" : ""}>${name}</option>`).join("");
    SIGNED_IN_ONLY.forEach(sel => { $(sel).hidden = !S.me; });
    if (!S.me) return;
    const users = q("SELECT * FROM users WHERE active=1 ORDER BY role, name");
    $("#user").innerHTML = users.map(u => `<option value="${esc(u.id)}" ${u.id === S.me.id ? "selected" : ""}>${esc(u.name)} · ${esc(t("role." + u.role))}</option>`).join("");
    $("#avatar").textContent = S.me.name.split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase();
  }

  /** Header pill showing whether the audit log chain is intact. */
  function renderCompliancePill() {
    const ok = verifyLog();
    const pill = $("#compliance");
    pill.className = "pill " + (ok ? "ok" : "crit");
    pill.textContent = ok ? t("hdr.compliant") : t("comp.broken");
  }

  /** Side navigation: only the screens the profile may see, with counters. */
  function renderNav(current) {
    const badge = {
      workorders: one("SELECT COUNT(*) n FROM wo WHERE status='awaiting_crs'").n,
      nc: one("SELECT COUNT(*) n FROM nc WHERE status='open'").n
    };
    const link = s => `<a href="#${s}" ${current === s ? 'aria-current="page"' : ""}>${esc(t("nav." + s))}${badge[s] ? `<span class="count">${badge[s]}</span>` : ""}</a>`;
    $("#nav").innerHTML = SCREENS.map(g => {
      const items = g.items.filter(([s]) => canSee(s));
      return items.length ? `<div class="nav-group"><div class="nav-h">${esc(t(g.group))}</div>${items.map(([s]) => link(s)).join("")}</div>` : "";
    }).join("");
  }

  /** Denied view; the attempt is logged once per screen and profile. */
  function renderDenied(screen) {
    const key = screen + S.me.id;
    if (S.lastDenied !== key) {
      S.lastDenied = key;
      try { logNow("denied", "log.denied_screen", { s: "@nav." + screen }); } catch (e) { /* render anyway */ }
    }
    return VIEWS.denied();
  }

  const footer = () => `<footer class="foot"><span>${esc(t("foot.demo"))}</span><span>${esc(t("foot.storage"))}</span></footer>`;

  /** Sign-in page: no navigation, no data. */
  function renderSignedOut() {
    renderHeader();
    renderSaveState();
    $("#nav").innerHTML = "";
    $("#main").innerHTML = loginView() + footer();
    bindLoginView();
  }

  /** Redraws the header, navigation and current screen. */
  function render() {
    if (!S.me) return renderSignedOut();
    const screen = route();
    renderHeader();
    renderCompliancePill();
    renderSaveState();
    renderNav(screen);
    S.exportSpec = null;
    const html = canSee(screen) ? VIEWS[screen]() : renderDenied(screen);
    $("#main").innerHTML = html + footer();
  }

  /* =========================================================
     Events
     ========================================================= */

  /** Delegated clicks: data-act (actions), data-open (record dialogs), data-chip (filters). */
  function onClick(e) {
    const act = e.target.closest("[data-act]");
    if (act) {
      e.preventDefault();
      const handler = ACTIONS[act.dataset.act];
      if (handler) handler(act.dataset.id);
      return;
    }
    const open = e.target.closest("[data-open]");
    if (open && open.dataset.open) {
      e.preventDefault();
      openRecord(open.dataset.open);
      return;
    }
    const chip = e.target.closest("[data-chip]");
    if (chip) {
      S.filters[chip.dataset.chip] = chip.dataset.v;
      render();
    }
  }

  /** Header profile list: the new profile must sign in with its own number. */
  function onProfileChange(e) {
    if (S.me && e.target.value !== S.me.id) askProfileSwitch(e.target.value);
  }

  /** After a successful sign-in: go to the dashboard if the screen is not allowed. */
  function afterSignIn() {
    S.lastDenied = null;
    if (!canSee(route())) location.hash = "#dashboard";
    else render();
  }

  function onLanguageChange(e) {
    setLang(e.target.value);
    render();
    if (dlg().open && S.current) reopen();
  }

  function onSearch(e) {
    e.preventDefault();
    S.filters.search = $("#gsearch").value;
    if (location.hash === "#search") render();
    else location.hash = "#search";
  }

  /** Role select boxes of the users screen. */
  function onDocumentChange(e) {
    if (e.target.dataset && e.target.dataset.role) MIS.changeRole(e.target.dataset.role, e.target.value);
  }

  function bind() {
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", e => {
      if (e.key === "Enter" && e.target.matches && e.target.matches("tr[data-open]")) openRecord(e.target.dataset.open);
    });
    document.addEventListener("change", onDocumentChange);
    dlg().addEventListener("click", e => { if (e.target === dlg()) closeDlg(); });
    dlg().addEventListener("close", () => { S.current = null; });
    $("#lang").addEventListener("change", onLanguageChange);
    $("#user").addEventListener("change", onProfileChange);
    $("#search-form").addEventListener("submit", onSearch);
    window.addEventListener("hashchange", () => { closeDlg(); render(); window.scrollTo(0, 0); });
  }

  /* =========================================================
     Start-up
     ========================================================= */

  /** Fallback: asm.js build of SQLite (no WebAssembly, no extra fetch). */
  async function loadAsm() {
    await new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "vendor/sql-asm.js";
      // Integrity hash of vendor/sql-asm.js, kept up to date by tools/update-sri.py.
      if (isHttp()) s.integrity = "sha384-ur9WCykw0SZNZ8drFEOH/m9+bB+wzKinbF63kpF2yRb4AYvAFbrGvvEC/RfCK8Wp";
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
    return window.initSqlJs();
  }

  /** WebAssembly SQLite when served over http(s); asm.js for file:// or after 8 s. */
  async function loadSqlJs() {
    if (location.protocol === "file:") return loadAsm();
    const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 8000));
    try {
      return await Promise.race([window.initSqlJs({ locateFile: f => "vendor/" + f }), timeout]);
    } catch (e) {
      return loadAsm();
    }
  }

  /** Opens the saved database if it has the current schema, otherwise creates the demo data. */
  async function openDatabase() {
    const saved = await loadSaved();
    if (saved) {
      try {
        S.db = new S.SQL.Database(saved);
        one("SELECT COUNT(*) n FROM log");
        if ((one("SELECT v FROM meta WHERE k='schema'") || {}).v !== SCHEMA_VERSION) throw new Error("schema");
      } catch (e) {
        S.db = null;
      }
    }
    if (!S.db) {
      freshDb();
      persist();
    }
  }

  async function start() {
    try {
      S.SQL = await loadSqlJs();
      await openDatabase();
      S.me = null; // every page load starts signed out
      S.shaOk = await selfTestSha();
      $("#boot").hidden = true;
      $("#app").hidden = false;
      bind();
      render();
    } catch (e) {
      console.error(e);
      $("#boot").innerHTML = `<p class="err">${esc(t("err.boot"))}</p><p class="small muted">${esc(e.message || e)}</p>`;
    }
  }

  ACTIONS.close = closeDlg; // "Close" and "Cancel" buttons of every dialog
  MIS.render = render;
  MIS.afterSignIn = afterSignIn;
  start();
})();
