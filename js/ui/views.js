/**
 * @file Screens (one function per navigation entry).
 *
 * Each view returns the HTML of the main area. Views that show a table
 * register it through table() so that the CSV/PDF export buttons export
 * exactly what is on screen. Views never write to the database.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const F = S.filters;
  const {
    esc, t, tx, fD, fTs, fH, fN, daysTo, q, one, can, canSee, maskAuth, uname, ROLES, SCREENS,
    taskRows, adRows, acStatus, llp, verifyLog, ST_K, WO_K, NC_K, PART_K,
    pill, acPill, remText, pageHead, exportBtns, actionBtn, rowBtn, chips, kv, list, openLink, table, tableNoExport
  } = MIS;

  const V = {};

  /** All aircraft, each with its computed status in `s`. */
  const fleetWithStatus = () => q("SELECT * FROM aircraft ORDER BY reg").map(a => Object.assign(a, { s: acStatus(a) }));

  /** Card with a header (title + optional link) and free content. */
  function card(titleHtml, content, linkHref) {
    const link = linkHref ? `<a class="link" href="${linkHref}">${esc(t("btn.see_all"))}</a>` : "";
    return `<div class="card"><div class="card-head"><h2>${titleHtml}</h2>${link}</div>${content}</div>`;
  }

  /** List row: left content and a right-hand pill. */
  const listRow = (left, right) => `<div><span>${left}</span>${right || ""}</div>`;

  const noneRow = () => `<div class="muted">${esc(t("dash.none"))}</div>`;

  /* =========================================================
     Dashboard
     ========================================================= */

  /** Overdue items (tasks, ADs, ARC) across the fleet. */
  function collectOverdue(fleet) {
    const out = [];
    fleet.forEach(a => {
      a.s.tasks.filter(x => x.st === "overdue").forEach(x => out.push({ reg: a.reg, what: tx(x.title), detail: remText(x) }));
      a.s.ads.filter(x => x.st === "overdue").forEach(x => out.push({ reg: a.reg, what: x.ad_id, detail: x.due ? t("ad.due", { d: fD(x.due) }) : remText(x) }));
      if (a.s.arcD < 0) out.push({ reg: a.reg, what: "ARC", detail: fD(a.arc_expiry) });
    });
    return out;
  }

  /** Tasks and ARC renewals due soon. */
  function collectSoon(fleet) {
    const out = [];
    fleet.forEach(a => {
      a.s.tasks.filter(x => x.st === "soon").forEach(x => out.push({ a, x }));
      if (a.s.arcD >= 0 && a.s.arcD <= 30) out.push({ a, arc: true });
    });
    return out;
  }

  function dashOverdueAlert(overdue) {
    if (!overdue.length) return "";
    const items = overdue.map(o => `<li>${openLink("ac:" + o.reg, o.reg)} · ${esc(o.what)} · ${esc(o.detail)}</li>`).join("");
    return `<section class="alert" role="alert"><strong>${esc(t("dash.overdue_title", { n: overdue.length }))}</strong><ul>${items}</ul></section>`;
  }

  function kpi(labelKey, value, cls, hint) {
    return `<div class="card kpi"><div class="label">${esc(t(labelKey))}</div><div class="value ${cls}">${value}</div><div class="hint">${esc(hint)}</div></div>`;
  }

  function dashKpis(d) {
    const ncCls = d.ncOpen.some(n => n.level === "L1") ? "crit" : d.ncOpen.length ? "warn" : "ok";
    return `<section class="kpis">
      ${kpi("kpi.airworthy", `${d.okN} / ${d.fleet.length}`, d.okN === d.fleet.length ? "ok" : "", t("kpi.airworthy_hint", { n: d.fleet.length - d.okN }))}
      ${kpi("kpi.wo", d.woOpen.length, "", t("kpi.wo_hint", { n: d.woOpen.filter(w => w.status === "awaiting_crs").length }))}
      ${kpi("kpi.nc", d.ncOpen.length, ncCls, t("kpi.nc_hint", { n: d.ncOpen.filter(n => n.level === "L1").length }))}
      ${kpi("kpi.docs", `${d.docPct} %`, d.docPct === 100 ? "ok" : "warn", t("kpi.docs_hint", { n: d.docs.filter(x => x.status !== "current").length }))}
    </section>`;
  }

  function dashFleetTiles(fleet) {
    const tiles = fleet.map(a => `<button class="ac" data-open="ac:${esc(a.reg)}"><span class="stripe ${a.s.k}"></span>` +
      `<span class="reg">${esc(a.reg)}</span><span class="mod">${esc(a.model)} · ${esc(a.base)}</span>` +
      `<span class="st ${a.s.k}">${esc(t("acst." + a.s.code))}</span></button>`).join("");
    return `<section class="card"><div class="card-head"><h2>${esc(t("dash.fleet"))}</h2><a class="link" href="#fleet">${esc(t("btn.see_all"))}</a></div>
      <div class="fleet">${tiles}</div></section>`;
  }

  function dashSoonCard(soon) {
    const rows = soon.map(s => {
      const detail = s.arc ? t("dash.arc_soon", { n: s.a.s.arcD, d: fD(s.a.arc_expiry) }) : tx(s.x.title) + " : " + remText(s.x);
      return listRow(`${openLink("ac:" + s.a.reg, s.a.reg, "mono")} <span class="muted">${esc(s.a.model)}</span><br><span class="small muted">${esc(detail)}</span>`, pill("warn", t("st.soon")));
    }).join("");
    return card(esc(t("dash.soon")), `<div class="list">${rows || noneRow()}</div>`);
  }

  const llpPill = l => pill(l.k, l.pct !== undefined ? t("llp.pct", { n: l.pct }) : t("llp.days", { n: l.days }));

  function dashLlpCard(parts) {
    const rows = parts.map(p => listRow(
      `${openLink("part:" + p.id, tx(p.descr))}<br><span class="small muted mono">${esc(p.pn)} · ${esc(p.sn || p.lot)} · ${esc(p.reg || p.location)}</span>`,
      llpPill(llp(p)))).join("");
    return card(esc(t("dash.llp")), `<div class="list">${rows || noneRow()}</div>`, "#stock");
  }

  function dashWoCard(woOpen) {
    const rows = woOpen.slice(0, 6).map(w => listRow(
      `${openLink("wo:" + w.id, w.id, "mono")} · <span class="mono">${esc(w.reg)}</span><br><span class="small muted">${esc(tx(w.title))}</span>`,
      pill(WO_K[w.status], t("wost." + w.status)))).join("");
    return card(esc(t("dash.wo")), `<div class="list">${rows}</div>`, canSee("workorders") ? "#workorders" : null);
  }

  function dashComplianceCard(fleet, docPct) {
    const gap = one("SELECT 1 FROM part WHERE form1 IS NULL AND status!='quarantine'");
    const rows = [
      listRow(esc(t("comp.log")), verifyLog() ? pill("ok", t("comp.intact")) : pill("crit", t("comp.broken"))),
      listRow(esc(t("comp.sod")), pill("ok", t("comp.active"))),
      listRow(esc(t("comp.trace")), gap ? pill("crit", t("comp.gap")) : pill("ok", t("comp.complete"))),
      listRow(esc(t("comp.docs")), pill(docPct === 100 ? "ok" : "warn", docPct === 100 ? t("comp.current") : t("comp.pending"))),
      listRow(esc(t("comp.arc")), fleet.some(a => a.s.arcD <= 30) ? pill("warn", t("comp.renew")) : pill("ok", t("comp.valid"))),
      `<div class="small muted">${esc(t("comp.simnote"))}</div>`
    ];
    return card(esc(t("dash.compliance")), `<div class="list">${rows.join("")}</div>`);
  }

  /** Collects every figure shown on the dashboard. */
  function dashboardData() {
    const fleet = fleetWithStatus();
    const docs = q("SELECT status FROM doc");
    return {
      fleet,
      okN: fleet.filter(a => a.s.code === "airworthy").length,
      woOpen: q("SELECT * FROM wo WHERE status!='closed' ORDER BY id DESC"),
      ncOpen: q("SELECT * FROM nc WHERE status='open'"),
      llpAlerts: q("SELECT * FROM part WHERE status IN ('installed','stock')").filter(p => { const l = llp(p); return l && l.k !== "ok"; }),
      docs,
      docPct: Math.round(100 * docs.filter(d => d.status === "current").length / docs.length),
      totalH: fleet.reduce((sum, a) => sum + a.hours, 0)
    };
  }

  V.dashboard = () => {
    const d = dashboardData();
    S.exportSpec = {
      title: "nav.fleet", rows: d.fleet, cols: [
        { h: "col.reg", v: a => a.reg }, { h: "col.model", v: a => a.model }, { h: "col.msn", v: a => a.msn },
        { h: "col.hours", v: a => fH(a.hours) }, { h: "col.status", v: a => t("acst." + a.s.code) }]
    };
    const greeting = { name: S.me.name.split(" ")[0], role: t("role." + S.me.role), n: d.fleet.length, h: fH(d.totalH) };
    return pageHead("dash.hello", "dash.sub", exportBtns(), greeting) +
      dashOverdueAlert(collectOverdue(d.fleet)) +
      dashKpis(d) +
      dashFleetTiles(d.fleet) +
      `<section class="grid2">${dashSoonCard(collectSoon(d.fleet))}${dashLlpCard(d.llpAlerts)}</section>` +
      `<section class="grid2">${dashWoCard(d.woOpen)}${dashComplianceCard(d.fleet, d.docPct)}</section>`;
  };

  /* =========================================================
     CAMO: fleet, maintenance programme, directives
     ========================================================= */

  V.fleet = () => {
    const models = ["all", ...q("SELECT DISTINCT model FROM aircraft ORDER BY model").map(r => r.model)];
    const rows = fleetWithStatus().filter(a => F.fleet === "all" || a.model === F.fleet);
    return pageHead("nav.fleet", "fleet.sub", exportBtns()) +
      `<section class="card"><div class="card-head">${chips("fleet", models, F.fleet, v => (v === "all" ? t("f.all") : v))}</div>` +
      table({
        title: "nav.fleet", rows, open: a => "ac:" + a.reg, cols: [
          { h: "col.reg", v: a => a.reg, cls: "mono strong" },
          { h: "col.model", v: a => a.model },
          { h: "col.msn", v: a => a.msn, cls: "mono" },
          { h: "col.base", v: a => a.base + " · " + tx(a.mission), html: a => `${esc(a.base)}<br><span class="small muted">${esc(tx(a.mission))}</span>` },
          { h: "col.hours", v: a => fH(a.hours), cls: "num" },
          { h: "col.cycles", v: a => fN(a.cycles), cls: "num" },
          { h: "col.arc", v: a => fD(a.arc_expiry), html: a => `${esc(fD(a.arc_expiry))}<br><span class="small ${a.s.arcD <= 30 ? "warn-t" : "muted"}">${esc(t("rem.d", { n: a.s.arcD }))}</span>` },
          { h: "col.status", v: a => t("acst." + a.s.code), html: a => acPill(a.s) }]
      }) + `</section>`;
  };

  const DUE_ORDER = { overdue: 0, soon: 1, ok: 2 };

  /** "100 h / 12 months" interval text of a programme task. */
  function intervalText(r) {
    return [r.interval_h ? r.interval_h + " h" : null, r.interval_c ? r.interval_c + " cyc" : null, r.interval_m ? t("unit.months", { n: r.interval_m }) : null]
      .filter(Boolean).join(" / ");
  }

  V.maintenance = () => {
    const rows = taskRows().sort((a, b) => (DUE_ORDER[a.st] - DUE_ORDER[b.st]) || a.reg.localeCompare(b.reg));
    const counts = { n: rows.length, o: rows.filter(r => r.st === "overdue").length, s: rows.filter(r => r.st === "soon").length };
    return pageHead("nav.maintenance", "mp.sub", exportBtns()) +
      `<section class="card"><div class="card-head"><h2>${esc(t("mp.count", counts))}</h2></div>` +
      table({
        title: "nav.maintenance", rows, open: r => "ac:" + r.reg, cols: [
          { h: "col.reg", v: r => r.reg, cls: "mono strong" },
          { h: "col.model", v: r => r.model },
          { h: "col.task", v: r => tx(r.title) },
          { h: "col.interval", v: intervalText },
          { h: "col.last", v: r => fD(r.last_date), html: r => `${esc(fD(r.last_date))}<br><span class="small muted num">${esc(fH(r.last_h))} h · ${esc(fN(r.last_c))} cyc</span>` },
          { h: "col.remaining", v: r => remText(r), cls: "num small" },
          { h: "col.status", v: r => t("st." + r.st), html: r => pill(ST_K[r.st], t("st." + r.st)) }]
      }) + `</section>`;
  };

  /** Compliance text of an AD row. */
  function adComplianceText(r) {
    if (r.status === "open") return t("ad.due", { d: fD(r.due) });
    if (r.status === "applied") return r.kind === "repeat" ? t("rem.h", { n: fH(r.remH) }) : fD(r.last_date);
    return "-";
  }

  /** Status pill of an AD row (shared with the aircraft dialog). */
  function adPill(r) {
    const k = r.st === "overdue" ? "crit" : r.status === "open" ? "warn" : r.status === "applied" ? "ok" : "plain";
    return pill(k, r.st === "overdue" ? t("st.overdue") : t("ads." + r.status));
  }

  V.directives = () => {
    return pageHead("nav.directives", "ad.sub", exportBtns()) + `<section class="card">` +
      table({
        title: "nav.directives", rows: adRows(), open: r => "ac:" + r.reg, cols: [
          { h: "col.ad", v: r => r.ad_id, cls: "mono strong" },
          { h: "col.reg", v: r => r.reg, cls: "mono" },
          { h: "col.model", v: r => r.model },
          { h: "col.subject", v: r => tx(r.title) },
          { h: "col.kind", v: r => t("adk." + r.kind) },
          { h: "col.compliance", v: adComplianceText },
          { h: "col.status", v: r => t("ads." + r.status), html: adPill }]
      }) + `<p class="small muted">${esc(t("ad.note"))}</p></section>`;
  };

  /* =========================================================
     Part-145: work orders and certificates
     ========================================================= */

  /** "signed / total" task cards of a work order. */
  function cardProgress(w) {
    const c = one("SELECT COUNT(*) n, SUM(insp IS NOT NULL) d FROM card WHERE wo_id=?", [w.id]);
    return (c.d || 0) + "/" + c.n;
  }

  function matchesWoFilter(w) {
    if (F.wo === "all") return true;
    return F.wo === "active" ? w.status !== "closed" : w.status === F.wo;
  }

  V.workorders = () => {
    const tabs = ["active", "awaiting_crs", "closed", "all"];
    const rows = q("SELECT w.*, c.model, c.msn FROM wo w JOIN aircraft c ON c.reg=w.reg ORDER BY w.id DESC").filter(matchesWoFilter);
    return pageHead("nav.workorders", "wo.sub", actionBtn(can("wo.create"), "new-wo", "wo.new") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("wo", tabs, F.wo, v => t("wof." + v))}</div>` +
      table({
        title: "nav.workorders", rows, open: w => "wo:" + w.id, cols: [
          { h: "col.wo", v: w => w.id, cls: "mono strong" },
          { h: "col.aircraft", v: w => w.reg + " · " + w.model + " MSN " + w.msn, html: w => `<span class="mono">${esc(w.reg)}</span> <span class="muted">· ${esc(w.model)} MSN ${esc(w.msn)}</span>` },
          { h: "col.task", v: w => tx(w.title) },
          { h: "col.kind", v: w => t("wok." + w.kind) },
          { h: "col.assignee", v: w => (w.assignee ? uname(w.assignee) : "-") },
          { h: "col.cards", v: cardProgress, cls: "num" },
          { h: "col.status", v: w => t("wost." + w.status), html: w => pill(WO_K[w.status], t("wost." + w.status)) }]
      }) + `</section>`;
  };

  /** "Name (••••••, B2)" certifier text: the personal code is always masked. */
  const certifierText = r => uname(r.certifier) + " (" + maskAuth(r.cert_auth) + (r.cert_cat ? " " + r.cert_cat : "") + ")";

  V.certificates = () => {
    return pageHead("nav.certificates", "crs.sub", exportBtns()) + `<section class="card">` +
      table({
        title: "nav.certificates", rows: q("SELECT * FROM crs ORDER BY at DESC"), open: r => "crs:" + r.id, cols: [
          { h: "col.crs", v: r => r.id, cls: "mono strong" },
          { h: "col.wo", v: r => r.wo_id, cls: "mono" },
          { h: "col.reg", v: r => r.reg, cls: "mono" },
          { h: "col.certifier", v: certifierText },
          { h: "col.approval", v: r => r.approval, cls: "mono" },
          { h: "col.date", v: r => fTs(r.at) },
          { h: "col.hours", v: r => fH(r.hours), cls: "num" }]
      }) + `</section>`;
  };

  /* =========================================================
     Part-21: modifications and Form 1 register
     ========================================================= */

  const MOD_K = { embodied: "ok", in_work: "info" };

  /** Form 1 cell: reference, or a "missing" pill. */
  const form1Cell = p => (p.form1 ? `<span class="mono">${esc(p.form1)}</span>` : pill("crit", t("p.missing")));

  function modTable() {
    return table({
      title: "nav.part21", rows: q("SELECT * FROM modif ORDER BY id DESC"), cols: [
        { h: "col.mod", v: r => r.id, cls: "mono strong" },
        { h: "col.subject", v: r => tx(r.title) },
        { h: "col.reg", v: r => r.reg || t("p21.fleetwide"), cls: "mono" },
        { h: "col.class", v: r => t("cls." + r.cls), html: r => pill(r.cls === "major" ? "warn" : "info", t("cls." + r.cls)) },
        { h: "col.approval", v: r => r.approval, cls: "mono" },
        { h: "col.status", v: r => t("mods." + r.status), html: r => pill(MOD_K[r.status] || "plain", t("mods." + r.status)) },
        { h: "", v: () => "", html: r => rowBtn(can("mod.manage") && r.status !== "embodied", "mod-next", r.id, t("p21.next")) }]
    });
  }

  function form1Register() {
    return tableNoExport({
      rows: q("SELECT * FROM part ORDER BY received DESC"), open: p => "part:" + p.id, cols: [
        { h: "col.form1", v: p => p.form1 || "-", html: form1Cell },
        { h: "col.pn", v: p => p.pn, cls: "mono" },
        { h: "col.descr", v: p => tx(p.descr) },
        { h: "col.received", v: p => fD(p.received) }]
    });
  }

  V.part21 = () => {
    return pageHead("nav.part21", "p21.sub", exportBtns()) +
      `<section class="card"><div class="card-head"><h2>${esc(t("p21.mods"))}</h2></div>${modTable()}</section>` +
      `<section class="card"><div class="card-head"><h2>${esc(t("p21.form1"))}</h2></div><p class="sub">${esc(t("p21.form1_sub"))}</p>${form1Register()}</section>`;
  };

  /* =========================================================
     Logistics: stock and purchase orders
     ========================================================= */

  function matchesStockFilter(p) {
    if (F.stock === "all") return true;
    if (F.stock === "llp") { const l = llp(p); return !!(l && l.k !== "ok"); }
    return p.status === F.stock;
  }

  /** Life column: progress bar (hours) or days to the limit date. */
  function lifeCell(p) {
    const l = llp(p);
    if (!l) return `<span class="muted">-</span>`;
    if (l.pct === undefined) return pill(l.k, t("llp.days", { n: l.days }));
    return `<div class="barrow"><div class="bar ${l.k}"><i style="width:${Math.min(100, l.pct)}%"></i></div><span class="num small">${l.pct} %</span></div>`;
  }

  function lifeText(p) {
    const l = llp(p);
    if (!l) return "-";
    return l.pct !== undefined ? l.pct + " %" : t("llp.days", { n: l.days });
  }

  V.stock = () => {
    const filters = ["all", "stock", "installed", "quarantine", "llp"];
    const rows = q("SELECT * FROM part ORDER BY id").filter(matchesStockFilter);
    return pageHead("nav.stock", "stock.sub", actionBtn(can("part.receive"), "receive", "stock.receive") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("stock", filters, F.stock, v => t("sf." + v))}</div>` +
      table({
        title: "nav.stock", rows, open: p => "part:" + p.id, cols: [
          { h: "col.pn", v: p => p.pn, cls: "mono strong" },
          { h: "col.descr", v: p => tx(p.descr) },
          { h: "col.snlot", v: p => p.sn || ("Lot " + p.lot), cls: "mono" },
          { h: "col.qty", v: p => fN(p.qty), cls: "num" },
          { h: "col.form1", v: p => p.form1 || t("p.missing"), html: form1Cell },
          { h: "col.location", v: p => p.reg || p.location || "-", cls: "mono" },
          { h: "col.life", v: lifeText, html: lifeCell },
          { h: "col.status", v: p => t("ps." + p.status), html: p => pill(PART_K[p.status], t("ps." + p.status)) }]
      }) + `</section>`;
  };

  const PO_K = { received: "ok", awaiting_doc: "crit" };

  V.orders = () => {
    return pageHead("nav.orders", "po.sub", actionBtn(can("po.create"), "new-po", "po.new") + exportBtns()) + `<section class="card">` +
      table({
        title: "nav.orders", rows: q("SELECT * FROM po ORDER BY id DESC"), cols: [
          { h: "col.po", v: r => r.id, cls: "mono strong" },
          { h: "col.pn", v: r => r.pn, cls: "mono" },
          { h: "col.descr", v: r => tx(r.descr) },
          { h: "col.qty", v: r => fN(r.qty), cls: "num" },
          { h: "col.supplier", v: r => tx(r.supplier) },
          { h: "col.date", v: r => fD(r.ordered) },
          { h: "col.status", v: r => t("pos." + r.status), html: r => pill(PO_K[r.status] || "info", t("pos." + r.status)) },
          { h: "", v: () => "", html: r => rowBtn(can("po.receive") && r.status === "ordered", "po-receive", r.id, t("po.receive")) }]
      }) + `</section>`;
  };

  /* =========================================================
     Quality: findings, audits, documents
     ========================================================= */

  /** Due date of a finding, with days left or late while it is open. */
  function ncDueCell(n) {
    if (n.status !== "open") return esc(fD(n.due));
    const d = daysTo(n.due);
    const cls = d < 0 ? "crit-t" : d <= 7 ? "warn-t" : "muted";
    return `${esc(fD(n.due))}<br><span class="small ${cls}">${esc(d < 0 ? t("late", { n: -d }) : t("rem.d", { n: d }))}</span>`;
  }

  V.nc = () => {
    const filters = ["open", "closed", "all"];
    const rows = q("SELECT * FROM nc ORDER BY id DESC").filter(n => F.nc === "all" || n.status === F.nc);
    return pageHead("nav.nc", "nc.sub", actionBtn(can("nc.create"), "new-nc", "nc.new") + exportBtns()) +
      `<section class="card"><div class="card-head">${chips("nc", filters, F.nc, v => t("ncf." + v))}</div>` +
      table({
        title: "nav.nc", rows, open: n => "nc:" + n.id, cols: [
          { h: "col.nc", v: n => n.id, cls: "mono strong" },
          { h: "col.level", v: n => t("lvl." + n.level), html: n => pill(NC_K[n.level], t("lvl." + n.level)) },
          { h: "col.descr", v: n => tx(n.descr), cls: "wide" },
          { h: "col.reg", v: n => n.reg || "-", cls: "mono" },
          { h: "col.due", v: n => fD(n.due), html: ncDueCell },
          { h: "col.status", v: n => t("ncs." + n.status), html: n => pill(n.status === "open" ? "warn" : "ok", t("ncs." + n.status)) }]
      }) + `</section>`;
  };

  const AUDIT_K = { closed: "ok", in_progress: "info" };

  V.audits = () => {
    const nextLabel = r => t(r.status === "planned" ? "aud.start" : "aud.close");
    return pageHead("nav.audits", "aud.sub", actionBtn(can("audit.manage"), "new-audit", "aud.new") + exportBtns()) + `<section class="card">` +
      table({
        title: "nav.audits", rows: q("SELECT * FROM audit ORDER BY planned"), cols: [
          { h: "col.audit", v: r => r.id, cls: "mono strong" },
          { h: "col.subject", v: r => tx(r.title) },
          { h: "col.scope", v: r => tx(r.scope) },
          { h: "col.date", v: r => fD(r.planned) },
          { h: "col.auditor", v: r => uname(r.auditor) },
          { h: "col.findings", v: r => fN(r.findings), cls: "num" },
          { h: "col.status", v: r => t("auds." + r.status), html: r => pill(AUDIT_K[r.status] || "plain", t("auds." + r.status)) },
          { h: "", v: () => "", html: r => rowBtn(can("audit.manage") && r.status !== "closed", "audit-next", r.id, nextLabel(r)) }]
      }) + `</section>`;
  };

  V.documents = () => {
    return pageHead("nav.documents", "doc.sub", exportBtns()) + `<section class="card">` +
      table({
        title: "nav.documents", rows: q("SELECT * FROM doc ORDER BY id"), cols: [
          { h: "col.ref", v: r => r.id, cls: "mono strong" },
          { h: "col.subject", v: r => tx(r.title) },
          { h: "col.category", v: r => tx(r.kind) },
          { h: "col.rev", v: r => r.rev + (r.pending ? " (" + r.pending + ")" : ""), html: r => `${esc(r.rev)}${r.pending ? `<br><span class="small muted">${esc(t("doc.received", { r: r.pending }))}</span>` : ""}` },
          { h: "col.date", v: r => fD(r.rev_date) },
          { h: "col.status", v: r => t("docs." + r.status), html: r => pill(r.status === "current" ? "ok" : "warn", t("docs." + r.status)) },
          { h: "", v: () => "", html: r => rowBtn(!!r.pending && can("doc.approve"), "doc-approve", r.id, t("doc.approve", { r: r.pending })) }]
      }) + `</section>`;
  };

  /* =========================================================
     Administration: users and audit log
     ========================================================= */

  /** Role cell: a select box for the administrator, plain text otherwise. */
  function roleCell(u, editable) {
    if (!editable || u.id === S.me.id) return esc(t("role." + u.role));
    const opts = ROLES.map(r => `<option value="${r}" ${u.role === r ? "selected" : ""}>${esc(t("role." + r))}</option>`).join("");
    return `<label class="sr-only" for="role-${esc(u.id)}">${esc(t("col.role"))}</label><select id="role-${esc(u.id)}" class="input" data-role="${esc(u.id)}">${opts}</select>`;
  }

  function userToggleCell(u, editable) {
    if (u.id === S.me.id) return `<span class="small muted">${esc(t("u.you"))}</span>`;
    return rowBtn(editable, "user-toggle", u.id, t(u.active ? "u.suspend" : "u.reactivate"));
  }

  function usersTable(editable) {
    const status = u => t(u.active ? "u.active" : "u.suspended");
    return table({
      title: "nav.users", rows: q("SELECT * FROM users ORDER BY role, name"), cols: [
        { h: "col.name", v: u => u.name, cls: "strong" },
        { h: "col.role", v: u => t("role." + u.role), html: u => roleCell(u, editable) },
        { h: "col.auth", v: u => maskAuth(u.auth_hash), cls: "mono" },
        { h: "col.cat", v: u => u.cat || "-" },
        { h: "col.status", v: status, html: u => pill(u.active ? "ok" : "plain", status(u)) },
        { h: "", v: () => "", html: u => userToggleCell(u, editable) }]
    });
  }

  /** Screen x role matrix built from SCREENS (read-only documentation of the rights). */
  function rightsMatrix() {
    const yes = `<td class="yes"><span aria-hidden="true">●</span><span class="sr-only">${esc(t("yes"))}</span></td>`;
    const no = `<td class="no"><span aria-hidden="true">-</span><span class="sr-only">${esc(t("no"))}</span></td>`;
    const header = ROLES.map(r => `<th scope="col">${esc(t("role." + r))}</th>`).join("");
    const rows = SCREENS.flatMap(g => g.items).map(([screen, roles]) =>
      `<tr><td>${esc(t("nav." + screen))}</td>${ROLES.map(r => (roles.includes(r) ? yes : no)).join("")}</tr>`).join("");
    return `<div class="tablewrap"><table class="matrix"><thead><tr><th scope="col">${esc(t("col.screen"))}</th>${header}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  /** Database download and reset panel (administrator only). */
  function resetPanel() {
    return `<div class="danger"><div><strong>${esc(t("admin.reset"))}</strong><p class="small muted">${esc(t("admin.reset_sub"))}</p></div>
      <div class="toolbar"><button class="btn" data-act="db-download">${esc(t("admin.download"))}</button><button class="btn danger-btn" data-act="db-reset">${esc(t("admin.reset_btn"))}</button></div></div>`;
  }

  V.users = () => {
    const editable = can("user.manage");
    return pageHead("nav.users", "users.sub", exportBtns()) +
      `<section class="card">${usersTable(editable)}</section>` +
      `<section class="card"><div class="card-head"><h2>${esc(t("users.matrix"))}</h2></div>${rightsMatrix()}${editable ? resetPanel() : ""}</section>`;
  };

  /** Head hash card: to be copied and kept outside the workstation. */
  function anchorCard(rows) {
    const head = rows.length ? rows[0] : null;
    return `<section class="card"><div class="card-head"><h2>${esc(t("log.anchor_title"))}</h2><button class="btn small" data-act="copy-anchor">${esc(t("log.anchor_copy"))}</button></div>
      <p class="sub">${esc(t("log.anchor_sub"))}</p><p class="mono anchor" id="anchor">${esc(head ? head.h : "-")}</p>
      <p class="small muted">${esc(t("log.anchor_meta", { n: rows.length, d: head ? fTs(head.ts) : "-" }))}</p></section>`;
  }

  function actionCell(e) {
    const label = t("act." + e.action);
    return e.action === "denied" || e.action === "sign_fail" ? pill("crit", label) : `<strong>${esc(label)}</strong>`;
  }

  function logTable(rows) {
    return table({
      title: "nav.auditlog", rows, cols: [
        { h: "col.date", v: e => fTs(e.ts), cls: "mono" },
        { h: "col.user", v: e => uname(e.uid) },
        { h: "col.role", v: e => (e.role ? t("role." + e.role) : "-"), cls: "muted" },
        { h: "col.action", v: e => t("act." + e.action), html: actionCell },
        { h: "col.detail", v: e => t(e.msg, JSON.parse(e.params || "{}")), cls: "wide" },
        { h: "col.hash", v: e => e.h, html: e => `<span class="mono muted" title="${esc(e.prev)}">${esc(e.h.slice(0, 10))}</span>` }]
    });
  }

  V.auditlog = () => {
    const rows = q("SELECT * FROM log ORDER BY id DESC");
    const integrity = verifyLog() ? pill("ok", t("comp.intact")) : pill("crit", t("comp.broken"));
    const actions = `<button class="btn" data-act="verify">${esc(t("log.verify"))}</button>` + (can("log.export") ? exportBtns() : "");
    const html = pageHead("nav.auditlog", "log.sub", actions) +
      `<div class="notice">${esc(t("log.simulated"))}</div>` +
      anchorCard(rows) +
      `<section class="card"><div class="card-head"><h2>${esc(t("log.count", { n: rows.length }))}</h2>${integrity}</div>${logTable(rows)}</section>`;
    // Exports carry the head hash, to be kept outside the workstation (detects a full rewrite of the chain).
    if (S.exportSpec && rows.length) S.exportSpec.note = t("log.anchor_export", { h: rows[0].h, n: rows.length, d: fTs(rows[0].ts) });
    return html;
  };

  /* =========================================================
     Global search and access denied
     ========================================================= */

  /** Filters rows whose joined fields contain the search text (case-insensitive). */
  const textMatch = (rows, fields, needle) => rows.filter(r => fields(r).join(" ").toLowerCase().includes(needle));

  /** Result groups [titleKey, [{o: ref, a: label, b: detail}]] visible to the profile. */
  function searchGroups(s) {
    const like = "%" + s + "%", needle = s.toLowerCase();
    const groups = [];
    const add = (key, items) => { if (items.length) groups.push([key, items]); };
    add("nav.fleet", q("SELECT * FROM aircraft WHERE reg LIKE ? OR msn LIKE ? OR model LIKE ? OR base LIKE ?", [like, like, like, like])
      .map(a => ({ o: "ac:" + a.reg, a: a.reg, b: a.model + " · MSN " + a.msn + " · " + a.base })));
    if (canSee("workorders")) add("nav.workorders", textMatch(q("SELECT * FROM wo"), w => [w.id, w.reg, tx(w.title)], needle)
      .map(x => ({ o: "wo:" + x.id, a: x.id, b: x.reg + " · " + tx(x.title) })));
    if (canSee("stock")) add("nav.stock", textMatch(q("SELECT * FROM part"), p => [p.pn, p.sn, p.lot, p.form1, tx(p.descr), p.reg], needle)
      .map(x => ({ o: "part:" + x.id, a: x.pn, b: tx(x.descr) + " · " + (x.sn || x.lot) })));
    add("nav.nc", textMatch(q("SELECT * FROM nc"), n => [n.id, n.reg, tx(n.descr)], needle).map(x => ({ o: "nc:" + x.id, a: x.id, b: tx(x.descr) })));
    add("nav.documents", textMatch(q("SELECT * FROM doc"), d => [d.id, tx(d.title)], needle).map(x => ({ o: "", a: x.id, b: tx(x.title) })));
    return groups;
  }

  function searchGroupCard([titleKey, items]) {
    const rows = items.map(i => `<div>${i.o ? openLink(i.o, i.a, "mono") : `<span class="mono strong">${esc(i.a)}</span>`}<span class="muted" style="flex:1">${esc(i.b)}</span></div>`).join("");
    return `<section class="card"><div class="card-head"><h2>${esc(t(titleKey))}</h2></div><div class="list">${rows}</div></section>`;
  }

  V.search = () => {
    const s = F.search.trim();
    if (s.length < 2) return pageHead("search.title", "search.short");
    const groups = searchGroups(s);
    const total = groups.reduce((n, g) => n + g[1].length, 0);
    const body = groups.length ? groups.map(searchGroupCard).join("") : `<section class="card empty">${esc(t("search.none"))}</section>`;
    return pageHead("search.title", "search.count", "", { n: total, q: s }) + body;
  };

  V.denied = () => `<section class="card empty"><h1>${esc(t("denied.title"))}</h1>
    <p class="sub">${esc(t("denied.sub", { role: t("role." + S.me.role) }))}</p>
    <p><a class="btn" href="#dashboard">${esc(t("nav.dashboard"))}</a></p></section>`;

  MIS.VIEWS = V;
  Object.assign(MIS, { adPill, llpPill });
})();
