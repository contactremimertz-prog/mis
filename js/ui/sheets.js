/**
 * @file Record dialogs ("sheets"): aircraft, work order, part, finding, CRS.
 *
 * Each show*() function reads the record, sets state.current so the dialog
 * can be refreshed after an action, and opens the modal. showRecord() opens a
 * dialog from a "type:id" reference (data-open attributes).
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    $, esc, t, tx, fD, fTs, fH, fN, q, one, run, can, canSee, maskAuth, uname, uauth, transact, log,
    acStatus, isModBlocked, llp, ST_K, WO_K, NC_K, PART_K,
    pill, acPill, remText, kv, html, list, openLink, tableNoExport, openDlg, safe, deny, adPill, llpPill
  } = MIS;

  const mono = v => `<span class="mono">${esc(v)}</span>`;
  const notice = (text, crit) => `<div class="notice${crit ? " crit" : ""}">${esc(text)}</div>`;
  const pdfBtn = (act, id, labelKey, primary) =>
    `<button class="btn${primary ? " primary" : ""}" data-act="${act}" data-id="${esc(id)}">${esc(t(labelKey || "btn.pdf_sheet"))}</button>`;

  /* =========================================================
     Aircraft
     ========================================================= */

  function aircraftKv(a, s) {
    return kv([
      ["col.msn", html(mono(a.msn))],
      ["col.year", a.mfg_year],
      ["col.base", a.base + " · " + tx(a.mission)],
      ["col.hours", fH(a.hours) + " h"],
      ["col.cycles", fN(a.cycles)],
      ["col.arc", html(esc(fD(a.arc_expiry)) + ` <span class="small muted">(${esc(t("rem.d", { n: s.arcD }))})</span>`)]
    ]);
  }

  /** Tasks, ADs, work orders, installed parts and CRS of the aircraft. */
  function aircraftSections(reg, s) {
    const wos = q("SELECT * FROM wo WHERE reg=? ORDER BY id DESC", [reg]);
    const parts = q("SELECT * FROM part WHERE reg=? AND status='installed'", [reg]);
    const crs = q("SELECT * FROM crs WHERE reg=? ORDER BY at DESC", [reg]);
    const h3 = key => `<h3>${esc(t(key))}</h3>`;
    return h3("ac.tasks") + tableNoExport({
      rows: s.tasks, cols: [
        { h: "col.task", v: r => tx(r.title) },
        { h: "col.remaining", v: r => remText(r), cls: "small num" },
        { h: "col.status", v: () => "", html: r => pill(ST_K[r.st], t("st." + r.st)) }]
    }) +
      h3("ac.ads") + tableNoExport({
        rows: s.ads, cols: [
          { h: "col.ad", v: r => r.ad_id, cls: "mono" },
          { h: "col.subject", v: r => tx(r.title) },
          { h: "col.status", v: () => "", html: adPill }]
      }) +
      h3("ac.wos") + list(wos, w => `<div>${openLink("wo:" + w.id, w.id, "mono")}<span style="flex:1">${esc(tx(w.title))}</span>${pill(WO_K[w.status], t("wost." + w.status))}</div>`) +
      h3("ac.parts") + list(parts, p => `<div>${openLink("part:" + p.id, tx(p.descr))}<span class="mono muted">${esc(p.pn)} · ${esc(p.sn || p.lot)}</span></div>`) +
      h3("ac.crs") + list(crs, c => `<div>${openLink("crs:" + c.id, c.id, "mono")}<span class="muted">${esc(fTs(c.at))}</span></div>`);
  }

  /** Flight hours entry form (CAMO and planner only). */
  function flightForm() {
    if (!can("fleet.hours")) return "";
    return `<h3>${esc(t("ac.flight"))}</h3><form id="f-hours" class="fields" novalidate>
      <div class="field"><label for="h-add">${esc(t("ac.hours_add"))}</label><input id="h-add" class="input" type="number" step="0.1" min="0.1" max="24" value="1.5" required></div>
      <div class="field"><label for="c-add">${esc(t("ac.cycles_add"))}</label><input id="c-add" class="input" type="number" step="1" min="0" max="60" value="2" required></div>
      <div class="field end"><button class="btn primary" type="submit">${esc(t("ac.save_flight"))}</button></div><p class="err" id="h-err" role="alert"></p></form>`;
  }

  /** Validates and records flown hours/cycles (also ages installed parts). */
  function bindFlightForm(reg, s) {
    const form = $("#f-hours");
    if (!form) return;
    form.addEventListener("submit", e => {
      e.preventDefault();
      const error = msg => ($("#h-err").textContent = msg);
      const h = parseFloat($("#h-add").value), c = parseInt($("#c-add").value, 10);
      if (!(h >= 0.1 && h <= 24)) return error(t("err.hours"));
      if (!(c >= 0 && c <= 60) || String(c) !== String($("#c-add").value).trim()) return error(t("err.cycles"));
      if (s.code === "aog") return error(t("err.aog"));
      safe(() => transact(() => {
        run("UPDATE aircraft SET hours=round(hours+?,1), cycles=cycles+? WHERE reg=?", [h, c, reg]);
        run("UPDATE part SET tsn=round(tsn+?,1) WHERE reg=? AND status='installed' AND tsn IS NOT NULL", [h, reg]);
        log("flight", "log.flight", { reg, h: fH(h), c });
      }), "toast.flight", { reg });
    });
  }

  function showAircraft(reg) {
    const a = one("SELECT * FROM aircraft WHERE reg=?", [reg]);
    if (!a) return;
    S.current = "ac:" + reg;
    const s = acStatus(a);
    const openNc = q("SELECT * FROM nc WHERE reg=? AND status='open'", [reg]);
    const body = `<div class="toolbar">${acPill(s)}</div>` +
      (s.code === "overdue" ? notice(t("ac.overdue_notice"), true) : "") +
      openNc.map(n => `<div class="notice crit"><strong>${esc(n.id)}</strong> · ${esc(tx(n.descr))}</div>`).join("") +
      aircraftKv(a, s) + aircraftSections(reg, s) + flightForm();
    openDlg(`${a.reg} · ${a.model}`, body, pdfBtn("pdf-ac", reg));
    bindFlightForm(reg, s);
  }

  /* =========================================================
     Work order
     ========================================================= */

  /** Buttons available for the work order, depending on status and role. */
  function woFooter(w) {
    const btn = (act, labelKey, primary) => `<button class="btn${primary ? " primary" : ""}" data-act="${act}" data-id="${esc(w.id)}">${esc(t(labelKey))}</button>`;
    let foot = "";
    if (w.status === "open" && can("wo.start")) foot += btn("wo-start", "wo.start", true);
    if (w.status === "open" && can("wo.assign")) foot += btn("wo-assign", "wo.assign");
    if (w.status === "in_progress" && can("part.install")) foot += btn("wo-part", "wo.install");
    if (w.status === "awaiting_crs" && can("crs.issue")) foot += btn("crs", "wo.crs", true);
    if (w.crs_id) foot += `<button class="btn" data-open="crs:${esc(w.crs_id)}">${esc(t("wo.view_crs"))}</button>`;
    return foot + pdfBtn("pdf-wo", w.id);
  }

  const waiting = key => `<span class="muted small">${esc(t(key))}</span>`;

  /** Sign button of an unsigned card cell, or the reason it cannot be signed yet. */
  function signButton(w, c, kind) {
    if (w.status !== "in_progress") return `<span class="muted">-</span>`;
    if (kind === "tech") {
      return can("card.tech") ? `<button class="btn small" data-act="card-tech" data-id="${c.id}">${esc(t("card.sign"))}</button>` : waiting("card.wait_tech");
    }
    if (!c.tech) return waiting("card.wait_tech");
    return can("card.insp") ? `<button class="btn small" data-act="card-insp" data-id="${c.id}">${esc(t("card.countersign"))}</button>` : waiting("card.wait_insp");
  }

  /** Signed cell: name, masked authorisation number and time. */
  function signedCell(uid, at) {
    return `<span class="signed">${esc(uname(uid))}</span><br><span class="small muted mono">${esc(maskAuth(uauth(uid)))} · ${esc(fTs(at))}</span>`;
  }

  /** Task cards with technician signature and inspector countersignature. */
  function cardsTable(w) {
    const cards = q("SELECT * FROM card WHERE wo_id=? ORDER BY seq", [w.id]);
    const rows = cards.map(c => `<tr><td class="num">${c.seq}</td><td>${esc(tx(c.title))}</td>
      <td>${c.tech ? signedCell(c.tech, c.tech_at) : signButton(w, c, "tech")}</td>
      <td>${c.insp ? signedCell(c.insp, c.insp_at) : signButton(w, c, "insp")}</td></tr>`).join("");
    return `<div class="tablewrap"><table><thead><tr><th>#</th><th>${esc(t("col.task"))}</th><th>${esc(t("card.tech"))}</th><th>${esc(t("card.insp"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  function woKv(w) {
    return kv([
      ["col.aircraft", html(`${openLink("ac:" + w.reg, w.reg, "mono")} · ${esc(w.model)} MSN ${esc(w.msn)}`)],
      ["col.kind", t("wok." + w.kind)],
      ["col.task", tx(w.title)],
      ["col.opened", fD(w.opened)],
      ["col.planner", uname(w.planner)],
      ["col.assignee", w.assignee ? uname(w.assignee) : "-"]
    ]);
  }

  function showWo(id) {
    const w = one("SELECT w.*, c.model, c.msn, c.hours, c.cycles FROM wo w JOIN aircraft c ON c.reg=w.reg WHERE w.id=?", [id]);
    if (!w) return;
    S.current = "wo:" + id;
    const parts = q("SELECT * FROM part WHERE wo_id=?", [id]);
    const mod = w.mod_id ? one("SELECT * FROM modif WHERE id=?", [w.mod_id]) : null;
    const blocked = isModBlocked(w);
    const body = `<div class="toolbar">${pill(WO_K[w.status], t("wost." + w.status))}${blocked ? pill("crit", t("wo.blocked")) : ""}</div>` +
      woKv(w) +
      (mod ? notice(t("wo.mod_link", { id: mod.id, a: mod.approval })) : "") +
      (blocked ? notice(t("wo.blocked_notice"), true) : "") +
      `<h3>${esc(t("wo.cards"))}</h3>${cardsTable(w)}` +
      `<h3>${esc(t("wo.parts"))}</h3>` + list(parts, p => `<div>${openLink("part:" + p.id, tx(p.descr))}<span class="mono muted">${esc(p.pn)} · ${esc(p.sn || p.lot)} · ${esc(p.form1 || "-")}</span></div>`) +
      `<p class="small muted">${esc(t("sign.simulated"))}</p>`;
    openDlg(w.id, body, woFooter(w));
  }

  /* =========================================================
     Part
     ========================================================= */

  function form1Value(p) {
    if (!p.form1) return pill("crit", t("p.missing"));
    const issuer = p.form1_org ? `<br><span class="small muted mono">${esc(p.form1_org)} · ${esc(fD(p.form1_date))}</span>` : "";
    return mono(p.form1) + issuer;
  }

  function limitText(p) {
    if (p.limit_h) return fN(p.limit_h) + " h";
    if (p.limit_date) return fD(p.limit_date);
    return t("p.nolimit");
  }

  function partKv(p) {
    return kv([
      ["col.pn", html(mono(p.pn))],
      ["col.snlot", html(mono(p.sn || "Lot " + p.lot))],
      ["col.form1", html(form1Value(p))],
      ["col.qty", fN(p.qty)],
      ["col.location", p.reg ? html(openLink("ac:" + p.reg, p.reg, "mono")) : (p.location || "-")],
      ["col.tsn", p.tsn !== null ? fH(p.tsn) + " h" : "-"],
      ["col.limit", limitText(p)],
      ["col.wo", p.wo_id ? html(openLink("wo:" + p.wo_id, p.wo_id, "mono")) : "-"]
    ]);
  }

  /** Traceability timeline: reception, issue, installation, release... */
  function partTimeline(id) {
    const moves = q("SELECT * FROM part_move WHERE part_id=? ORDER BY at", [id]);
    if (!moves.length) return `<ol class="timeline"><li class="muted">${esc(t("p.no_moves"))}</li></ol>`;
    const items = moves.map(m => `<li><span class="mono small muted">${esc(fTs(m.at))}</span> <strong>${esc(t("mv." + m.kind))}</strong> · ` +
      `${esc(tx(m.from_loc))} → ${esc(tx(m.to_loc))}${m.wo_id ? " · " + openLink("wo:" + m.wo_id, m.wo_id, "mono") : ""} · <span class="muted">${esc(uname(m.uid))}</span></li>`);
    return `<ol class="timeline">${items.join("")}</ol>`;
  }

  function showPart(id) {
    const p = one("SELECT * FROM part WHERE id=?", [id]);
    if (!p) return;
    S.current = "part:" + id;
    const l = llp(p);
    const attach = p.status === "quarantine" && can("part.doc") ? pdfBtn("part-doc", id, "p.attach", true) : "";
    const body = `<div class="toolbar">${pill(PART_K[p.status], t("ps." + p.status))}${l ? llpPill(l) : ""}</div>` +
      (p.status === "quarantine" ? notice(t("p.quarantine_notice"), true) : "") +
      partKv(p) + `<h3>${esc(t("p.trace"))}</h3>` + partTimeline(id);
    openDlg(`${p.pn} · ${tx(p.descr)}`, body, attach + pdfBtn("pdf-part", id));
  }

  /* =========================================================
     Finding (non-conformity)
     ========================================================= */

  function ncForm(n, editable) {
    const area = (id, labelKey, value) => `<div class="field"><label for="${id}">${esc(t(labelKey))}</label>` +
      `<textarea id="${id}" class="input" rows="2" maxlength="400" ${editable ? "" : "disabled"}>${esc(tx(value))}</textarea></div>`;
    return `<form id="f-nc" class="fields one" novalidate>${area("nc-cause", "nc.cause", n.cause)}${area("nc-action", "nc.action", n.action)}<p class="err" id="nc-err" role="alert"></p></form>`;
  }

  function showNc(id) {
    const n = one("SELECT * FROM nc WHERE id=?", [id]);
    if (!n) return;
    S.current = "nc:" + id;
    const editable = n.status === "open" && can("nc.edit");
    const body = `<div class="toolbar">${pill(NC_K[n.level], t("lvl." + n.level))}${pill(n.status === "open" ? "warn" : "ok", t("ncs." + n.status))}</div>` +
      kv([
        ["col.reg", n.reg ? html(openLink("ac:" + n.reg, n.reg, "mono")) : "-"],
        ["col.source", tx(n.source)],
        ["col.opened", fD(n.opened)],
        ["col.due", fD(n.due)],
        ["col.owner", uname(n.owner)],
        ["col.closed", fD(n.closed_at)]
      ]) +
      `<p><strong>${esc(t("col.descr"))} :</strong> ${esc(tx(n.descr))}</p>` + ncForm(n, editable);
    const foot = (editable ? `<button class="btn" data-act="nc-save" data-id="${esc(id)}">${esc(t("btn.save"))}</button>` : "") +
      (n.status === "open" && can("nc.close") ? `<button class="btn primary" data-act="nc-close" data-id="${esc(id)}">${esc(t("nc.close"))}</button>` : "");
    openDlg(n.id, body, foot);
  }

  /* =========================================================
     Certificate of Release to Service (CRS)
     ========================================================= */

  /** CRS record joined with its work order and aircraft (shared with the PDF export). */
  const crsRecord = id => one("SELECT c.*, w.title, w.kind, a.model, a.msn FROM crs c JOIN wo w ON w.id=c.wo_id JOIN aircraft a ON a.reg=c.reg WHERE c.id=?", [id]);

  function showCrs(id) {
    const c = crsRecord(id);
    if (!c) return;
    S.current = "crs:" + id;
    const category = c.cert_cat ? " · " + esc(t("col.cat")) + " " + esc(c.cert_cat) : "";
    const body = `<div class="certificate">
      <p class="eyebrow">${esc(t("crs.org", { a: c.approval }))}</p>
      <h3>${esc(t("crs.heading"))}</h3>
      ${kv([
        ["col.crs", html(mono(c.id))],
        ["col.wo", html(mono(c.wo_id))],
        ["col.aircraft", `${c.reg} · ${c.model} MSN ${c.msn}`],
        ["col.task", tx(c.title)],
        ["col.hours", fH(c.hours) + " h · " + fN(c.cycles) + " cyc"],
        ["col.date", fTs(c.at)]
      ])}
      <p class="statement">${esc(t("crs.statement"))}</p>
      <p><strong>${esc(t("col.certifier"))} :</strong> ${esc(uname(c.certifier))} · ${mono(maskAuth(c.cert_auth))}${category}</p>
      <p class="small muted">${esc(t("crs.simulated", { fp: String(c.fp).slice(0, 16) }))}</p>
    </div>`;
    openDlg(t("crs.title") + " · " + c.id, body, pdfBtn("pdf-crs", id, "btn.pdf_crs", true));
  }

  /* =========================================================
     Dispatch from a "type:id" reference
     ========================================================= */

  const SHEETS = { ac: showAircraft, wo: showWo, part: showPart, nc: showNc, crs: showCrs };

  /** Opens the dialog for a reference such as "wo:WO-2026-0415". */
  function showRecord(ref) {
    const [kind, id] = ref.split(/:(.+)/);
    SHEETS[kind](id);
  }

  /** Same as showRecord(), with the work order screen permission check (from links). */
  function openRecord(ref) {
    if (ref.startsWith("wo:") && !canSee("workorders")) return deny("wo.view");
    showRecord(ref);
  }

  Object.assign(MIS, { showAircraft, showWo, showPart, showNc, showCrs, showRecord, openRecord, crsRecord });
})();
