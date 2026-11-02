/* MIS démo : application (vanilla JS + SQLite via sql.js).
   Journal d'audit et signature électronique : SIMULÉS côté navigateur (démonstration). */
(function () {
  "use strict";

  /* =========================================================
     Utilitaires
     ========================================================= */
  const $ = s => document.querySelector(s);
  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const TODAY = new Date();
  const isoD = d => { const x = new Date(d); return x.getFullYear() + "-" + String(x.getMonth() + 1).padStart(2, "0") + "-" + String(x.getDate()).padStart(2, "0"); };
  const addDays = n => { const d = new Date(TODAY); d.setDate(d.getDate() + n); return isoD(d); };
  const addMonths = (s, m) => { const d = new Date(s + "T00:00:00"); d.setMonth(d.getMonth() + m); return isoD(d); };
  const daysTo = s => Math.round((new Date(s + "T00:00:00") - new Date(isoD(TODAY) + "T00:00:00")) / 86400000);
  const STORE_KEY = "mis-demo-db-v2", LANG_KEY = "mis-demo-lang", USER_KEY = "mis-demo-user";

  /* SHA-256 (FIPS 180-4), implémentation synchrone pour le chaînage du journal ; contrôlée au démarrage contre WebCrypto. */
  function sha256(str) {
    const K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const bytes = new TextEncoder().encode(str);
    const l = bytes.length, nBlocks = ((l + 9 + 63) >> 6);
    const w = new Uint32Array(nBlocks * 16);
    for (let i = 0; i < l; i++) w[i >> 2] |= bytes[i] << (24 - (i % 4) * 8);
    w[l >> 2] |= 0x80 << (24 - (l % 4) * 8);
    w[nBlocks * 16 - 1] = l * 8; w[nBlocks * 16 - 2] = Math.floor(l / 0x20000000);
    let H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const W = new Uint32Array(64); const r = (x, n) => (x >>> n) | (x << (32 - n));
    for (let b = 0; b < nBlocks; b++) {
      for (let i = 0; i < 16; i++) W[i] = w[b * 16 + i];
      for (let i = 16; i < 64; i++) { const s0 = r(W[i-15],7) ^ r(W[i-15],18) ^ (W[i-15] >>> 3), s1 = r(W[i-2],17) ^ r(W[i-2],19) ^ (W[i-2] >>> 10); W[i] = (W[i-16] + s0 + W[i-7] + s1) | 0; }
      let [a, bb, c, d, e, f, g, h] = H;
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (r(e,6) ^ r(e,11) ^ r(e,25)) + ((e & f) ^ (~e & g)) + K[i] + W[i]) | 0;
        const t2 = ((r(a,2) ^ r(a,13) ^ r(a,22)) + ((a & bb) ^ (a & c) ^ (bb & c))) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = bb; bb = a; a = (t1 + t2) | 0;
      }
      H = [H[0]+a, H[1]+bb, H[2]+c, H[3]+d, H[4]+e, H[5]+f, H[6]+g, H[7]+h].map(x => x | 0);
    }
    return H.map(x => (x >>> 0).toString(16).padStart(8, "0")).join("");
  }
  const GENESIS = "0".repeat(64);
  async function selfTestSha() { // contrôle de l'implémentation contre WebCrypto (si disponible)
    try { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("MIS-démo-é")); return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("") === sha256("MIS-démo-é"); }
    catch (e) { return null; }
  }

  /* =========================================================
     Langues
     ========================================================= */
  const LANGS = [["fr", "Français"], ["en", "English"], ["es", "Español"], ["de", "Deutsch"]];
  const LOCALES = { fr: "fr-FR", en: "en-GB", es: "es-ES", de: "de-DE" };
  let lang = "fr";
  try { const l = localStorage.getItem(LANG_KEY); if (l && window.I18N[l]) lang = l; } catch (e) { }
  function t(key, p) {
    let s = (window.I18N[lang] && window.I18N[lang][key]) ?? (window.I18N.fr[key]) ?? key;
    if (p) s = s.replace(/\{(\w+)\}/g, (m, k) => (p[k] !== undefined ? (typeof p[k] === "string" && p[k][0] === "@" ? t(p[k].slice(1)) : p[k]) : m));
    return s;
  }
  const tx = v => (typeof v === "string" && v[0] === "@" ? t(v.slice(1)) : (v ?? ""));
  const loc = () => LOCALES[lang];
  const fD = s => (s ? new Date(s.length > 10 ? s : s + "T00:00:00").toLocaleDateString(loc(), { day: "2-digit", month: "short", year: "numeric" }) : "-");
  const fTs = s => (s ? new Date(s).toLocaleString(loc(), { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-");
  const fH = n => (n === null || n === undefined ? "-" : Number(n).toLocaleString(loc(), { minimumFractionDigits: 1, maximumFractionDigits: 1 }));
  const fN = n => (n === null || n === undefined ? "-" : Number(n).toLocaleString(loc()));

  /* =========================================================
     Rôles, écrans et droits
     ========================================================= */
  const ROLES = ["CAMO", "PLANNER", "TECH", "CERT", "STORE", "QUALITY", "ADMIN"];
  const PERMS = {
    CAMO: ["fleet.hours", "wo.create", "ad.manage", "mod.manage", "nc.create"],
    PLANNER: ["wo.create", "wo.assign", "fleet.hours", "po.create", "nc.create"],
    TECH: ["wo.start", "card.tech", "part.install", "nc.create"],
    CERT: ["card.insp", "crs.issue", "nc.create"],
    STORE: ["part.receive", "part.doc", "part.issue", "po.create", "po.receive", "nc.create"],
    QUALITY: ["nc.create", "nc.edit", "nc.close", "audit.manage", "doc.approve", "log.export"],
    ADMIN: ["user.manage", "db.reset", "log.export"]
  };
  const ALL = ROLES;
  const SCREENS = [
    { group: "nav.g.overview", items: [["dashboard", ALL], ["fleet", ALL]] },
    { group: "nav.g.camo", items: [["maintenance", ["CAMO", "PLANNER", "CERT", "QUALITY", "ADMIN"]], ["directives", ["CAMO", "PLANNER", "CERT", "QUALITY", "ADMIN"]]] },
    { group: "nav.g.mro", items: [["workorders", ["CAMO", "PLANNER", "TECH", "CERT", "QUALITY", "ADMIN"]], ["certificates", ["CAMO", "PLANNER", "TECH", "CERT", "QUALITY", "ADMIN"]]] },
    { group: "nav.g.p21", items: [["part21", ["CAMO", "CERT", "QUALITY", "ADMIN"]]] },
    { group: "nav.g.log", items: [["stock", ["PLANNER", "TECH", "STORE", "QUALITY", "ADMIN", "CAMO"]], ["orders", ["PLANNER", "STORE", "ADMIN"]]] },
    { group: "nav.g.quality", items: [["nc", ALL], ["audits", ["QUALITY", "CAMO", "ADMIN"]], ["documents", ALL]] },
    { group: "nav.g.admin", items: [["users", ["ADMIN", "QUALITY"]], ["auditlog", ["ADMIN", "QUALITY"]]] }
  ];
  const SCREEN_ROLES = {}; SCREENS.forEach(g => g.items.forEach(([id, r]) => (SCREEN_ROLES[id] = r)));
  SCREEN_ROLES.search = ALL;

  /* =========================================================
     Base de données (sql.js) et persistance locale
     ========================================================= */
  let SQL, db, me, SHA_OK = null;
  const q = (sql, p) => { const st = db.prepare(sql); st.bind(p || []); const out = []; while (st.step()) out.push(st.getAsObject()); st.free(); return out; };
  const one = (sql, p) => q(sql, p)[0] || null;
  const run = (sql, p) => db.run(sql, p || []);

  function idbOpen() {
    return new Promise((res, rej) => { try { const r = indexedDB.open("mis-demo", 1); r.onupgradeneeded = () => r.result.createObjectStore("kv"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); } catch (e) { rej(e); } });
  }
  async function loadSaved() {
    try { const idb = await idbOpen(); return await new Promise(res => { const tr = idb.transaction("kv").objectStore("kv").get(STORE_KEY); tr.onsuccess = () => res(tr.result || null); tr.onerror = () => res(null); }); }
    catch (e) { return null; }
  }
  let saveState = "saved";
  async function persist() {
    saveState = "saving"; renderSaveState();
    try {
      const data = db.export();
      const idb = await idbOpen();
      await new Promise((res, rej) => { const tr = idb.transaction("kv", "readwrite"); tr.objectStore("kv").put(data, STORE_KEY); tr.oncomplete = res; tr.onerror = () => rej(tr.error); });
      saveState = "saved";
    } catch (e) { saveState = "memory"; }
    renderSaveState();
  }
  function renderSaveState() {
    const el = $("#save-state"); if (!el) return;
    el.textContent = t("save." + saveState);
    el.className = "save " + saveState;
  }

  /* Transaction : toute écriture passe ici, avec annulation en cas d'erreur (aucune perte partielle). */
  function tx_(fn) {
    run("BEGIN");
    try { const r = fn(); run("COMMIT"); persist(); return r; }
    catch (e) { try { run("ROLLBACK"); } catch (_) { } throw e; }
  }

  /* Journal d'audit : ajout seul (triggers SQL) + chaînage d'empreintes (simulé). */
  function addLog(uid, action, msg, params, ts) {
    const last = one("SELECT h FROM log ORDER BY id DESC LIMIT 1");
    const prev = last ? last.h : GENESIS;
    const u = one("SELECT role FROM users WHERE id=?", [uid]);
    const role = u ? u.role : "";
    const at = ts || new Date().toISOString();
    const pj = JSON.stringify(params || {});
    const h = sha256([prev, at, uid, role, action, msg, pj].join("|"));
    run("INSERT INTO log(ts,uid,role,action,msg,params,prev,h) VALUES(?,?,?,?,?,?,?,?)", [at, uid, role, action, msg, pj, prev, h]);
  }
  const log = (action, msg, params) => addLog(me.id, action, msg, params);
  function verifyLog() {
    let prev = GENESIS;
    for (const e of q("SELECT * FROM log ORDER BY id")) {
      if (e.prev !== prev) return false;
      if (sha256([prev, e.ts, e.uid, e.role, e.action, e.msg, e.params].join("|")) !== e.h) return false;
      prev = e.h;
    }
    return true;
  }

  function freshDb(keepLog) {
    const d = new SQL.Database();
    db = d;
    window.MIS_SEED.seed(d, TODAY, addDays, addMonths, addLog, { skipLog: !!keepLog });
    if (keepLog) { // le journal existant est recopié tel quel (mêmes empreintes), puis la réinitialisation y est tracée
      const st = d.prepare("INSERT INTO log(ts,uid,role,action,msg,params,prev,h) VALUES(?,?,?,?,?,?,?,?)");
      keepLog.forEach(e => st.run([e.ts, e.uid, e.role, e.action, e.msg, e.params, e.prev, e.h])); st.free();
    }
    return d;
  }

  /* =========================================================
     Règles métier
     ========================================================= */
  const can = p => !!me && me.active && PERMS[me.role].includes(p);
  const canSee = s => !!me && (SCREEN_ROLES[s] || []).includes(me.role);
  const uname = id => { const u = one("SELECT name FROM users WHERE id=?", [id]); return u ? u.name : "-"; };
  const uauth = id => { const u = one("SELECT auth FROM users WHERE id=?", [id]); return u ? u.auth : "-"; };
  /* Les numéros d'habilitation servent de secret de signature (démo) : ils ne sont affichés que masqués, sauf sur le CRS lui-même. */
  const maskAuth = a => (a ? "••••••" : "-"); // masque complet, longueur fixe (revue cybersécurité V2.3)

  function taskRows(reg) {
    return q(`SELECT a.*, m.code, m.title, m.interval_h, m.interval_c, m.interval_m, m.ref, c.hours, c.cycles, c.model
              FROM ac_task a JOIN mp_task m ON m.id=a.task_id JOIN aircraft c ON c.reg=a.reg ${reg ? "WHERE a.reg=?" : ""} ORDER BY a.reg, m.code`, reg ? [reg] : []).map(dueOf);
  }
  function dueOf(r) {
    const remH = r.interval_h ? Math.round((r.last_h + r.interval_h - r.hours) * 10) / 10 : null;
    const remC = r.interval_c ? r.last_c + r.interval_c - r.cycles : null;
    const nextDate = r.interval_m ? addMonths(r.last_date, r.interval_m) : null;
    const remD = nextDate ? daysTo(nextDate) : null;
    let st = "ok";
    if ((remH !== null && remH < 0) || (remC !== null && remC < 0) || (remD !== null && remD < 0)) st = "overdue";
    else if ((remH !== null && remH <= 25) || (remC !== null && remC <= 30) || (remD !== null && remD <= 30)) st = "soon";
    return Object.assign(r, { remH, remC, remD, nextDate, nextH: r.interval_h ? r.last_h + r.interval_h : null, nextC: r.interval_c ? r.last_c + r.interval_c : null, st });
  }
  function adRows(reg) {
    return q(`SELECT x.*, a.title, a.kind, a.interval_h, a.effective, a.comply_days, a.model, c.hours FROM ac_ad x JOIN ad a ON a.id=x.ad_id JOIN aircraft c ON c.reg=x.reg ${reg ? "WHERE x.reg=?" : ""} ORDER BY x.reg`, reg ? [reg] : []).map(r => {
      let st = "ok", due = null, remH = null;
      if (r.status === "open") { due = addDays(daysTo(r.effective) + r.comply_days); st = daysTo(due) < 0 ? "overdue" : daysTo(due) <= 30 ? "soon" : "ok"; }
      else if (r.status === "applied" && r.kind === "repeat") { remH = Math.round((r.last_h + r.interval_h - r.hours) * 10) / 10; st = remH < 0 ? "overdue" : remH <= 25 ? "soon" : "ok"; }
      return Object.assign(r, { st, due, remH });
    });
  }
  function acStatus(a) {
    const aog = one("SELECT 1 FROM nc WHERE reg=? AND level='L1' AND status='open'", [a.reg]);
    const tasks = taskRows(a.reg), ads = adRows(a.reg);
    const arcD = daysTo(a.arc_expiry);
    if (aog) return { k: "crit", code: "aog", tasks, ads, arcD };
    if (tasks.some(x => x.st === "overdue") || ads.some(x => x.st === "overdue") || arcD < 0) return { k: "crit", code: "overdue", tasks, ads, arcD };
    if (tasks.some(x => x.st === "soon") || ads.some(x => x.st === "soon") || arcD <= 30) return { k: "warn", code: "soon", tasks, ads, arcD };
    return { k: "ok", code: "airworthy", tasks, ads, arcD };
  }
  const ST_K = { ok: "ok", soon: "warn", overdue: "crit" };
  const WO_K = { open: "plain", in_progress: "info", awaiting_crs: "warn", closed: "ok" };
  const NC_K = { L1: "crit", L2: "warn", OBS: "info" };
  const PART_K = { stock: "ok", installed: "info", quarantine: "crit", consumed: "plain" };
  const llp = p => { // pièce à durée de vie limitée
    if (p.limit_h) { const pct = Math.round(100 * p.tsn / p.limit_h); return { pct, k: pct >= 95 ? "crit" : pct >= 85 ? "warn" : "ok" }; }
    if (p.limit_date) { const d = daysTo(p.limit_date); return { days: d, k: d < 0 ? "crit" : d <= 30 ? "warn" : "ok" }; }
    return null;
  };
  function nextId(table, prefix, width) {
    const y = TODAY.getFullYear();
    const r = one(`SELECT id FROM ${table} WHERE id LIKE ? ORDER BY id DESC LIMIT 1`, [prefix + "-" + y + "-%"]);
    const n = r ? parseInt(r.id.split("-").pop(), 10) + 1 : 1;
    return prefix + "-" + y + "-" + String(n).padStart(width, "0");
  }

  /* =========================================================
     Composants d'affichage
     ========================================================= */
  const pill = (k, label) => `<span class="pill ${k}">${esc(label)}</span>`;
  const acPill = s => pill(s.k, t("acst." + s.code));
  const remPart = (v, key, f) => (v === null || v === undefined ? null : v < 0 ? t(key + "_over", { n: f(-v) }) : t(key, { n: f(v) }));
  const remText = r => [remPart(r.remH, "rem.h", fH), remPart(r.remC, "rem.c", fN), remPart(r.remD, "rem.d", x => x)].filter(Boolean).join(" · ");
  let EXPORT = null; // tableau courant exportable

  function table(spec) {
    // spec: {id, title, cols:[{h, v:(row)=>text, html?:(row)=>html, cls?}], rows, open?:(row)=>"type:id", empty?}
    EXPORT = spec;
    const head = spec.cols.map(c => `<th scope="col">${esc(t(c.h))}</th>`).join("");
    const body = spec.rows.length ? spec.rows.map(r => {
      const o = spec.open ? spec.open(r) : null;
      return `<tr${o ? ` class="click" tabindex="0" data-open="${esc(o)}"` : ""}>${spec.cols.map(c => `<td class="${c.cls || ""}">${c.html ? c.html(r) : esc(c.v(r))}</td>`).join("")}</tr>`;
    }).join("") : `<tr><td colspan="${spec.cols.length}" class="empty">${esc(t(spec.empty || "tbl.empty"))}</td></tr>`;
    return `<div class="tablewrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  const exportBtns = () => `<button class="btn" data-act="csv">${esc(t("btn.csv"))}</button><button class="btn" data-act="pdf">${esc(t("btn.pdf"))}</button>`;
  function head(titleKey, subKey, actions, p) {
    return `<div class="page-head"><div><h1>${esc(t(titleKey, p))}</h1>${subKey ? `<p class="sub">${esc(t(subKey, p))}</p>` : ""}</div><div class="toolbar">${actions || ""}</div></div>`;
  }
  const chips = (name, values, cur, labelFn) => `<div class="toolbar" role="group">${values.map(v => `<button class="chip" data-chip="${name}" data-v="${esc(v)}" aria-pressed="${cur === v}">${esc(labelFn(v))}</button>`).join("")}</div>`;
  const F = { fleet: "all", wo: "active", stock: "all", nc: "open", search: "" };

  /* =========================================================
     Vues
     ========================================================= */
  const V = {};

  V.dashboard = () => {
    const fleet = q("SELECT * FROM aircraft ORDER BY reg").map(a => Object.assign(a, { s: acStatus(a) }));
    const okN = fleet.filter(a => a.s.code === "airworthy").length;
    const overdue = [];
    fleet.forEach(a => {
      a.s.tasks.filter(x => x.st === "overdue").forEach(x => overdue.push({ reg: a.reg, what: tx(x.title), detail: remText(x) }));
      a.s.ads.filter(x => x.st === "overdue").forEach(x => overdue.push({ reg: a.reg, what: x.ad_id, detail: x.due ? t("ad.due", { d: fD(x.due) }) : remText(x) }));
      if (a.s.arcD < 0) overdue.push({ reg: a.reg, what: "ARC", detail: fD(a.arc_expiry) });
    });
    const soon = [];
    fleet.forEach(a => { a.s.tasks.filter(x => x.st === "soon").forEach(x => soon.push({ a, x })); if (a.s.arcD >= 0 && a.s.arcD <= 30) soon.push({ a, arc: true }); });
    const woOpen = q("SELECT * FROM wo WHERE status!='closed' ORDER BY id DESC");
    const ncOpen = q("SELECT * FROM nc WHERE status='open'");
    const llpAlerts = q("SELECT * FROM part WHERE status IN ('installed','stock')").filter(p => { const l = llp(p); return l && l.k !== "ok"; });
    const docs = q("SELECT status FROM doc"); const docPct = Math.round(100 * docs.filter(d => d.status === "current").length / docs.length);
    const totalH = fleet.reduce((s, a) => s + a.hours, 0);
    EXPORT = { title: "nav.fleet", cols: [{ h: "col.reg", v: a => a.reg }, { h: "col.model", v: a => a.model }, { h: "col.msn", v: a => a.msn }, { h: "col.hours", v: a => fH(a.hours) }, { h: "col.status", v: a => t("acst." + a.s.code) }], rows: fleet };
    return head("dash.hello", "dash.sub", exportBtns(), { name: me.name.split(" ")[0], role: t("role." + me.role), n: fleet.length, h: fH(totalH) }) +
      (overdue.length ? `<section class="alert" role="alert"><strong>${esc(t("dash.overdue_title", { n: overdue.length }))}</strong><ul>${overdue.map(o => `<li><button class="link" data-open="ac:${esc(o.reg)}">${esc(o.reg)}</button> · ${esc(o.what)} · ${esc(o.detail)}</li>`).join("")}</ul></section>` : "") +
      `<section class="kpis">
        <div class="card kpi"><div class="label">${esc(t("kpi.airworthy"))}</div><div class="value ${okN === fleet.length ? "ok" : ""}">${okN} / ${fleet.length}</div><div class="hint">${esc(t("kpi.airworthy_hint", { n: fleet.length - okN }))}</div></div>
        <div class="card kpi"><div class="label">${esc(t("kpi.wo"))}</div><div class="value">${woOpen.length}</div><div class="hint">${esc(t("kpi.wo_hint", { n: woOpen.filter(w => w.status === "awaiting_crs").length }))}</div></div>
        <div class="card kpi"><div class="label">${esc(t("kpi.nc"))}</div><div class="value ${ncOpen.some(n => n.level === "L1") ? "crit" : ncOpen.length ? "warn" : "ok"}">${ncOpen.length}</div><div class="hint">${esc(t("kpi.nc_hint", { n: ncOpen.filter(n => n.level === "L1").length }))}</div></div>
        <div class="card kpi"><div class="label">${esc(t("kpi.docs"))}</div><div class="value ${docPct === 100 ? "ok" : "warn"}">${docPct} %</div><div class="hint">${esc(t("kpi.docs_hint", { n: docs.filter(d => d.status !== "current").length }))}</div></div>
      </section>
      <section class="card"><div class="card-head"><h2>${esc(t("dash.fleet"))}</h2><a class="link" href="#fleet">${esc(t("btn.see_all"))}</a></div>
        <div class="fleet">${fleet.map(a => `<button class="ac" data-open="ac:${esc(a.reg)}"><span class="stripe ${a.s.k}"></span><span class="reg">${esc(a.reg)}</span><span class="mod">${esc(a.model)} · ${esc(a.base)}</span><span class="st ${a.s.k}">${esc(t("acst." + a.s.code))}</span></button>`).join("")}</div>
      </section>
      <section class="grid2">
        <div class="card"><div class="card-head"><h2>${esc(t("dash.soon"))}</h2></div><div class="list">${soon.length ? soon.map(s => `<div><span><button class="link mono" data-open="ac:${esc(s.a.reg)}">${esc(s.a.reg)}</button> <span class="muted">${esc(s.a.model)}</span><br><span class="small muted">${s.arc ? esc(t("dash.arc_soon", { n: s.a.s.arcD, d: fD(s.a.arc_expiry) })) : esc(tx(s.x.title) + " : " + remText(s.x))}</span></span>${pill("warn", t("st.soon"))}</div>`).join("") : `<div class="muted">${esc(t("dash.none"))}</div>`}</div></div>
        <div class="card"><div class="card-head"><h2>${esc(t("dash.llp"))}</h2><a class="link" href="#stock">${esc(t("btn.see_all"))}</a></div><div class="list">${llpAlerts.length ? llpAlerts.map(p => { const l = llp(p); return `<div><span><button class="link" data-open="part:${esc(p.id)}">${esc(tx(p.descr))}</button><br><span class="small muted mono">${esc(p.pn)} · ${esc(p.sn || p.lot)} · ${esc(p.reg || p.location)}</span></span>${pill(l.k, l.pct !== undefined ? t("llp.pct", { n: l.pct }) : t("llp.days", { n: l.days }))}</div>`; }).join("") : `<div class="muted">${esc(t("dash.none"))}</div>`}</div></div>
      </section>
      <section class="grid2">
        <div class="card"><div class="card-head"><h2>${esc(t("dash.wo"))}</h2>${canSee("workorders") ? `<a class="link" href="#workorders">${esc(t("btn.see_all"))}</a>` : ""}</div><div class="list">${woOpen.slice(0, 6).map(w => `<div><span><button class="link mono" data-open="wo:${esc(w.id)}">${esc(w.id)}</button> · <span class="mono">${esc(w.reg)}</span><br><span class="small muted">${esc(tx(w.title))}</span></span>${pill(WO_K[w.status], t("wost." + w.status))}</div>`).join("")}</div></div>
        <div class="card"><div class="card-head"><h2>${esc(t("dash.compliance"))}</h2></div><div class="list">
          <div><span>${esc(t("comp.log"))}</span>${verifyLog() ? pill("ok", t("comp.intact")) : pill("crit", t("comp.broken"))}</div>
          <div><span>${esc(t("comp.sod"))}</span>${pill("ok", t("comp.active"))}</div>
          <div><span>${esc(t("comp.trace"))}</span>${one("SELECT 1 FROM part WHERE form1 IS NULL AND status!='quarantine'") ? pill("crit", t("comp.gap")) : pill("ok", t("comp.complete"))}</div>
          <div><span>${esc(t("comp.docs"))}</span>${pill(docPct === 100 ? "ok" : "warn", docPct === 100 ? t("comp.current") : t("comp.pending"))}</div>
          <div><span>${esc(t("comp.arc"))}</span>${fleet.some(a => a.s.arcD <= 30) ? pill("warn", t("comp.renew")) : pill("ok", t("comp.valid"))}</div>
          <div class="small muted">${esc(t("comp.simnote"))}</div>
        </div></div>
      </section>`;
  };

  V.fleet = () => {
    const models = ["all", ...q("SELECT DISTINCT model FROM aircraft ORDER BY model").map(r => r.model)];
    const rows = q("SELECT * FROM aircraft ORDER BY reg").filter(a => F.fleet === "all" || a.model === F.fleet).map(a => Object.assign(a, { s: acStatus(a) }));
    return head("nav.fleet", "fleet.sub", exportBtns()) +
      `<section class="card"><div class="card-head">${chips("fleet", models, F.fleet, v => (v === "all" ? t("f.all") : v))}</div>` +
      table({ title: "nav.fleet", rows, open: a => "ac:" + a.reg, cols: [
        { h: "col.reg", v: a => a.reg, cls: "mono strong" }, { h: "col.model", v: a => a.model }, { h: "col.msn", v: a => a.msn, cls: "mono" },
        { h: "col.base", v: a => a.base + " · " + tx(a.mission), html: a => `${esc(a.base)}<br><span class="small muted">${esc(tx(a.mission))}</span>` },
        { h: "col.hours", v: a => fH(a.hours), cls: "num" }, { h: "col.cycles", v: a => fN(a.cycles), cls: "num" },
        { h: "col.arc", v: a => fD(a.arc_expiry), html: a => `${esc(fD(a.arc_expiry))}<br><span class="small ${a.s.arcD <= 30 ? "warn-t" : "muted"}">${esc(t("rem.d", { n: a.s.arcD }))}</span>` },
        { h: "col.status", v: a => t("acst." + a.s.code), html: a => acPill(a.s) }] }) + `</section>`;
  };

  V.maintenance = () => {
    const rows = taskRows().sort((a, b) => ({ overdue: 0, soon: 1, ok: 2 }[a.st] - { overdue: 0, soon: 1, ok: 2 }[b.st]) || a.reg.localeCompare(b.reg));
    return head("nav.maintenance", "mp.sub", exportBtns()) +
      `<section class="card"><div class="card-head"><h2>${esc(t("mp.count", { n: rows.length, o: rows.filter(r => r.st === "overdue").length, s: rows.filter(r => r.st === "soon").length }))}</h2></div>` +
      table({ title: "nav.maintenance", rows, open: r => "ac:" + r.reg, cols: [
        { h: "col.reg", v: r => r.reg, cls: "mono strong" }, { h: "col.model", v: r => r.model }, { h: "col.task", v: r => tx(r.title) },
        { h: "col.interval", v: r => [r.interval_h ? r.interval_h + " h" : null, r.interval_c ? r.interval_c + " cyc" : null, r.interval_m ? t("unit.months", { n: r.interval_m }) : null].filter(Boolean).join(" / ") },
        { h: "col.last", v: r => fD(r.last_date), html: r => `${esc(fD(r.last_date))}<br><span class="small muted num">${esc(fH(r.last_h))} h · ${esc(fN(r.last_c))} cyc</span>` },
        { h: "col.remaining", v: r => remText(r), cls: "num small" },
        { h: "col.status", v: r => t("st." + r.st), html: r => pill(ST_K[r.st], t("st." + r.st)) }] }) + `</section>`;
  };

  V.directives = () => {
    const rows = adRows();
    return head("nav.directives", "ad.sub", exportBtns()) + `<section class="card">` +
      table({ title: "nav.directives", rows, open: r => "ac:" + r.reg, cols: [
        { h: "col.ad", v: r => r.ad_id, cls: "mono strong" }, { h: "col.reg", v: r => r.reg, cls: "mono" }, { h: "col.model", v: r => r.model },
        { h: "col.subject", v: r => tx(r.title) }, { h: "col.kind", v: r => t("adk." + r.kind) },
        { h: "col.compliance", v: r => (r.status === "open" ? t("ad.due", { d: fD(r.due) }) : r.status === "applied" ? (r.kind === "repeat" ? t("rem.h", { n: fH(r.remH) }) : fD(r.last_date)) : "-") },
        { h: "col.status", v: r => t("ads." + r.status), html: r => pill(r.st === "overdue" ? "crit" : r.status === "open" ? "warn" : r.status === "applied" ? "ok" : "plain", r.st === "overdue" ? t("st.overdue") : t("ads." + r.status)) }] }) +
      `<p class="small muted">${esc(t("ad.note"))}</p></section>`;
  };

  V.workorders = () => {
    const tabs = ["active", "awaiting_crs", "closed", "all"];
    const rows = q("SELECT w.*, c.model, c.msn FROM wo w JOIN aircraft c ON c.reg=w.reg ORDER BY w.id DESC").filter(w => F.wo === "all" || (F.wo === "active" ? w.status !== "closed" : w.status === F.wo));
    return head("nav.workorders", "wo.sub", (can("wo.create") ? `<button class="btn primary" data-act="new-wo">${esc(t("wo.new"))}</button>` : "") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("wo", tabs, F.wo, v => t("wof." + v))}</div>` +
      table({ title: "nav.workorders", rows, open: w => "wo:" + w.id, cols: [
        { h: "col.wo", v: w => w.id, cls: "mono strong" }, { h: "col.aircraft", v: w => w.reg + " · " + w.model + " MSN " + w.msn, html: w => `<span class="mono">${esc(w.reg)}</span> <span class="muted">· ${esc(w.model)} MSN ${esc(w.msn)}</span>` },
        { h: "col.task", v: w => tx(w.title) }, { h: "col.kind", v: w => t("wok." + w.kind) }, { h: "col.assignee", v: w => (w.assignee ? uname(w.assignee) : "-") },
        { h: "col.cards", v: w => { const c = one("SELECT COUNT(*) n, SUM(insp IS NOT NULL) d FROM card WHERE wo_id=?", [w.id]); return (c.d || 0) + "/" + c.n; }, cls: "num" },
        { h: "col.status", v: w => t("wost." + w.status), html: w => pill(WO_K[w.status], t("wost." + w.status)) }] }) + `</section>`;
  };

  V.certificates = () => {
    const rows = q("SELECT * FROM crs ORDER BY at DESC");
    return head("nav.certificates", "crs.sub", exportBtns()) + `<section class="card">` +
      table({ title: "nav.certificates", rows, open: r => "crs:" + r.id, cols: [
        { h: "col.crs", v: r => r.id, cls: "mono strong" }, { h: "col.wo", v: r => r.wo_id, cls: "mono" }, { h: "col.reg", v: r => r.reg, cls: "mono" },
        { h: "col.certifier", v: r => uname(r.certifier) + " (" + maskAuth(r.cert_auth) + (r.cert_cat ? " " + r.cert_cat : "") + ")" }, { h: "col.approval", v: r => r.approval, cls: "mono" }, { h: "col.date", v: r => fTs(r.at) },
        { h: "col.hours", v: r => fH(r.hours), cls: "num" }] }) + `</section>`;
  };

  V.part21 = () => {
    const rows = q("SELECT * FROM modif ORDER BY id DESC");
    return head("nav.part21", "p21.sub", exportBtns()) + `<section class="card"><div class="card-head"><h2>${esc(t("p21.mods"))}</h2></div>` +
      table({ title: "nav.part21", rows, cols: [
        { h: "col.mod", v: r => r.id, cls: "mono strong" }, { h: "col.subject", v: r => tx(r.title) }, { h: "col.reg", v: r => r.reg || t("p21.fleetwide"), cls: "mono" },
        { h: "col.class", v: r => t("cls." + r.cls), html: r => pill(r.cls === "major" ? "warn" : "info", t("cls." + r.cls)) },
        { h: "col.approval", v: r => r.approval, cls: "mono" }, { h: "col.status", v: r => t("mods." + r.status), html: r => pill(r.status === "embodied" ? "ok" : r.status === "in_work" ? "info" : "plain", t("mods." + r.status)) },
        { h: "", v: () => "", html: r => (can("mod.manage") && r.status !== "embodied" ? `<button class="btn small" data-act="mod-next" data-id="${esc(r.id)}">${esc(t("p21.next"))}</button>` : "") }] }) +
      `</section><section class="card"><div class="card-head"><h2>${esc(t("p21.form1"))}</h2></div><p class="sub">${esc(t("p21.form1_sub"))}</p>` +
      tableNoExport({ rows: q("SELECT * FROM part ORDER BY received DESC"), open: p => "part:" + p.id, cols: [
        { h: "col.form1", v: p => p.form1 || "-", html: p => (p.form1 ? `<span class="mono">${esc(p.form1)}</span>` : pill("crit", t("p.missing"))) },
        { h: "col.pn", v: p => p.pn, cls: "mono" }, { h: "col.descr", v: p => tx(p.descr) }, { h: "col.received", v: p => fD(p.received) }] }) + `</section>`;
  };
  function tableNoExport(spec) { const keep = EXPORT; const h = table(spec); EXPORT = keep; return h; }

  V.stock = () => {
    const f = ["all", "stock", "installed", "quarantine", "llp"];
    const rows = q("SELECT * FROM part ORDER BY id").filter(p => F.stock === "all" || (F.stock === "llp" ? (llp(p) && llp(p).k !== "ok") : p.status === F.stock));
    return head("nav.stock", "stock.sub", (can("part.receive") ? `<button class="btn primary" data-act="receive">${esc(t("stock.receive"))}</button>` : "") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("stock", f, F.stock, v => t("sf." + v))}</div>` +
      table({ title: "nav.stock", rows, open: p => "part:" + p.id, cols: [
        { h: "col.pn", v: p => p.pn, cls: "mono strong" }, { h: "col.descr", v: p => tx(p.descr) }, { h: "col.snlot", v: p => p.sn || ("Lot " + p.lot), cls: "mono" },
        { h: "col.qty", v: p => fN(p.qty), cls: "num" },
        { h: "col.form1", v: p => p.form1 || t("p.missing"), html: p => (p.form1 ? `<span class="mono">${esc(p.form1)}</span>` : pill("crit", t("p.missing"))) },
        { h: "col.location", v: p => p.reg || p.location || "-", cls: "mono" },
        { h: "col.life", v: p => { const l = llp(p); return !l ? "-" : l.pct !== undefined ? l.pct + " %" : t("llp.days", { n: l.days }); }, html: p => { const l = llp(p); if (!l) return `<span class="muted">-</span>`; return l.pct !== undefined ? `<div class="barrow"><div class="bar ${l.k}"><i style="width:${Math.min(100, l.pct)}%"></i></div><span class="num small">${l.pct} %</span></div>` : pill(l.k, t("llp.days", { n: l.days })); } },
        { h: "col.status", v: p => t("ps." + p.status), html: p => pill(PART_K[p.status], t("ps." + p.status)) }] }) + `</section>`;
  };

  V.orders = () => {
    const rows = q("SELECT * FROM po ORDER BY id DESC");
    return head("nav.orders", "po.sub", (can("po.create") ? `<button class="btn primary" data-act="new-po">${esc(t("po.new"))}</button>` : "") + exportBtns()) + `<section class="card">` +
      table({ title: "nav.orders", rows, cols: [
        { h: "col.po", v: r => r.id, cls: "mono strong" }, { h: "col.pn", v: r => r.pn, cls: "mono" }, { h: "col.descr", v: r => tx(r.descr) }, { h: "col.qty", v: r => fN(r.qty), cls: "num" },
        { h: "col.supplier", v: r => tx(r.supplier) }, { h: "col.date", v: r => fD(r.ordered) },
        { h: "col.status", v: r => t("pos." + r.status), html: r => pill(r.status === "received" ? "ok" : r.status === "awaiting_doc" ? "crit" : "info", t("pos." + r.status)) },
        { h: "", v: () => "", html: r => (can("po.receive") && r.status === "ordered" ? `<button class="btn small" data-act="po-receive" data-id="${esc(r.id)}">${esc(t("po.receive"))}</button>` : "") }] }) + `</section>`;
  };

  V.nc = () => {
    const f = ["open", "closed", "all"];
    const rows = q("SELECT * FROM nc ORDER BY id DESC").filter(n => F.nc === "all" || n.status === F.nc);
    return head("nav.nc", "nc.sub", (can("nc.create") ? `<button class="btn primary" data-act="new-nc">${esc(t("nc.new"))}</button>` : "") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("nc", f, F.nc, v => t("ncf." + v))}</div>` +
      table({ title: "nav.nc", rows, open: n => "nc:" + n.id, cols: [
        { h: "col.nc", v: n => n.id, cls: "mono strong" }, { h: "col.level", v: n => t("lvl." + n.level), html: n => pill(NC_K[n.level], t("lvl." + n.level)) },
        { h: "col.descr", v: n => tx(n.descr), cls: "wide" }, { h: "col.reg", v: n => n.reg || "-", cls: "mono" },
        { h: "col.due", v: n => fD(n.due), html: n => { const d = daysTo(n.due); return `${esc(fD(n.due))}${n.status === "open" ? `<br><span class="small ${d < 0 ? "crit-t" : d <= 7 ? "warn-t" : "muted"}">${esc(d < 0 ? t("late", { n: -d }) : t("rem.d", { n: d }))}</span>` : ""}`; } },
        { h: "col.status", v: n => t("ncs." + n.status), html: n => pill(n.status === "open" ? "warn" : "ok", t("ncs." + n.status)) }] }) + `</section>`;
  };

  V.audits = () => {
    const rows = q("SELECT * FROM audit ORDER BY planned");
    return head("nav.audits", "aud.sub", (can("audit.manage") ? `<button class="btn primary" data-act="new-audit">${esc(t("aud.new"))}</button>` : "") + exportBtns()) + `<section class="card">` +
      table({ title: "nav.audits", rows, cols: [
        { h: "col.audit", v: r => r.id, cls: "mono strong" }, { h: "col.subject", v: r => tx(r.title) }, { h: "col.scope", v: r => tx(r.scope) },
        { h: "col.date", v: r => fD(r.planned) }, { h: "col.auditor", v: r => uname(r.auditor) }, { h: "col.findings", v: r => fN(r.findings), cls: "num" },
        { h: "col.status", v: r => t("auds." + r.status), html: r => pill(r.status === "closed" ? "ok" : r.status === "in_progress" ? "info" : "plain", t("auds." + r.status)) },
        { h: "", v: () => "", html: r => (can("audit.manage") && r.status !== "closed" ? `<button class="btn small" data-act="audit-next" data-id="${esc(r.id)}">${esc(t(r.status === "planned" ? "aud.start" : "aud.close"))}</button>` : "") }] }) + `</section>`;
  };

  V.documents = () => {
    const rows = q("SELECT * FROM doc ORDER BY id");
    return head("nav.documents", "doc.sub", exportBtns()) + `<section class="card">` +
      table({ title: "nav.documents", rows, cols: [
        { h: "col.ref", v: r => r.id, cls: "mono strong" }, { h: "col.subject", v: r => tx(r.title) }, { h: "col.category", v: r => tx(r.kind) },
        { h: "col.rev", v: r => r.rev + (r.pending ? " (" + r.pending + ")" : ""), html: r => `${esc(r.rev)}${r.pending ? `<br><span class="small muted">${esc(t("doc.received", { r: r.pending }))}</span>` : ""}` },
        { h: "col.date", v: r => fD(r.rev_date) }, { h: "col.status", v: r => t("docs." + r.status), html: r => pill(r.status === "current" ? "ok" : "warn", t("docs." + r.status)) },
        { h: "", v: () => "", html: r => (r.pending && can("doc.approve") ? `<button class="btn small" data-act="doc-approve" data-id="${esc(r.id)}">${esc(t("doc.approve", { r: r.pending }))}</button>` : "") }] }) + `</section>`;
  };

  V.users = () => {
    const rows = q("SELECT * FROM users ORDER BY role, name");
    const edit = can("user.manage");
    return head("nav.users", "users.sub", exportBtns()) + `<section class="card">` +
      table({ title: "nav.users", rows, cols: [
        { h: "col.name", v: u => u.name, cls: "strong" },
        { h: "col.role", v: u => t("role." + u.role), html: u => (edit && u.id !== me.id ? `<label class="sr-only" for="role-${esc(u.id)}">${esc(t("col.role"))}</label><select id="role-${esc(u.id)}" class="input" data-role="${esc(u.id)}">${ROLES.map(r => `<option value="${r}" ${u.role === r ? "selected" : ""}>${esc(t("role." + r))}</option>`).join("")}</select>` : esc(t("role." + u.role))) },
        { h: "col.auth", v: u => maskAuth(u.auth), cls: "mono" }, { h: "col.cat", v: u => u.cat || "-" }, { h: "col.status", v: u => t(u.active ? "u.active" : "u.suspended"), html: u => pill(u.active ? "ok" : "plain", t(u.active ? "u.active" : "u.suspended")) },
        { h: "", v: () => "", html: u => (edit && u.id !== me.id ? `<button class="btn small" data-act="user-toggle" data-id="${esc(u.id)}">${esc(t(u.active ? "u.suspend" : "u.reactivate"))}</button>` : u.id === me.id ? `<span class="small muted">${esc(t("u.you"))}</span>` : "") }] }) +
      `</section><section class="card"><div class="card-head"><h2>${esc(t("users.matrix"))}</h2></div><div class="tablewrap"><table class="matrix"><thead><tr><th scope="col">${esc(t("col.screen"))}</th>${ROLES.map(r => `<th scope="col">${esc(t("role." + r))}</th>`).join("")}</tr></thead><tbody>${SCREENS.flatMap(g => g.items).map(([s, rr]) => `<tr><td>${esc(t("nav." + s))}</td>${ROLES.map(r => (rr.includes(r) ? `<td class="yes"><span aria-hidden="true">●</span><span class="sr-only">${esc(t("yes"))}</span></td>` : `<td class="no"><span aria-hidden="true">-</span><span class="sr-only">${esc(t("no"))}</span></td>`)).join("")}</tr>`).join("")}</tbody></table></div>
      ${edit ? `<div class="danger"><div><strong>${esc(t("admin.reset"))}</strong><p class="small muted">${esc(t("admin.reset_sub"))}</p></div><div class="toolbar"><button class="btn" data-act="db-download">${esc(t("admin.download"))}</button><button class="btn danger-btn" data-act="db-reset">${esc(t("admin.reset_btn"))}</button></div></div>` : ""}</section>`;
  };

  V.auditlog = () => {
    const rows = q("SELECT * FROM log ORDER BY id DESC");
    const ok = verifyLog();
    const html = head("nav.auditlog", "log.sub", `<button class="btn" data-act="verify">${esc(t("log.verify"))}</button>` + (can("log.export") ? exportBtns() : "")) +
      `<div class="notice">${esc(t("log.simulated"))}</div>
      <section class="card"><div class="card-head"><h2>${esc(t("log.anchor_title"))}</h2><button class="btn small" data-act="copy-anchor">${esc(t("log.anchor_copy"))}</button></div>
        <p class="sub">${esc(t("log.anchor_sub"))}</p><p class="mono anchor" id="anchor">${esc(rows.length ? rows[0].h : "-")}</p>
        <p class="small muted">${esc(t("log.anchor_meta", { n: rows.length, d: rows.length ? fTs(rows[0].ts) : "-" }))}</p></section>
      <section class="card"><div class="card-head"><h2>${esc(t("log.count", { n: rows.length }))}</h2>${ok ? pill("ok", t("comp.intact")) : pill("crit", t("comp.broken"))}</div>` +
      table({ title: "nav.auditlog", rows, cols: [
        { h: "col.date", v: e => fTs(e.ts), cls: "mono" }, { h: "col.user", v: e => uname(e.uid) }, { h: "col.role", v: e => (e.role ? t("role." + e.role) : "-"), cls: "muted" },
        { h: "col.action", v: e => t("act." + e.action), html: e => (e.action === "denied" || e.action === "sign_fail" ? pill("crit", t("act." + e.action)) : `<strong>${esc(t("act." + e.action))}</strong>`) },
        { h: "col.detail", v: e => t(e.msg, JSON.parse(e.params || "{}")), cls: "wide" }, { h: "col.hash", v: e => e.h, html: e => `<span class="mono muted" title="${esc(e.prev)}">${esc(e.h.slice(0, 10))}</span>` }] }) + `</section>`;
    // l'export porte l'empreinte de tête, à conserver hors du poste pour détecter une réécriture complète de la chaîne
    if (EXPORT && rows.length) EXPORT.note = t("log.anchor_export", { h: rows[0].h, n: rows.length, d: fTs(rows[0].ts) });
    return html;
  };

  V.search = () => {
    const s = F.search.trim(); const like = "%" + s + "%";
    if (s.length < 2) return head("search.title", "search.short");
    const groups = [];
    const acs = q("SELECT * FROM aircraft WHERE reg LIKE ? OR msn LIKE ? OR model LIKE ? OR base LIKE ?", [like, like, like, like]);
    if (acs.length) groups.push(["nav.fleet", acs.map(a => ({ o: "ac:" + a.reg, a: a.reg, b: a.model + " · MSN " + a.msn + " · " + a.base }))]);
    if (canSee("workorders")) { const w = q("SELECT * FROM wo").filter(w => (w.id + " " + w.reg + " " + tx(w.title)).toLowerCase().includes(s.toLowerCase())); if (w.length) groups.push(["nav.workorders", w.map(x => ({ o: "wo:" + x.id, a: x.id, b: x.reg + " · " + tx(x.title) }))]); }
    if (canSee("stock")) { const p = q("SELECT * FROM part").filter(p => [p.pn, p.sn, p.lot, p.form1, tx(p.descr), p.reg].join(" ").toLowerCase().includes(s.toLowerCase())); if (p.length) groups.push(["nav.stock", p.map(x => ({ o: "part:" + x.id, a: x.pn, b: tx(x.descr) + " · " + (x.sn || x.lot) }))]); }
    const n = q("SELECT * FROM nc").filter(n => [n.id, n.reg, tx(n.descr)].join(" ").toLowerCase().includes(s.toLowerCase())); if (n.length) groups.push(["nav.nc", n.map(x => ({ o: "nc:" + x.id, a: x.id, b: tx(x.descr) }))]);
    const d = q("SELECT * FROM doc").filter(d => [d.id, tx(d.title)].join(" ").toLowerCase().includes(s.toLowerCase())); if (d.length) groups.push(["nav.documents", d.map(x => ({ o: "", a: x.id, b: tx(x.title) }))]);
    const total = groups.reduce((t, g) => t + g[1].length, 0);
    return head("search.title", "search.count", "", { n: total, q: s }) + (groups.length ? groups.map(([g, items]) => `<section class="card"><div class="card-head"><h2>${esc(t(g))}</h2></div><div class="list">${items.map(i => `<div>${i.o ? `<button class="link mono" data-open="${esc(i.o)}">${esc(i.a)}</button>` : `<span class="mono strong">${esc(i.a)}</span>`}<span class="muted" style="flex:1">${esc(i.b)}</span></div>`).join("")}</div></section>`).join("") : `<section class="card empty">${esc(t("search.none"))}</section>`);
  };

  V.denied = () => `<section class="card empty"><h1>${esc(t("denied.title"))}</h1><p class="sub">${esc(t("denied.sub", { role: t("role." + me.role) }))}</p><p><a class="btn" href="#dashboard">${esc(t("nav.dashboard"))}</a></p></section>`;

  /* =========================================================
     Fiches (boîtes de dialogue)
     ========================================================= */
  const dlg = () => $("#dlg");
  function openDlg(title, body, foot) {
    $("#dlg-inner").innerHTML = `<div class="dlg-head"><h2 id="dlg-title">${esc(title)}</h2><button class="btn small" data-act="close" aria-label="${esc(t("btn.close"))}">${esc(t("btn.close"))}</button></div><div class="dlg-body">${body}</div>${foot ? `<div class="dlg-foot">${foot}</div>` : ""}`;
    if (!dlg().open) dlg().showModal();
  }
  const closeDlg = () => { if (dlg().open) dlg().close(); };
  let CURRENT = null; // fiche ouverte, pour la rafraîchir
  const kv = pairs => `<dl class="kv">${pairs.map(([k, v]) => `<div><dt>${esc(t(k))}</dt><dd>${v}</dd></div>`).join("")}</dl>`;

  function showAircraft(reg) {
    const a = one("SELECT * FROM aircraft WHERE reg=?", [reg]); if (!a) return;
    CURRENT = "ac:" + reg;
    const s = acStatus(a);
    const wos = q("SELECT * FROM wo WHERE reg=? ORDER BY id DESC", [reg]);
    const parts = q("SELECT * FROM part WHERE reg=? AND status='installed'", [reg]);
    const ncs = q("SELECT * FROM nc WHERE reg=? AND status='open'", [reg]);
    const crs = q("SELECT * FROM crs WHERE reg=? ORDER BY at DESC", [reg]);
    openDlg(`${a.reg} · ${a.model}`,
      `<div class="toolbar">${acPill(s)}</div>
      ${s.code === "overdue" ? `<div class="notice crit">${esc(t("ac.overdue_notice"))}</div>` : ""}
      ${ncs.map(n => `<div class="notice crit"><strong>${esc(n.id)}</strong> · ${esc(tx(n.descr))}</div>`).join("")}
      ${kv([["col.msn", `<span class="mono">${esc(a.msn)}</span>`], ["col.year", esc(a.mfg_year)], ["col.base", esc(a.base) + " · " + esc(tx(a.mission))], ["col.hours", esc(fH(a.hours)) + " h"], ["col.cycles", esc(fN(a.cycles))], ["col.arc", esc(fD(a.arc_expiry)) + ` <span class="small muted">(${esc(t("rem.d", { n: s.arcD }))})</span>`]])}
      <h3>${esc(t("ac.tasks"))}</h3>${tableNoExport({ rows: s.tasks, cols: [{ h: "col.task", v: r => tx(r.title) }, { h: "col.remaining", v: r => remText(r), cls: "small num" }, { h: "col.status", v: r => "", html: r => pill(ST_K[r.st], t("st." + r.st)) }] })}
      <h3>${esc(t("ac.ads"))}</h3>${tableNoExport({ rows: s.ads, cols: [{ h: "col.ad", v: r => r.ad_id, cls: "mono" }, { h: "col.subject", v: r => tx(r.title) }, { h: "col.status", v: r => "", html: r => pill(r.st === "overdue" ? "crit" : r.status === "open" ? "warn" : "ok", r.st === "overdue" ? t("st.overdue") : t("ads." + r.status)) }] })}
      <h3>${esc(t("ac.wos"))}</h3><div class="list">${wos.map(w => `<div><button class="link mono" data-open="wo:${esc(w.id)}">${esc(w.id)}</button><span style="flex:1">${esc(tx(w.title))}</span>${pill(WO_K[w.status], t("wost." + w.status))}</div>`).join("") || `<div class="muted">${esc(t("tbl.empty"))}</div>`}</div>
      <h3>${esc(t("ac.parts"))}</h3><div class="list">${parts.map(p => `<div><button class="link" data-open="part:${esc(p.id)}">${esc(tx(p.descr))}</button><span class="mono muted">${esc(p.pn)} · ${esc(p.sn || p.lot)}</span></div>`).join("") || `<div class="muted">${esc(t("tbl.empty"))}</div>`}</div>
      <h3>${esc(t("ac.crs"))}</h3><div class="list">${crs.map(c => `<div><button class="link mono" data-open="crs:${esc(c.id)}">${esc(c.id)}</button><span class="muted">${esc(fTs(c.at))}</span></div>`).join("") || `<div class="muted">${esc(t("tbl.empty"))}</div>`}</div>
      ${can("fleet.hours") ? `<h3>${esc(t("ac.flight"))}</h3><form id="f-hours" class="fields" novalidate>
        <div class="field"><label for="h-add">${esc(t("ac.hours_add"))}</label><input id="h-add" class="input" type="number" step="0.1" min="0.1" max="24" value="1.5" required></div>
        <div class="field"><label for="c-add">${esc(t("ac.cycles_add"))}</label><input id="c-add" class="input" type="number" step="1" min="0" max="60" value="2" required></div>
        <div class="field end"><button class="btn primary" type="submit">${esc(t("ac.save_flight"))}</button></div><p class="err" id="h-err" role="alert"></p></form>` : ""}`,
      `<button class="btn" data-act="pdf-ac" data-id="${esc(reg)}">${esc(t("btn.pdf_sheet"))}</button>`);
    const f = $("#f-hours");
    if (f) f.addEventListener("submit", e => {
      e.preventDefault();
      const h = parseFloat($("#h-add").value), c = parseInt($("#c-add").value, 10);
      if (!(h >= 0.1 && h <= 24)) return ($("#h-err").textContent = t("err.hours"));
      if (!(c >= 0 && c <= 60) || String(c) !== String($("#c-add").value).trim()) return ($("#h-err").textContent = t("err.cycles"));
      if (s.code === "aog") return ($("#h-err").textContent = t("err.aog"));
      safe(() => tx_(() => {
        run("UPDATE aircraft SET hours=round(hours+?,1), cycles=cycles+? WHERE reg=?", [h, c, reg]);
        run("UPDATE part SET tsn=round(tsn+?,1) WHERE reg=? AND status='installed' AND tsn IS NOT NULL", [h, reg]);
        log("flight", "log.flight", { reg, h: fH(h), c });
      }), "toast.flight", { reg });
    });
  }

  function showWo(id) {
    const w = one("SELECT w.*, c.model, c.msn, c.hours, c.cycles FROM wo w JOIN aircraft c ON c.reg=w.reg WHERE w.id=?", [id]); if (!w) return;
    CURRENT = "wo:" + id;
    const cards = q("SELECT * FROM card WHERE wo_id=? ORDER BY seq", [id]);
    const parts = q("SELECT * FROM part WHERE wo_id=?", [id]);
    const mod = w.mod_id ? one("SELECT * FROM modif WHERE id=?", [w.mod_id]) : null;
    const blocked = w.kind === "mod" && !one("SELECT 1 FROM part WHERE wo_id=? AND status='installed'", [id]) && one("SELECT 1 FROM part WHERE pn='125A55-0012-01' AND status='quarantine'");
    let foot = "";
    if (w.status === "open" && can("wo.start")) foot += `<button class="btn primary" data-act="wo-start" data-id="${esc(id)}">${esc(t("wo.start"))}</button>`;
    if (w.status === "open" && can("wo.assign")) foot += `<button class="btn" data-act="wo-assign" data-id="${esc(id)}">${esc(t("wo.assign"))}</button>`;
    if (w.status === "in_progress" && can("part.install")) foot += `<button class="btn" data-act="wo-part" data-id="${esc(id)}">${esc(t("wo.install"))}</button>`;
    if (w.status === "awaiting_crs" && can("crs.issue")) foot += `<button class="btn primary" data-act="crs" data-id="${esc(id)}">${esc(t("wo.crs"))}</button>`;
    if (w.crs_id) foot += `<button class="btn" data-open="crs:${esc(w.crs_id)}">${esc(t("wo.view_crs"))}</button>`;
    foot += `<button class="btn" data-act="pdf-wo" data-id="${esc(id)}">${esc(t("btn.pdf_sheet"))}</button>`;
    const signBtn = (c, kind) => {
      if (w.status !== "in_progress") return `<span class="muted">-</span>`;
      if (kind === "tech") return can("card.tech") ? `<button class="btn small" data-act="card-tech" data-id="${c.id}">${esc(t("card.sign"))}</button>` : `<span class="muted small">${esc(t("card.wait_tech"))}</span>`;
      if (!c.tech) return `<span class="muted small">${esc(t("card.wait_tech"))}</span>`;
      return can("card.insp") ? `<button class="btn small" data-act="card-insp" data-id="${c.id}">${esc(t("card.countersign"))}</button>` : `<span class="muted small">${esc(t("card.wait_insp"))}</span>`;
    };
    openDlg(w.id,
      `<div class="toolbar">${pill(WO_K[w.status], t("wost." + w.status))}${blocked ? pill("crit", t("wo.blocked")) : ""}</div>
      ${kv([["col.aircraft", `<button class="link mono" data-open="ac:${esc(w.reg)}">${esc(w.reg)}</button> · ${esc(w.model)} MSN ${esc(w.msn)}`], ["col.kind", esc(t("wok." + w.kind))], ["col.task", esc(tx(w.title))], ["col.opened", esc(fD(w.opened))], ["col.planner", esc(uname(w.planner))], ["col.assignee", esc(w.assignee ? uname(w.assignee) : "-")]])}
      ${mod ? `<div class="notice">${esc(t("wo.mod_link", { id: mod.id, a: mod.approval }))}</div>` : ""}
      ${blocked ? `<div class="notice crit">${esc(t("wo.blocked_notice"))}</div>` : ""}
      <h3>${esc(t("wo.cards"))}</h3>
      <div class="tablewrap"><table><thead><tr><th>#</th><th>${esc(t("col.task"))}</th><th>${esc(t("card.tech"))}</th><th>${esc(t("card.insp"))}</th></tr></thead><tbody>
      ${cards.map(c => `<tr><td class="num">${c.seq}</td><td>${esc(tx(c.title))}</td>
        <td>${c.tech ? `<span class="signed">${esc(uname(c.tech))}</span><br><span class="small muted mono">${esc(maskAuth(uauth(c.tech)))} · ${esc(fTs(c.tech_at))}</span>` : signBtn(c, "tech")}</td>
        <td>${c.insp ? `<span class="signed">${esc(uname(c.insp))}</span><br><span class="small muted mono">${esc(maskAuth(uauth(c.insp)))} · ${esc(fTs(c.insp_at))}</span>` : signBtn(c, "insp")}</td></tr>`).join("")}
      </tbody></table></div>
      <h3>${esc(t("wo.parts"))}</h3><div class="list">${parts.map(p => `<div><button class="link" data-open="part:${esc(p.id)}">${esc(tx(p.descr))}</button><span class="mono muted">${esc(p.pn)} · ${esc(p.sn || p.lot)} · ${esc(p.form1 || "-")}</span></div>`).join("") || `<div class="muted">${esc(t("tbl.empty"))}</div>`}</div>
      <p class="small muted">${esc(t("sign.simulated"))}</p>`, foot);
  }

  function showPart(id) {
    const p = one("SELECT * FROM part WHERE id=?", [id]); if (!p) return;
    CURRENT = "part:" + id;
    const moves = q("SELECT * FROM part_move WHERE part_id=? ORDER BY at", [id]);
    const l = llp(p);
    let foot = "";
    if (p.status === "quarantine" && can("part.doc")) foot += `<button class="btn primary" data-act="part-doc" data-id="${esc(id)}">${esc(t("p.attach"))}</button>`;
    foot += `<button class="btn" data-act="pdf-part" data-id="${esc(id)}">${esc(t("btn.pdf_sheet"))}</button>`;
    openDlg(`${p.pn} · ${tx(p.descr)}`,
      `<div class="toolbar">${pill(PART_K[p.status], t("ps." + p.status))}${l ? pill(l.k, l.pct !== undefined ? t("llp.pct", { n: l.pct }) : t("llp.days", { n: l.days })) : ""}</div>
      ${p.status === "quarantine" ? `<div class="notice crit">${esc(t("p.quarantine_notice"))}</div>` : ""}
      ${kv([["col.pn", `<span class="mono">${esc(p.pn)}</span>`], ["col.snlot", `<span class="mono">${esc(p.sn || "Lot " + p.lot)}</span>`], ["col.form1", p.form1 ? `<span class="mono">${esc(p.form1)}</span>${p.form1_org ? `<br><span class="small muted mono">${esc(p.form1_org)} · ${esc(fD(p.form1_date))}</span>` : ""}` : pill("crit", t("p.missing"))], ["col.qty", esc(fN(p.qty))], ["col.location", p.reg ? `<button class="link mono" data-open="ac:${esc(p.reg)}">${esc(p.reg)}</button>` : esc(p.location || "-")], ["col.tsn", p.tsn !== null ? esc(fH(p.tsn)) + " h" : "-"], ["col.limit", p.limit_h ? esc(fN(p.limit_h)) + " h" : p.limit_date ? esc(fD(p.limit_date)) : esc(t("p.nolimit"))], ["col.wo", p.wo_id ? `<button class="link mono" data-open="wo:${esc(p.wo_id)}">${esc(p.wo_id)}</button>` : "-"]])}
      <h3>${esc(t("p.trace"))}</h3>
      <ol class="timeline">${moves.length ? moves.map(m => `<li><span class="mono small muted">${esc(fTs(m.at))}</span> <strong>${esc(t("mv." + m.kind))}</strong> · ${esc(tx(m.from_loc))} → ${esc(tx(m.to_loc))}${m.wo_id ? ` · <button class="link mono" data-open="wo:${esc(m.wo_id)}">${esc(m.wo_id)}</button>` : ""} · <span class="muted">${esc(uname(m.uid))}</span></li>`).join("") : `<li class="muted">${esc(t("p.no_moves"))}</li>`}</ol>`, foot);
  }

  function showNc(id) {
    const n = one("SELECT * FROM nc WHERE id=?", [id]); if (!n) return;
    CURRENT = "nc:" + id;
    const editable = n.status === "open" && can("nc.edit");
    openDlg(n.id,
      `<div class="toolbar">${pill(NC_K[n.level], t("lvl." + n.level))}${pill(n.status === "open" ? "warn" : "ok", t("ncs." + n.status))}</div>
      ${kv([["col.reg", n.reg ? `<button class="link mono" data-open="ac:${esc(n.reg)}">${esc(n.reg)}</button>` : "-"], ["col.source", esc(tx(n.source))], ["col.opened", esc(fD(n.opened))], ["col.due", esc(fD(n.due))], ["col.owner", esc(uname(n.owner))], ["col.closed", esc(fD(n.closed_at))]])}
      <p><strong>${esc(t("col.descr"))} :</strong> ${esc(tx(n.descr))}</p>
      <form id="f-nc" class="fields one" novalidate>
        <div class="field"><label for="nc-cause">${esc(t("nc.cause"))}</label><textarea id="nc-cause" class="input" rows="2" maxlength="400" ${editable ? "" : "disabled"}>${esc(tx(n.cause))}</textarea></div>
        <div class="field"><label for="nc-action">${esc(t("nc.action"))}</label><textarea id="nc-action" class="input" rows="2" maxlength="400" ${editable ? "" : "disabled"}>${esc(tx(n.action))}</textarea></div>
        <p class="err" id="nc-err" role="alert"></p>
      </form>`,
      (editable ? `<button class="btn" data-act="nc-save" data-id="${esc(id)}">${esc(t("btn.save"))}</button>` : "") + (n.status === "open" && can("nc.close") ? `<button class="btn primary" data-act="nc-close" data-id="${esc(id)}">${esc(t("nc.close"))}</button>` : ""));
  }

  function showCrs(id) {
    const c = one("SELECT c.*, w.title, w.kind, a.model, a.msn FROM crs c JOIN wo w ON w.id=c.wo_id JOIN aircraft a ON a.reg=c.reg WHERE c.id=?", [id]); if (!c) return;
    CURRENT = "crs:" + id;
    openDlg(t("crs.title") + " · " + c.id,
      `<div class="certificate">
        <p class="eyebrow">${esc(t("crs.org", { a: c.approval }))}</p>
        <h3>${esc(t("crs.heading"))}</h3>
        ${kv([["col.crs", `<span class="mono">${esc(c.id)}</span>`], ["col.wo", `<span class="mono">${esc(c.wo_id)}</span>`], ["col.aircraft", `${esc(c.reg)} · ${esc(c.model)} MSN ${esc(c.msn)}`], ["col.task", esc(tx(c.title))], ["col.hours", esc(fH(c.hours)) + " h · " + esc(fN(c.cycles)) + " cyc"], ["col.date", esc(fTs(c.at))]])}
        <p class="statement">${esc(t("crs.statement"))}</p>
        <p><strong>${esc(t("col.certifier"))} :</strong> ${esc(uname(c.certifier))} · <span class="mono">${esc(maskAuth(c.cert_auth))}</span>${c.cert_cat ? " · " + esc(t("col.cat")) + " " + esc(c.cert_cat) : ""}</p>
        <p class="small muted">${esc(t("crs.simulated", { fp: String(c.fp).slice(0, 16) }))}</p>
      </div>`,
      `<button class="btn primary" data-act="pdf-crs" data-id="${esc(id)}">${esc(t("btn.pdf_crs"))}</button>`);
  }

  /* =========================================================
     Signature électronique SIMULÉE
     ========================================================= */
  function sign(purposeKey, p, onOk) {
    openDlg(t("sign.title"),
      `<div class="notice">${esc(t("sign.simulated"))}</div>
      <p>${esc(t(purposeKey, p))}</p>
      <form id="f-sign" class="fields one" novalidate>
        <div class="field"><label for="sign-auth">${esc(t("sign.label", { name: me.name }))}</label><input id="sign-auth" class="input mono" autocomplete="off" spellcheck="false" required></div>
        <p class="small muted">${esc(t("sign.hint"))}</p>
        <p class="err" id="sign-err" role="alert"></p>
      </form>`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button><button class="btn primary" type="submit" form="f-sign">${esc(t("sign.confirm"))}</button>`);
    setTimeout(() => { const i = $("#sign-auth"); if (i) i.focus(); }, 30);
    $("#f-sign").addEventListener("submit", e => {
      e.preventDefault();
      const v = $("#sign-auth").value.trim().toUpperCase();
      if (v !== me.auth) {
        safe(() => tx_(() => log("sign_fail", "log.sign_fail", {})));
        $("#sign-err").textContent = t("err.sign");
        return;
      }
      onOk();
    });
  }

  /* =========================================================
     Actions
     ========================================================= */
  function deny(whatKey) {
    safe(() => tx_(() => log("denied", "log.denied", { what: "@perm." + whatKey })));
    toast(t("toast.denied"), true);
  }
  function safe(fn, okKey, p) {
    try { fn(); if (okKey) toast(t(okKey, p)); render(); if (dlg().open && CURRENT && okKey) reopen(); return true; }
    catch (e) { console.error(e); toast(t("err.generic", { m: e.message }), true); return false; }
  }
  function reopen() {
    const [k, id] = CURRENT.split(/:(.+)/);
    ({ ac: showAircraft, wo: showWo, part: showPart, nc: showNc, crs: showCrs })[k](id);
  }

  function formDlg(title, fieldsHtml, submitLabel, onSubmit) {
    openDlg(title, `<form id="f-gen" class="fields" novalidate>${fieldsHtml}<p class="err full" id="gen-err" role="alert"></p></form>`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button><button class="btn primary" type="submit" form="f-gen">${esc(submitLabel)}</button>`);
    $("#f-gen").addEventListener("submit", e => {
      e.preventDefault();
      const err = onSubmit();
      if (err) { $("#gen-err").textContent = err; return; }
    });
  }
  function form1Check(f1, org, date) { // contrôle de saisie du certificat EASA Form 1
    if (!/^F1-[A-Z0-9]{2,10}-\d{2}-\d{4,6}$/.test(f1)) return t("err.form1");
    if (!/^[A-Z]{2}\.(21G|145|21J)\.[A-Z0-9]{2,8}$/.test(org) || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return t("err.form1_fields");
    if (date > isoD(TODAY)) return t("err.form1_date");
    if (one("SELECT 1 FROM part WHERE form1=?", [f1])) return t("err.form1_dup");
    return null;
  }
  const val = id => ($("#" + id) ? $("#" + id).value.trim() : "");
  const field = (id, label, input, full) => `<div class="field${full ? " full" : ""}"><label for="${id}">${esc(t(label))}</label>${input}</div>`;
  const sel = (id, opts, cur) => `<select id="${id}" class="input">${opts.map(([v, l]) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;

  const ACTIONS = {
    close: () => closeDlg(),
    csv: () => exportCsv(),
    pdf: () => exportPdf(),
    "pdf-crs": id => pdfCrs(id),
    "pdf-wo": id => pdfSheet("wo", id),
    "pdf-ac": id => pdfSheet("ac", id),
    "pdf-part": id => pdfSheet("part", id),
    verify: () => toast(verifyLog() ? t("log.ok", { n: one("SELECT COUNT(*) n FROM log").n }) + (SHA_OK ? " " + t("log.webcrypto") : "") : t("log.ko"), !verifyLog()),

    "new-wo": () => {
      if (!can("wo.create")) return deny("wo.create");
      const acs = q("SELECT * FROM aircraft ORDER BY reg");
      const techs = q("SELECT * FROM users WHERE role='TECH' AND active=1");
      formDlg(t("wo.new"),
        field("w-reg", "col.aircraft", sel("w-reg", acs.map(a => [a.reg, a.reg + " · " + a.model + " MSN " + a.msn]))) +
        field("w-kind", "col.kind", sel("w-kind", ["scheduled", "defect", "ad", "mod"].map(k => [k, t("wok." + k)]))) +
        field("w-task", "col.task", `<select id="w-task" class="input"></select>`, true) +
        field("w-free", "wo.free", `<input id="w-free" class="input" maxlength="120" placeholder="${esc(t("wo.free_ph"))}">`, true) +
        field("w-tech", "col.assignee", sel("w-tech", [["", "-"], ...techs.map(u => [u.id, u.name])])),
        t("wo.create"), () => {
          const reg = val("w-reg"), kind = val("w-kind"), taskSel = val("w-task"), free = val("w-free");
          if (!reg) return t("err.required");
          let title = free, acTask = null, acAd = null;
          if (kind === "scheduled" && taskSel) { const r = one("SELECT a.id, m.title FROM ac_task a JOIN mp_task m ON m.id=a.task_id WHERE a.id=?", [+taskSel]); title = r.title; acTask = r.id; }
          if (kind === "ad" && taskSel) { const r = one("SELECT x.id, a.title FROM ac_ad x JOIN ad a ON a.id=x.ad_id WHERE x.id=?", [+taskSel]); title = r.title; acAd = r.id; }
          if (!title || title.length < 3) return t("err.title");
          if (acTask && one("SELECT 1 FROM wo WHERE ac_task_id=? AND status!='closed'", [acTask])) return t("err.wo_dup");
          const id = nextId("wo", "WO", 4);
          const ok = safe(() => tx_(() => {
            run("INSERT INTO wo(id,reg,title,kind,status,opened,planner,assignee,ac_task_id,ac_ad_id) VALUES(?,?,?,?,?,?,?,?,?,?)", [id, reg, title, kind, "open", isoD(new Date()), me.id, val("w-tech") || null, acTask, acAd]);
            ["@card.prep", "@card.perform", "@card.test", "@card.docs"].forEach((c, i) => run("INSERT INTO card(wo_id,seq,title) VALUES(?,?,?)", [id, i + 1, c]));
            log("wo_create", "log.wo_create", { id, reg });
          }), "toast.wo_created", { id });
          if (ok) { F.wo = "active"; showWo(id); location.hash = "#workorders"; }
        });
      const refresh = () => {
        const reg = val("w-reg"), kind = val("w-kind");
        let opts = [["", t("wo.free_opt")]];
        if (kind === "scheduled") opts = opts.concat(taskRows(reg).map(r => [String(r.id), tx(r.title) + " · " + t("st." + r.st)]));
        if (kind === "ad") opts = opts.concat(adRows(reg).filter(r => r.status === "open" || r.kind === "repeat").map(r => [String(r.id), r.ad_id + " · " + tx(r.title)]));
        $("#w-task").innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join("");
      };
      $("#w-reg").addEventListener("change", refresh); $("#w-kind").addEventListener("change", refresh); refresh();
    },
    "wo-start": id => {
      if (!can("wo.start")) return deny("wo.start");
      const w = one("SELECT * FROM wo WHERE id=?", [id]);
      if (w.kind === "mod" && one("SELECT 1 FROM part WHERE pn='125A55-0012-01' AND status='quarantine'") && !one("SELECT 1 FROM part WHERE pn='125A55-0012-01' AND status='stock'")) return toast(t("err.part_blocked"), true);
      safe(() => tx_(() => { run("UPDATE wo SET status='in_progress', assignee=COALESCE(assignee,?) WHERE id=?", [me.id, id]); log("wo_start", "log.wo_start", { id }); }), "toast.wo_started", { id });
    },
    "wo-assign": id => {
      if (!can("wo.assign")) return deny("wo.assign");
      const techs = q("SELECT * FROM users WHERE role='TECH' AND active=1");
      formDlg(t("wo.assign") + " · " + id, field("a-tech", "col.assignee", sel("a-tech", techs.map(u => [u.id, u.name]))), t("btn.save"), () => {
        const u = val("a-tech"); if (!u) return t("err.required");
        safe(() => tx_(() => { run("UPDATE wo SET assignee=? WHERE id=?", [u, id]); log("wo_assign", "log.wo_assign", { id, who: uname(u) }); }), "toast.saved");
        showWo(id);
      });
    },
    "wo-part": id => {
      if (!can("part.install")) return deny("part.install");
      const w = one("SELECT * FROM wo WHERE id=?", [id]);
      const stock = q("SELECT * FROM part WHERE status='stock' AND form1 IS NOT NULL AND form1_org IS NOT NULL AND (limit_date IS NULL OR limit_date>=?) AND (limit_h IS NULL OR tsn<limit_h) ORDER BY pn", [isoD(TODAY)]);
      if (!stock.length) return toast(t("err.no_stock"), true);
      formDlg(t("wo.install") + " · " + w.reg, field("p-sel", "col.part", sel("p-sel", stock.map(p => [p.id, p.pn + " · " + tx(p.descr) + " · " + (p.sn || "Lot " + p.lot) + " · " + p.form1])), true) +
        `<p class="small muted full">${esc(t("wo.install_note"))}</p>`, t("wo.install"), () => {
          const pid = val("p-sel"); const p = one("SELECT * FROM part WHERE id=?", [pid]);
          if (!p || p.status !== "stock") return t("err.part_invalid");
          if (!p.form1 || !p.form1_org || (p.limit_date && p.limit_date < isoD(TODAY)) || (p.limit_h && p.tsn >= p.limit_h)) { safe(() => tx_(() => log("denied", "log.install_refused", { pn: p.pn, sn: p.sn || p.lot }))); return t("err.install_check"); }
          safe(() => tx_(() => {
            const now = new Date().toISOString();
            if (p.lot && p.qty > 1) { // pièce au lot : on sort une unité
              run("UPDATE part SET qty=qty-1 WHERE id=?", [pid]);
              run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,wo_id,uid) VALUES(?,?,?,?,?,?,?)", [pid, now, "consume", p.location, w.reg, id, me.id]);
            } else {
              run("UPDATE part SET status='installed', reg=?, wo_id=?, location=NULL, tsn=COALESCE(tsn,0) WHERE id=?", [w.reg, id, pid]);
              run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,wo_id,uid) VALUES(?,?,?,?,?,?,?)", [pid, now, "issue", p.location, id, id, me.id]);
              run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,wo_id,uid) VALUES(?,?,?,?,?,?,?)", [pid, now, "install", id, w.reg, id, me.id]);
            }
            log("part_install", "log.part_install", { pn: p.pn, sn: p.sn || p.lot, reg: w.reg, wo: id });
          }), "toast.part_installed");
          showWo(id);
        });
    },
    "card-tech": cid => {
      if (!can("card.tech")) return deny("card.tech");
      const c = one("SELECT * FROM card WHERE id=?", [+cid]);
      sign("sign.purpose_tech", { task: tx(c.title), wo: c.wo_id }, () => {
        safe(() => tx_(() => { run("UPDATE card SET tech=?, tech_at=? WHERE id=? AND tech IS NULL", [me.id, new Date().toISOString(), +cid]); log("card_tech", "log.card_tech", { wo: c.wo_id, n: c.seq }); }), "toast.signed");
        showWo(c.wo_id);
      });
    },
    "card-insp": cid => {
      if (!can("card.insp")) return deny("card.insp");
      const c = one("SELECT * FROM card WHERE id=?", [+cid]);
      if (!c.tech) return toast(t("err.need_tech"), true);
      if (c.tech === me.id) { safe(() => tx_(() => log("denied", "log.self_cert", { wo: c.wo_id }))); return toast(t("err.self"), true); }
      sign("sign.purpose_insp", { task: tx(c.title), wo: c.wo_id }, () => {
        safe(() => tx_(() => {
          run("UPDATE card SET insp=?, insp_at=? WHERE id=? AND insp IS NULL", [me.id, new Date().toISOString(), +cid]);
          log("card_insp", "log.card_insp", { wo: c.wo_id, n: c.seq });
          const left = one("SELECT COUNT(*) n FROM card WHERE wo_id=? AND insp IS NULL", [c.wo_id]).n;
          if (!left) { run("UPDATE wo SET status='awaiting_crs' WHERE id=?", [c.wo_id]); log("wo_ready", "log.wo_ready", { id: c.wo_id }); }
        }), "toast.signed");
        showWo(c.wo_id);
      });
    },
    crs: id => {
      if (!can("crs.issue")) return deny("crs.issue");
      const w = one("SELECT * FROM wo WHERE id=?", [id]);
      if (w.status !== "awaiting_crs") return toast(t("err.not_ready"), true);
      if (one("SELECT 1 FROM card WHERE wo_id=? AND tech=?", [id, me.id])) { safe(() => tx_(() => log("denied", "log.self_cert", { wo: id }))); return toast(t("err.self"), true); }
      if (one("SELECT 1 FROM nc WHERE reg=? AND level='L1' AND status='open'", [w.reg]) && w.kind !== "defect") return toast(t("err.aog_crs"), true);
      sign("sign.purpose_crs", { wo: id, reg: w.reg }, () => {
        const cid = nextId("crs", "CRS", 4);
        CURRENT = null; // A2 : ne pas rouvrir l'OT, le CRS émis sert de confirmation
        const ok = safe(() => tx_(() => {
          const a = one("SELECT * FROM aircraft WHERE reg=?", [w.reg]);
          const at = new Date().toISOString();
          const approval = (one("SELECT v FROM meta WHERE k='approval'") || { v: "FR.145.DEMO" }).v;
          const fp = sha256([cid, id, w.reg, me.id, me.auth, me.cat || "", approval, at, a.hours, a.cycles].join("|"));
          run("INSERT INTO crs(id,wo_id,reg,certifier,cert_auth,cert_cat,approval,at,hours,cycles,fp) VALUES(?,?,?,?,?,?,?,?,?,?,?)", [cid, id, w.reg, me.id, me.auth, me.cat || null, approval, at, a.hours, a.cycles, fp]);
          run("UPDATE wo SET status='closed', crs_id=?, closed_at=? WHERE id=?", [cid, at, id]);
          if (w.ac_task_id) run("UPDATE ac_task SET last_h=?, last_c=?, last_date=? WHERE id=?", [a.hours, a.cycles, isoD(new Date()), w.ac_task_id]);
          if (w.ac_ad_id) run("UPDATE ac_ad SET status='applied', last_h=?, last_date=?, wo_id=? WHERE id=?", [a.hours, isoD(new Date()), id, w.ac_ad_id]);
          if (w.mod_id) run("UPDATE modif SET status='embodied' WHERE id=?", [w.mod_id]);
          log("crs_issue", "log.crs_issue", { id: cid, wo: id });
        }), "toast.crs", { id: cid });
        if (ok) showCrs(cid);
      });
    },
    receive: () => {
      if (!can("part.receive")) return deny("part.receive");
      formDlg(t("stock.receive"),
        field("r-pn", "col.pn", `<input id="r-pn" class="input mono" maxlength="30" required placeholder="145A00-0000-00">`) +
        field("r-descr", "col.descr", `<input id="r-descr" class="input" maxlength="80" required>`) +
        field("r-sn", "col.sn", `<input id="r-sn" class="input mono" maxlength="30">`) +
        field("r-lot", "col.lot", `<input id="r-lot" class="input mono" maxlength="30">`) +
        field("r-qty", "col.qty", `<input id="r-qty" class="input" type="number" min="1" max="999" value="1">`) +
        field("r-loc", "col.location", `<input id="r-loc" class="input mono" maxlength="10" value="A-10">`) +
        field("r-f1", "col.form1", `<input id="r-f1" class="input mono" maxlength="30" placeholder="F1-ORG-26-00000">`) +
        field("r-f1org", "col.form1_org", `<input id="r-f1org" class="input mono" maxlength="20" placeholder="FR.21G.0000">`) +
        field("r-f1date", "col.form1_date", `<input id="r-f1date" class="input" type="date" max="${isoD(TODAY)}">`) +
        field("r-lim", "col.limit_h", `<input id="r-lim" class="input" type="number" min="0" step="1">`) +
        `<p class="small muted full">${esc(t("stock.receive_note"))}</p>`, t("stock.receive_btn"), () => {
          const pn = val("r-pn").toUpperCase(), descr = val("r-descr"), sn = val("r-sn").toUpperCase(), lot = val("r-lot").toUpperCase(), qty = parseInt(val("r-qty"), 10), locn = val("r-loc").toUpperCase(), f1 = val("r-f1").toUpperCase(), lim = val("r-lim");
          if (!/^[A-Z0-9][A-Z0-9-]{3,29}$/.test(pn)) return t("err.pn");
          if (descr.length < 3) return t("err.descr");
          if (!sn && !lot) return t("err.snlot");
          if (sn && qty !== 1) return t("err.sn_qty");
          if (!(qty >= 1 && qty <= 999)) return t("err.qty");
          if (sn && one("SELECT 1 FROM part WHERE pn=? AND sn=?", [pn, sn])) return t("err.dup_sn");
          const f1org = val("r-f1org").toUpperCase(), f1date = val("r-f1date");
          if (f1) { const e = form1Check(f1, f1org, f1date); if (e) return e; }
          const id = "PT-" + String((one("SELECT COUNT(*) n FROM part").n + 1)).padStart(4, "0");
          const status = f1 ? "stock" : "quarantine";
          safe(() => tx_(() => {
            run("INSERT INTO part(id,pn,descr,sn,lot,qty,form1,form1_org,form1_date,status,location,tsn,limit_h,received) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [id, pn, descr, sn || null, lot || null, qty, f1 || null, f1 ? f1org : null, f1 ? f1date : null, status, f1 ? locn : "Q-01", sn ? 0 : null, lim ? +lim : null, isoD(new Date())]);
            run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,uid) VALUES(?,?,?,?,?,?)", [id, new Date().toISOString(), f1 ? "receive" : "quarantine", "@loc.supplier", f1 ? locn : "Q-01", me.id]);
            log(f1 ? "part_receive" : "part_quarantine", f1 ? "log.part_receive" : "log.part_quarantine", { pn, sn: sn || lot });
          }), f1 ? "toast.received" : "toast.quarantined");
          closeDlg();
        });
    },
    "part-doc": id => {
      if (!can("part.doc")) return deny("part.doc");
      formDlg(t("p.attach"), field("d-f1", "col.form1", `<input id="d-f1" class="input mono" maxlength="30" placeholder="F1-ORG-26-00000" required>`, true) +
        field("d-f1org", "col.form1_org", `<input id="d-f1org" class="input mono" maxlength="20" placeholder="FR.21G.0000" required>`) +
        field("d-f1date", "col.form1_date", `<input id="d-f1date" class="input" type="date" max="${isoD(TODAY)}" required>`) +
        `<p class="small muted full">${esc(t("p.attach_note"))}</p>`, t("btn.save"), () => {
        const f1 = val("d-f1").toUpperCase(), f1org = val("d-f1org").toUpperCase(), f1date = val("d-f1date");
        const err = form1Check(f1, f1org, f1date); if (err) return err;
        const p = one("SELECT * FROM part WHERE id=?", [id]);
        CURRENT = null; // A3 : fermer la fenêtre, le message confirme la libération
        if (safe(() => tx_(() => {
          run("UPDATE part SET form1=?, form1_org=?, form1_date=?, status='stock', location='A-11' WHERE id=?", [f1, f1org, f1date, id]);
          run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,uid) VALUES(?,?,?,?,?,?)", [id, new Date().toISOString(), "release", "Q-01", "A-11", me.id]);
          run("UPDATE po SET status='received' WHERE pn=? AND status='awaiting_doc'", [p.pn]);
          log("part_release", "log.part_release", { pn: p.pn, sn: p.sn || p.lot, f1 });
        }), "toast.released")) closeDlg();
      });
    },
    "new-po": () => {
      if (!can("po.create")) return deny("po.create");
      formDlg(t("po.new"), field("o-pn", "col.pn", `<input id="o-pn" class="input mono" maxlength="30">`) + field("o-descr", "col.descr", `<input id="o-descr" class="input" maxlength="80">`) +
        field("o-qty", "col.qty", `<input id="o-qty" class="input" type="number" min="1" max="999" value="1">`) + field("o-sup", "col.supplier", sel("o-sup", [["@sup.a", t("sup.a")], ["@sup.b", t("sup.b")]])), t("po.create"), () => {
          const pn = val("o-pn").toUpperCase(), d = val("o-descr"), qty = parseInt(val("o-qty"), 10);
          if (!/^[A-Z0-9][A-Z0-9-]{3,29}$/.test(pn)) return t("err.pn");
          if (d.length < 3) return t("err.descr");
          if (!(qty >= 1 && qty <= 999)) return t("err.qty");
          const id = nextId("po", "PO", 4);
          safe(() => tx_(() => { run("INSERT INTO po(id,pn,descr,qty,supplier,status,ordered,uid) VALUES(?,?,?,?,?,?,?,?)", [id, pn, d, qty, val("o-sup"), "ordered", isoD(new Date()), me.id]); log("po_create", "log.po_create", { id, pn }); }), "toast.po", { id });
          closeDlg();
        });
    },
    "po-receive": id => {
      if (!can("po.receive")) return deny("po.receive");
      safe(() => tx_(() => { run("UPDATE po SET status='awaiting_doc' WHERE id=?", [id]); log("po_receive", "log.po_receive", { id }); }), "toast.po_received");
    },
    "new-nc": () => {
      if (!can("nc.create")) return deny("nc.create");
      const acs = q("SELECT reg, model FROM aircraft ORDER BY reg");
      formDlg(t("nc.new"),
        field("n-level", "col.level", sel("n-level", ["L1", "L2", "OBS"].map(l => [l, t("lvl." + l)]), "L2")) +
        field("n-reg", "col.reg", sel("n-reg", [["", t("nc.org")], ...acs.map(a => [a.reg, a.reg + " · " + a.model])])) +
        field("n-src", "col.source", sel("n-src", ["internal", "audit", "reception", "authority"].map(s => ["@src." + s, t("src." + s)]))) +
        field("n-descr", "col.descr", `<textarea id="n-descr" class="input" rows="3" maxlength="400"></textarea>`, true) +
        `<div class="notice full">${esc(t("nc.l1_note"))}</div>`, t("nc.open"), () => {
          const d = val("n-descr"); if (d.length < 10) return t("err.descr_long");
          const level = val("n-level"), reg = val("n-reg") || null;
          const id = nextId("nc", "NC", 3);
          const due = level === "L1" ? addDays(0) : level === "L2" ? addDays(90) : addDays(30);
          const owner = (one("SELECT id FROM users WHERE role='QUALITY' AND active=1") || me).id;
          safe(() => tx_(() => { run("INSERT INTO nc(id,level,reg,descr,source,opened,due,status,owner) VALUES(?,?,?,?,?,?,?,?,?)", [id, level, reg, d, val("n-src"), isoD(new Date()), due, "open", owner]); log("nc_open", "log.nc_open", { id, level }); }), "toast.nc", { id });
          F.nc = "open"; showNc(id); location.hash = "#nc";
        });
    },
    "nc-save": id => {
      if (!can("nc.edit")) return deny("nc.edit");
      safe(() => tx_(() => { run("UPDATE nc SET cause=?, action=? WHERE id=?", [val("nc-cause") || null, val("nc-action") || null, id]); log("nc_update", "log.nc_update", { id }); }), "toast.saved");
    },
    "nc-close": id => {
      if (!can("nc.close")) return deny("nc.close");
      if (val("nc-cause").length < 5 || val("nc-action").length < 5) { $("#nc-err").textContent = t("err.nc_close"); return; }
      sign("sign.purpose_nc", { id }, () => {
        safe(() => tx_(() => { run("UPDATE nc SET cause=?, action=?, status='closed', closed_at=? WHERE id=?", [val("nc-cause") || one("SELECT cause FROM nc WHERE id=?", [id]).cause, val("nc-action") || one("SELECT action FROM nc WHERE id=?", [id]).action, isoD(new Date()), id]); log("nc_close", "log.nc_close", { id }); }), "toast.nc_closed", { id });
        showNc(id);
      });
    },
    "new-audit": () => {
      if (!can("audit.manage")) return deny("audit.manage");
      formDlg(t("aud.new"), field("au-title", "col.subject", `<input id="au-title" class="input" maxlength="100">`, true) + field("au-scope", "col.scope", sel("au-scope", [["Part-145", "Part-145"], ["Part-CAMO", "Part-CAMO"], ["Part-M", "Part-M"], ["Part-21", "Part-21"], ["@scope.store", t("scope.store")]])) +
        field("au-date", "col.date", `<input id="au-date" class="input" type="date" value="${addDays(14)}">`), t("aud.plan"), () => {
          const ti = val("au-title"), d = val("au-date"); if (ti.length < 3) return t("err.title"); if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return t("err.date");
          const id = "AUD-" + d.slice(0, 4) + "-" + String(one("SELECT COUNT(*) n FROM audit").n + 1).padStart(2, "0") + "b";
          safe(() => tx_(() => { run("INSERT INTO audit(id,title,scope,planned,auditor,status,findings) VALUES(?,?,?,?,?,?,0)", [id, ti, val("au-scope"), d, me.id, "planned"]); log("audit_plan", "log.audit_plan", { id }); }), "toast.saved");
          closeDlg();
        });
    },
    "audit-next": id => {
      if (!can("audit.manage")) return deny("audit.manage");
      const a = one("SELECT * FROM audit WHERE id=?", [id]); const nx = a.status === "planned" ? "in_progress" : "closed";
      safe(() => tx_(() => { run("UPDATE audit SET status=? WHERE id=?", [nx, id]); log("audit_status", "log.audit_status", { id, s: "@auds." + nx }); }), "toast.saved");
    },
    "doc-approve": id => {
      if (!can("doc.approve")) return deny("doc.approve");
      const d = one("SELECT * FROM doc WHERE id=?", [id]);
      sign("sign.purpose_doc", { id, r: d.pending }, () => {
        safe(() => tx_(() => { run("UPDATE doc SET rev=pending, pending=NULL, status='current', rev_date=? WHERE id=?", [isoD(new Date()), id]); log("doc_approve", "log.doc_approve", { id, rev: d.pending }); }), "toast.doc", { id });
        closeDlg();
      });
    },
    "mod-next": id => {
      if (!can("mod.manage")) return deny("mod.manage");
      const m = one("SELECT * FROM modif WHERE id=?", [id]); const nx = { draft: "approved", approved: "in_work", in_work: "embodied" }[m.status];
      if (nx === "embodied" && one("SELECT 1 FROM wo WHERE mod_id=? AND status!='closed'", [id])) return toast(t("err.mod_wo"), true);
      safe(() => tx_(() => { run("UPDATE modif SET status=? WHERE id=?", [nx, id]); log("mod_status", "log.mod_status", { id, s: "@mods." + nx }); }), "toast.saved");
    },
    "user-toggle": id => {
      if (!can("user.manage")) return deny("user.manage");
      const u = one("SELECT * FROM users WHERE id=?", [id]);
      if (u.role === "ADMIN" && u.active && one("SELECT COUNT(*) n FROM users WHERE role='ADMIN' AND active=1").n <= 1) return toast(t("err.last_admin"), true);
      safe(() => tx_(() => { run("UPDATE users SET active=? WHERE id=?", [u.active ? 0 : 1, id]); log("user", u.active ? "log.user_off" : "log.user_on", { name: u.name }); }), "toast.saved");
    },
    "db-download": () => {
      if (!can("user.manage")) return deny("db.reset");
      download(new Blob([db.export()], { type: "application/x-sqlite3" }), "mis-demo-" + isoD(new Date()) + ".sqlite");
    },
    "db-reset": () => {
      if (!can("db.reset")) return deny("db.reset");
      openDlg(t("admin.reset"), `<p>${esc(t("admin.reset_confirm"))}</p>`, `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button><button class="btn danger-btn" data-act="db-reset-ok">${esc(t("admin.reset_btn"))}</button>`);
    },
    "copy-anchor": () => {
      const h = $("#anchor") ? $("#anchor").textContent : "";
      const ok = () => toast(t("log.anchor_copied"));
      try { navigator.clipboard.writeText(h).then(ok, () => { selectText($("#anchor")); toast(t("log.anchor_select")); }); }
      catch (e) { selectText($("#anchor")); toast(t("log.anchor_select")); }
    },
    "db-reset-ok": () => {
      if (!can("db.reset")) return deny("db.reset");
      sign("sign.purpose_reset", {}, () => doReset());
    }
  };
  function selectText(el) { if (!el) return; const r = document.createRange(); r.selectNodeContents(el); const s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
  function doReset() {
    if (!can("db.reset")) return deny("db.reset");
    {
      const who = me.id; const keep = q("SELECT * FROM log ORDER BY id");
      db.close(); freshDb(keep); me = one("SELECT * FROM users WHERE id=?", [who]) || one("SELECT * FROM users WHERE role='ADMIN'");
      addLog(me.id, "db_reset", "log.db_reset", { n: keep.length });
      persist(); closeDlg(); toast(t("toast.reset")); render();
    }
  }

  /* =========================================================
     Exports CSV et PDF
     ========================================================= */
  function download(blob, name) {
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast(t("toast.download", { f: name }));
  }
  const fileBase = () => (EXPORT ? t(EXPORT.title).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") : "export") + "-" + isoD(new Date());
  const exportCols = () => EXPORT.cols.filter(c => c.h);
  function exportCsv() {
    if (!EXPORT) return;
    const sep = lang === "en" ? "," : ";";
    const cell = v => { // neutralise l'injection de formules (=, +, -, @, tabulation, retour chariot) puis échappe
      let s = String(v ?? ""); if (s !== "-" && /^[=+\-@\t\r]/.test(s)) s = "'" + s;
      return /[";,\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const lines = [exportCols().map(c => cell(t(c.h))).join(sep), ...EXPORT.rows.map(r => exportCols().map(c => cell(c.v(r))).join(sep))];
    if (EXPORT.note) lines.push("", cell(EXPORT.note));
    download(new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }), fileBase() + ".csv");
    safe(() => tx_(() => log("export", "log.export", { f: "CSV", what: "@" + EXPORT.title })));
  }
  const pdfSafe = s => String(s ?? "").replace(/[\u202f\u00a0]/g, " ").replace(/[→]/g, "->").replace(/[’]/g, "'").replace(/[●✓]/g, "x");
  function newPdf(landscape) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: landscape ? "landscape" : "portrait", unit: "mm", format: "a4" });
    return doc;
  }
  function pdfHeader(doc, title) {
    const w = doc.internal.pageSize.getWidth();
    doc.setFillColor(0, 32, 91); doc.rect(0, 0, w, 18, "F");
    doc.setTextColor(255, 255, 255); doc.setFont("helvetica", "bold"); doc.setFontSize(12); doc.text(pdfSafe(t("app.name")), 12, 11.5);
    doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.text(pdfSafe(t("pdf.generated", { d: fTs(new Date().toISOString()), u: me.name })), w - 12, 11.5, { align: "right" });
    doc.setTextColor(15, 27, 45); doc.setFont("helvetica", "bold"); doc.setFontSize(15); doc.text(pdfSafe(title), 12, 30);
  }
  function pdfFooter(doc) {
    const n = doc.getNumberOfPages(), w = doc.internal.pageSize.getWidth(), h = doc.internal.pageSize.getHeight();
    for (let i = 1; i <= n; i++) { doc.setPage(i); doc.setFont("helvetica", "normal"); doc.setFontSize(7.5); doc.setTextColor(90, 100, 120); doc.text(pdfSafe(t("pdf.footer")), 12, h - 8); doc.text(i + " / " + n, w - 12, h - 8, { align: "right" }); }
  }
  function exportPdf() {
    if (!EXPORT) return;
    if (!window.jspdf) return toast(t("err.pdf"), true);
    const cols = exportCols();
    const doc = newPdf(cols.length > 5);
    pdfHeader(doc, t(EXPORT.title));
    doc.autoTable({ startY: 36, head: [cols.map(c => pdfSafe(t(c.h)))], body: EXPORT.rows.map(r => cols.map(c => pdfSafe(c.v(r)))), styles: { fontSize: 8, cellPadding: 2 }, headStyles: { fillColor: [0, 32, 91] }, margin: { left: 12, right: 12, bottom: 16 } });
    if (EXPORT.note) { doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.setTextColor(15, 27, 45); doc.text(doc.splitTextToSize(pdfSafe(EXPORT.note), doc.internal.pageSize.getWidth() - 24), 12, doc.lastAutoTable.finalY + 8); }
    pdfFooter(doc);
    download(doc.output("blob"), fileBase() + ".pdf");
    safe(() => tx_(() => log("export", "log.export", { f: "PDF", what: "@" + EXPORT.title })));
  }
  function pdfKv(doc, y, pairs) {
    doc.autoTable({ startY: y, body: pairs.map(([k, v]) => [pdfSafe(t(k)), pdfSafe(v)]), theme: "plain", styles: { fontSize: 9.5, cellPadding: 1.6 }, columnStyles: { 0: { fontStyle: "bold", cellWidth: 55, textColor: [80, 90, 110] } }, margin: { left: 12, right: 12 } });
    return doc.lastAutoTable.finalY + 6;
  }
  function pdfCrs(id) {
    if (!window.jspdf) return toast(t("err.pdf"), true);
    const c = one("SELECT c.*, w.title, a.model, a.msn FROM crs c JOIN wo w ON w.id=c.wo_id JOIN aircraft a ON a.reg=c.reg WHERE c.id=?", [id]);
    const doc = newPdf(false); pdfHeader(doc, t("crs.heading"));
    doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.setTextColor(90, 100, 120); doc.text(pdfSafe(t("crs.org", { a: c.approval })), 12, 37);
    let y = pdfKv(doc, 42, [["col.crs", c.id], ["col.wo", c.wo_id], ["col.aircraft", c.reg + " - " + c.model + " MSN " + c.msn], ["col.task", tx(c.title)], ["col.hours", fH(c.hours) + " h / " + fN(c.cycles) + " cyc"], ["col.date", fTs(c.at)], ["col.certifier", uname(c.certifier) + " (" + maskAuth(c.cert_auth) + (c.cert_cat ? ", " + t("col.cat") + " " + c.cert_cat : "") + ")"]]);
    doc.setDrawColor(0, 32, 91); doc.setLineWidth(0.4); doc.rect(12, y, doc.internal.pageSize.getWidth() - 24, 30);
    doc.setTextColor(15, 27, 45); doc.setFontSize(10.5); doc.text(doc.splitTextToSize(pdfSafe(t("crs.statement")), doc.internal.pageSize.getWidth() - 32), 16, y + 8);
    y += 40; doc.setFontSize(8.5); doc.setTextColor(180, 35, 24); doc.text(doc.splitTextToSize(pdfSafe(t("crs.simulated", { fp: String(c.fp).slice(0, 16) })), doc.internal.pageSize.getWidth() - 24), 12, y);
    pdfFooter(doc); download(doc.output("blob"), c.id + ".pdf");
    safe(() => tx_(() => log("export", "log.export", { f: "PDF", what: c.id })));
  }
  function pdfSheet(kind, id) {
    if (!window.jspdf) return toast(t("err.pdf"), true);
    const doc = newPdf(false); let name = id;
    if (kind === "ac") {
      const a = one("SELECT * FROM aircraft WHERE reg=?", [id]); const s = acStatus(a);
      pdfHeader(doc, t("pdf.ac_title", { reg: a.reg }));
      let y = pdfKv(doc, 36, [["col.model", a.model], ["col.msn", a.msn], ["col.base", a.base + " - " + tx(a.mission)], ["col.hours", fH(a.hours) + " h"], ["col.cycles", fN(a.cycles)], ["col.arc", fD(a.arc_expiry)], ["col.status", t("acst." + s.code)]]);
      doc.autoTable({ startY: y, head: [[t("col.task"), t("col.remaining"), t("col.status")].map(pdfSafe)], body: s.tasks.map(r => [tx(r.title), remText(r), t("st." + r.st)].map(pdfSafe)), styles: { fontSize: 8.5 }, headStyles: { fillColor: [0, 32, 91] }, margin: { left: 12, right: 12 } });
      y = doc.lastAutoTable.finalY + 6;
      doc.autoTable({ startY: y, head: [[t("col.ad"), t("col.subject"), t("col.status")].map(pdfSafe)], body: s.ads.map(r => [r.ad_id, tx(r.title), t("ads." + r.status)].map(pdfSafe)), styles: { fontSize: 8.5 }, headStyles: { fillColor: [0, 32, 91] }, margin: { left: 12, right: 12 } });
    } else if (kind === "wo") {
      const w = one("SELECT * FROM wo WHERE id=?", [id]);
      pdfHeader(doc, t("pdf.wo_title", { id }));
      const y = pdfKv(doc, 36, [["col.aircraft", w.reg], ["col.kind", t("wok." + w.kind)], ["col.task", tx(w.title)], ["col.status", t("wost." + w.status)], ["col.opened", fD(w.opened)], ["col.assignee", w.assignee ? uname(w.assignee) : "-"], ["col.crs", w.crs_id || "-"]]);
      doc.autoTable({ startY: y, head: [["#", t("col.task"), t("card.tech"), t("card.insp")].map(pdfSafe)], body: q("SELECT * FROM card WHERE wo_id=? ORDER BY seq", [id]).map(c => [c.seq, tx(c.title), c.tech ? uname(c.tech) + " " + maskAuth(uauth(c.tech)) + " " + fTs(c.tech_at) : "-", c.insp ? uname(c.insp) + " " + maskAuth(uauth(c.insp)) + " " + fTs(c.insp_at) : "-"].map(pdfSafe)), styles: { fontSize: 8.5 }, headStyles: { fillColor: [0, 32, 91] }, margin: { left: 12, right: 12 } });
    } else {
      const p = one("SELECT * FROM part WHERE id=?", [id]); name = p.pn + "-" + (p.sn || p.lot);
      pdfHeader(doc, t("pdf.part_title", { pn: p.pn }));
      const y = pdfKv(doc, 36, [["col.descr", tx(p.descr)], ["col.snlot", p.sn || "Lot " + p.lot], ["col.form1", p.form1 || t("p.missing")], ["col.status", t("ps." + p.status)], ["col.location", p.reg || p.location || "-"], ["col.tsn", p.tsn !== null ? fH(p.tsn) + " h" : "-"], ["col.limit", p.limit_h ? fN(p.limit_h) + " h" : p.limit_date ? fD(p.limit_date) : t("p.nolimit")]]);
      doc.autoTable({ startY: y, head: [[t("col.date"), t("col.action"), t("p.from"), t("p.to"), t("col.user")].map(pdfSafe)], body: (mv => mv.length ? mv : [[{ content: pdfSafe(t("p.no_moves")), colSpan: 5 }]])(q("SELECT * FROM part_move WHERE part_id=? ORDER BY at", [id]).map(m => [fTs(m.at), t("mv." + m.kind), tx(m.from_loc), tx(m.to_loc), uname(m.uid)].map(pdfSafe))), styles: { fontSize: 8.5 }, headStyles: { fillColor: [0, 32, 91] }, margin: { left: 12, right: 12 } });
    }
    pdfFooter(doc); download(doc.output("blob"), name + ".pdf");
    safe(() => tx_(() => log("export", "log.export", { f: "PDF", what: name })));
  }

  /* =========================================================
     Rendu général et événements
     ========================================================= */
  const route = () => { const r = location.hash.slice(1); return V[r] && r !== "denied" ? r : "dashboard"; };
  let lastDenied = null;
  function renderChrome() {
    document.documentElement.lang = lang;
    document.title = t("app.title");
    $("#brand-name").textContent = t("app.name");
    $("#brand-sub").textContent = t("app.sub");
    $("#demo-banner").textContent = t("app.demo");
    $("#lang-label").textContent = t("hdr.lang");
    $("#user-label").textContent = t("hdr.profile");
    $("#gsearch").placeholder = t("hdr.search");
    $("#gsearch").setAttribute("aria-label", t("hdr.search"));
    $("#lang").innerHTML = LANGS.map(([c, n]) => `<option value="${c}" ${c === lang ? "selected" : ""}>${n}</option>`).join("");
    $("#user").innerHTML = q("SELECT * FROM users WHERE active=1 ORDER BY role, name").map(u => `<option value="${esc(u.id)}" ${u.id === me.id ? "selected" : ""}>${esc(u.name)} · ${esc(t("role." + u.role))}</option>`).join("");
    $("#avatar").textContent = me.name.split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase();
    const ok = verifyLog(); const cp = $("#compliance");
    cp.className = "pill " + (ok ? "ok" : "crit"); cp.textContent = ok ? t("hdr.compliant") : t("comp.broken");
    renderSaveState();
    const r = route();
    const badge = { workorders: one("SELECT COUNT(*) n FROM wo WHERE status='awaiting_crs'").n, nc: one("SELECT COUNT(*) n FROM nc WHERE status='open'").n };
    $("#nav").innerHTML = SCREENS.map(g => { const items = g.items.filter(([s]) => canSee(s)); return items.length ? `<div class="nav-group"><div class="nav-h">${esc(t(g.group))}</div>${items.map(([s]) => `<a href="#${s}" ${r === s ? 'aria-current="page"' : ""}>${esc(t("nav." + s))}${badge[s] ? `<span class="count">${badge[s]}</span>` : ""}</a>`).join("")}</div>` : ""; }).join("");
  }
  function render() {
    const r = route();
    renderChrome();
    EXPORT = null;
    let html;
    if (!canSee(r)) {
      html = V.denied();
      if (lastDenied !== r + me.id) { lastDenied = r + me.id; try { tx_(() => log("denied", "log.denied_screen", { s: "@nav." + r })); } catch (e) { } }
    } else html = V[r]();
    $("#main").innerHTML = html + `<footer class="foot"><span>${esc(t("foot.demo"))}</span><span>${esc(t("foot.storage"))}</span></footer>`;
  }
  let toastT;
  function toast(msg, bad) { const el = $("#toast"); el.textContent = msg; el.className = bad ? "bad" : ""; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => (el.hidden = true), 4200); }

  function openRef(ref) {
    const [k, id] = ref.split(/:(.+)/);
    if (k === "wo" && !canSee("workorders")) return deny("wo.view");
    ({ ac: showAircraft, wo: showWo, part: showPart, nc: showNc, crs: showCrs })[k](id);
  }
  function bind() {
    document.addEventListener("click", e => {
      const a = e.target.closest("[data-act]");
      if (a) { e.preventDefault(); const fn = ACTIONS[a.dataset.act]; if (fn) fn(a.dataset.id); return; }
      const o = e.target.closest("[data-open]"); if (o && o.dataset.open) { e.preventDefault(); return openRef(o.dataset.open); }
      const c = e.target.closest("[data-chip]"); if (c) { F[c.dataset.chip] = c.dataset.v; render(); }
    });
    document.addEventListener("keydown", e => { if (e.key === "Enter" && e.target.matches && e.target.matches("tr[data-open]")) openRef(e.target.dataset.open); });
    $("#dlg").addEventListener("click", e => { if (e.target === $("#dlg")) closeDlg(); });
    $("#dlg").addEventListener("close", () => { CURRENT = null; });
    $("#lang").addEventListener("change", e => { lang = e.target.value; try { localStorage.setItem(LANG_KEY, lang); } catch (_) { } render(); if (dlg().open && CURRENT) reopen(); });
    $("#user").addEventListener("change", e => {
      me = one("SELECT * FROM users WHERE id=?", [e.target.value]);
      try { localStorage.setItem(USER_KEY, me.id); } catch (_) { }
      safe(() => tx_(() => log("login", "log.login", { role: "@role." + me.role })));
      closeDlg(); toast(t("toast.login", { name: me.name, role: t("role." + me.role) }));
      if (!canSee(route())) location.hash = "#dashboard"; else render();
    });
    $("#search-form").addEventListener("submit", e => { e.preventDefault(); F.search = $("#gsearch").value; if (location.hash === "#search") render(); else location.hash = "#search"; });
    document.addEventListener("change", e => {
      if (e.target.dataset && e.target.dataset.role) {
        if (!can("user.manage")) return deny("user.manage");
        const u = one("SELECT * FROM users WHERE id=?", [e.target.dataset.role]); const nr = e.target.value;
        if (u.role === "ADMIN" && nr !== "ADMIN" && one("SELECT COUNT(*) n FROM users WHERE role='ADMIN' AND active=1").n <= 1) { toast(t("err.last_admin"), true); return render(); }
        safe(() => tx_(() => { run("UPDATE users SET role=? WHERE id=?", [nr, u.id]); log("user", "log.user_role", { name: u.name, from: "@role." + u.role, to: "@role." + nr }); }), "toast.saved");
      }
    });
    window.addEventListener("hashchange", () => { closeDlg(); render(); window.scrollTo(0, 0); });
  }

  /* =========================================================
     Démarrage
     ========================================================= */
  async function loadAsm() { // repli : version asm.js (sans WebAssembly ni chargement réseau)
    await new Promise((res, rej) => { const s = document.createElement("script"); s.src = "vendor/sql-asm.js"; if (location.protocol === "http:" || location.protocol === "https:") s.integrity = "sha384-ur9WCykw0SZNZ8drFEOH/m9+bB+wzKinbF63kpF2yRb4AYvAFbrGvvEC/RfCK8Wp"; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
    return await window.initSqlJs();
  }
  async function loadSqlJs() {
    if (location.protocol === "file:") return loadAsm(); // ouverture directe du fichier (démo locale)
    try { return await Promise.race([window.initSqlJs({ locateFile: f => "vendor/" + f }), new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), 8000))]); }
    catch (e) { return loadAsm(); }
  }
  async function start() {
    try {
      SQL = await loadSqlJs();
      const saved = await loadSaved();
      if (saved) { try { db = new SQL.Database(saved); one("SELECT COUNT(*) n FROM log"); if ((one("SELECT v FROM meta WHERE k='schema'") || {}).v !== "3") throw new Error("schema"); } catch (e) { db = null; } }
      if (!db) { freshDb(); persist(); }
      let uid = "u2"; try { uid = localStorage.getItem(USER_KEY) || uid; } catch (e) { }
      me = one("SELECT * FROM users WHERE id=? AND active=1", [uid]) || one("SELECT * FROM users WHERE active=1 ORDER BY id");
      SHA_OK = await selfTestSha();
      $("#boot").hidden = true; $("#app").hidden = false;
      bind(); render();
    } catch (e) {
      console.error(e);
      $("#boot").innerHTML = `<p class="err">${esc(t("err.boot"))}</p><p class="small muted">${esc(e.message || e)}</p>`;
    }
  }
  start();
})();
