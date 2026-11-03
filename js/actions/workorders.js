/**
 * @file Part-145 actions: work orders, task cards, part installation, CRS.
 *
 * Every handler first checks the permission (refusals are logged), validates
 * the business rules, then writes inside a single transaction.
 * Handlers are registered in MIS.ACTIONS under their data-act name.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    $, esc, t, tx, isoD, TODAY, q, one, run, transact, log, logNow, sha256, can, uname, taskRows, adRows,
    isAog, isKitMissing, isInstallable, installableStock, nextId, val, field, select, formDlg, toast,
    safe, deny, sign, showWo, showCrs
  } = MIS;

  const nowIso = () => new Date().toISOString();
  const activeTechs = () => q("SELECT * FROM users WHERE role='TECH' AND active=1");

  /** Generic task cards created for every new work order. */
  const DEFAULT_CARDS = ["@card.prep", "@card.perform", "@card.test", "@card.docs"];

  /* ---------------------------------------------------------
     New work order
     --------------------------------------------------------- */

  function newWoFields() {
    const acs = q("SELECT * FROM aircraft ORDER BY reg");
    return field("w-reg", "col.aircraft", select("w-reg", acs.map(a => [a.reg, a.reg + " · " + a.model + " MSN " + a.msn]))) +
      field("w-kind", "col.kind", select("w-kind", ["scheduled", "defect", "ad", "mod"].map(k => [k, t("wok." + k)]))) +
      field("w-task", "col.task", `<select id="w-task" class="input"></select>`, true) +
      field("w-free", "wo.free", `<input id="w-free" class="input" maxlength="120" placeholder="${esc(t("wo.free_ph"))}">`, true) +
      field("w-tech", "col.assignee", select("w-tech", [["", "-"], ...activeTechs().map(u => [u.id, u.name])]));
  }

  /** Fills the task list with the programme tasks or ADs of the selected aircraft. */
  function refreshTaskOptions() {
    const reg = val("w-reg"), kind = val("w-kind");
    let opts = [["", t("wo.free_opt")]];
    if (kind === "scheduled") opts = opts.concat(taskRows(reg).map(r => [String(r.id), tx(r.title) + " · " + t("st." + r.st)]));
    if (kind === "ad") opts = opts.concat(adRows(reg).filter(r => r.status === "open" || r.kind === "repeat").map(r => [String(r.id), r.ad_id + " · " + tx(r.title)]));
    $("#w-task").innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join("");
  }

  /** Title and link (programme task or AD) of the new work order. */
  function resolveWoSubject(kind, taskSel, free) {
    if (kind === "scheduled" && taskSel) {
      const r = one("SELECT a.id, m.title FROM ac_task a JOIN mp_task m ON m.id=a.task_id WHERE a.id=?", [+taskSel]);
      return { title: r.title, acTask: r.id, acAd: null };
    }
    if (kind === "ad" && taskSel) {
      const r = one("SELECT x.id, a.title FROM ac_ad x JOIN ad a ON a.id=x.ad_id WHERE x.id=?", [+taskSel]);
      return { title: r.title, acTask: null, acAd: r.id };
    }
    return { title: free, acTask: null, acAd: null };
  }

  function submitNewWo() {
    const reg = val("w-reg"), kind = val("w-kind");
    if (!reg) return t("err.required");
    const subject = resolveWoSubject(kind, val("w-task"), val("w-free"));
    if (!subject.title || subject.title.length < 3) return t("err.title");
    if (subject.acTask && one("SELECT 1 FROM wo WHERE ac_task_id=? AND status!='closed'", [subject.acTask])) return t("err.wo_dup");
    const id = nextId("wo", "WO", 4);
    const ok = safe(() => transact(() => {
      run("INSERT INTO wo(id,reg,title,kind,status,opened,planner,assignee,ac_task_id,ac_ad_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
        [id, reg, subject.title, kind, "open", isoD(new Date()), S.me.id, val("w-tech") || null, subject.acTask, subject.acAd]);
      DEFAULT_CARDS.forEach((c, i) => run("INSERT INTO card(wo_id,seq,title) VALUES(?,?,?)", [id, i + 1, c]));
      log("wo_create", "log.wo_create", { id, reg });
    }), "toast.wo_created", { id });
    if (ok) {
      S.filters.wo = "active";
      showWo(id);
      location.hash = "#workorders";
    }
  }

  function newWo() {
    if (!can("wo.create")) return deny("wo.create");
    formDlg(t("wo.new"), newWoFields(), t("wo.create"), submitNewWo);
    $("#w-reg").addEventListener("change", refreshTaskOptions);
    $("#w-kind").addEventListener("change", refreshTaskOptions);
    refreshTaskOptions();
  }

  /* ---------------------------------------------------------
     Start, assign
     --------------------------------------------------------- */

  function startWo(id) {
    if (!can("wo.start")) return deny("wo.start");
    const w = one("SELECT * FROM wo WHERE id=?", [id]);
    if (w.kind === "mod" && isKitMissing()) return toast(t("err.part_blocked"), true);
    safe(() => transact(() => {
      run("UPDATE wo SET status='in_progress', assignee=COALESCE(assignee,?) WHERE id=?", [S.me.id, id]);
      log("wo_start", "log.wo_start", { id });
    }), "toast.wo_started", { id });
  }

  function assignWo(id) {
    if (!can("wo.assign")) return deny("wo.assign");
    const techs = activeTechs();
    formDlg(t("wo.assign") + " · " + id, field("a-tech", "col.assignee", select("a-tech", techs.map(u => [u.id, u.name]))), t("btn.save"), () => {
      const uid = val("a-tech");
      if (!uid) return t("err.required");
      safe(() => transact(() => {
        run("UPDATE wo SET assignee=? WHERE id=?", [uid, id]);
        log("wo_assign", "log.wo_assign", { id, who: uname(uid) });
      }), "toast.saved");
      showWo(id);
    });
  }

  /* ---------------------------------------------------------
     Part installation (Form 1 and life limits re-checked)
     --------------------------------------------------------- */

  /** Moves the part (or one unit of a batch) from stores to the aircraft. */
  function recordInstall(p, w) {
    const now = nowIso();
    const move = (kind, from, to) => run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,wo_id,uid) VALUES(?,?,?,?,?,?,?)", [p.id, now, kind, from, to, w.id, S.me.id]);
    if (p.lot && p.qty > 1) {
      run("UPDATE part SET qty=qty-1 WHERE id=?", [p.id]);
      move("consume", p.location, w.reg);
    } else {
      run("UPDATE part SET status='installed', reg=?, wo_id=?, location=NULL, tsn=COALESCE(tsn,0) WHERE id=?", [w.reg, w.id, p.id]);
      move("issue", p.location, w.id);
      move("install", w.id, w.reg);
    }
    log("part_install", "log.part_install", { pn: p.pn, sn: p.sn || p.lot, reg: w.reg, wo: w.id });
  }

  function submitInstall(w) {
    const p = one("SELECT * FROM part WHERE id=?", [val("p-sel")]);
    if (!p || p.status !== "stock") return t("err.part_invalid");
    if (!isInstallable(p)) {
      safe(() => logNow("denied", "log.install_refused", { pn: p.pn, sn: p.sn || p.lot }));
      return t("err.install_check");
    }
    safe(() => transact(() => recordInstall(p, w)), "toast.part_installed");
    showWo(w.id);
  }

  function installPart(id) {
    if (!can("part.install")) return deny("part.install");
    const w = one("SELECT * FROM wo WHERE id=?", [id]);
    const stock = installableStock();
    if (!stock.length) return toast(t("err.no_stock"), true);
    const options = stock.map(p => [p.id, p.pn + " · " + tx(p.descr) + " · " + (p.sn || "Lot " + p.lot) + " · " + p.form1]);
    formDlg(t("wo.install") + " · " + w.reg,
      field("p-sel", "col.part", select("p-sel", options), true) + `<p class="small muted full">${esc(t("wo.install_note"))}</p>`,
      t("wo.install"), () => submitInstall(w));
  }

  /* ---------------------------------------------------------
     Task cards: technician signature, inspector countersignature
     --------------------------------------------------------- */

  function signCardTech(cardId) {
    if (!can("card.tech")) return deny("card.tech");
    const c = one("SELECT * FROM card WHERE id=?", [+cardId]);
    sign("sign.purpose_tech", { task: tx(c.title), wo: c.wo_id }, () => {
      safe(() => transact(() => {
        run("UPDATE card SET tech=?, tech_at=? WHERE id=? AND tech IS NULL", [S.me.id, nowIso(), +cardId]);
        log("card_tech", "log.card_tech", { wo: c.wo_id, n: c.seq });
      }), "toast.signed");
      showWo(c.wo_id);
    });
  }

  /** Countersigns a card; the last countersignature makes the WO ready for CRS. */
  function countersignCard(c) {
    run("UPDATE card SET insp=?, insp_at=? WHERE id=? AND insp IS NULL", [S.me.id, nowIso(), c.id]);
    log("card_insp", "log.card_insp", { wo: c.wo_id, n: c.seq });
    const left = one("SELECT COUNT(*) n FROM card WHERE wo_id=? AND insp IS NULL", [c.wo_id]).n;
    if (!left) {
      run("UPDATE wo SET status='awaiting_crs' WHERE id=?", [c.wo_id]);
      log("wo_ready", "log.wo_ready", { id: c.wo_id });
    }
  }

  function signCardInspector(cardId) {
    if (!can("card.insp")) return deny("card.insp");
    const c = one("SELECT * FROM card WHERE id=?", [+cardId]);
    if (!c.tech) return toast(t("err.need_tech"), true);
    if (c.tech === S.me.id) { // separation of duties: nobody inspects their own work
      safe(() => logNow("denied", "log.self_cert", { wo: c.wo_id }));
      return toast(t("err.self"), true);
    }
    sign("sign.purpose_insp", { task: tx(c.title), wo: c.wo_id }, () => {
      safe(() => transact(() => countersignCard(c)), "toast.signed");
      showWo(c.wo_id);
    });
  }

  /* ---------------------------------------------------------
     Certificate of Release to Service
     --------------------------------------------------------- */

  /** Returns a translated error when the CRS cannot be issued, or null. */
  function crsBlocker(w) {
    if (w.status !== "awaiting_crs") return t("err.not_ready");
    if (one("SELECT 1 FROM card WHERE wo_id=? AND tech=?", [w.id, S.me.id])) {
      safe(() => logNow("denied", "log.self_cert", { wo: w.id }));
      return t("err.self");
    }
    if (isAog(w.reg) && w.kind !== "defect") return t("err.aog_crs");
    return null;
  }

  /**
   * Writes the CRS and its consequences: WO closed, programme task or AD
   * reset to the current hours/cycles/date, modification embodied.
   * Approval, credential identifier and category are frozen in the CRS.
   */
  function recordCrs(cid, w) {
    const a = one("SELECT * FROM aircraft WHERE reg=?", [w.reg]);
    const at = nowIso(), today = isoD(new Date());
    const approval = (one("SELECT v FROM meta WHERE k='approval'") || { v: "FR.145.DEMO" }).v;
    const me = S.me;
    const credential = window.MIS_SEED.credentialId(me.auth_hash); // identifies the credential, reveals nothing
    const fp = sha256([cid, w.id, w.reg, me.id, credential, me.cat || "", approval, at, a.hours, a.cycles].join("|"));
    run("INSERT INTO crs(id,wo_id,reg,certifier,cert_auth,cert_cat,approval,at,hours,cycles,fp) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
      [cid, w.id, w.reg, me.id, credential, me.cat || null, approval, at, a.hours, a.cycles, fp]);
    run("UPDATE wo SET status='closed', crs_id=?, closed_at=? WHERE id=?", [cid, at, w.id]);
    if (w.ac_task_id) run("UPDATE ac_task SET last_h=?, last_c=?, last_date=? WHERE id=?", [a.hours, a.cycles, today, w.ac_task_id]);
    if (w.ac_ad_id) run("UPDATE ac_ad SET status='applied', last_h=?, last_date=?, wo_id=? WHERE id=?", [a.hours, today, w.id, w.ac_ad_id]);
    if (w.mod_id) run("UPDATE modif SET status='embodied' WHERE id=?", [w.mod_id]);
    log("crs_issue", "log.crs_issue", { id: cid, wo: w.id });
  }

  function issueCrs(id) {
    if (!can("crs.issue")) return deny("crs.issue");
    const w = one("SELECT * FROM wo WHERE id=?", [id]);
    const blocker = crsBlocker(w);
    if (blocker) return toast(blocker, true);
    sign("sign.purpose_crs", { wo: id, reg: w.reg }, () => {
      const cid = nextId("crs", "CRS", 4);
      S.current = null; // do not reopen the WO: the issued CRS is the confirmation
      const ok = safe(() => transact(() => recordCrs(cid, w)), "toast.crs", { id: cid });
      if (ok) showCrs(cid);
    });
  }

  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, {
    "new-wo": newWo,
    "wo-start": startWo,
    "wo-assign": assignWo,
    "wo-part": installPart,
    "card-tech": signCardTech,
    "card-insp": signCardInspector,
    crs: issueCrs
  });
})();
