/**
 * @file Quality and Part-21 actions: findings (non-conformities), audits,
 * document approval, design change (modification) workflow.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    $, esc, t, isoD, addDays, q, one, run, transact, log, can, nextId,
    val, field, select, formDlg, closeDlg, toast, safe, deny, sign, showNc
  } = MIS;

  /** Days allowed to close a finding, by level (L1 = immediate, aircraft AOG). */
  const NC_DELAY = { L1: 0, L2: 90, OBS: 30 };

  /* ---------------------------------------------------------
     Findings
     --------------------------------------------------------- */

  function ncFields() {
    const acs = q("SELECT reg, model FROM aircraft ORDER BY reg");
    return field("n-level", "col.level", select("n-level", ["L1", "L2", "OBS"].map(l => [l, t("lvl." + l)]), "L2")) +
      field("n-reg", "col.reg", select("n-reg", [["", t("nc.org")], ...acs.map(a => [a.reg, a.reg + " · " + a.model])])) +
      field("n-src", "col.source", select("n-src", ["internal", "audit", "reception", "authority"].map(s => ["@src." + s, t("src." + s)]))) +
      field("n-descr", "col.descr", `<textarea id="n-descr" class="input" rows="3" maxlength="400"></textarea>`, true) +
      `<div class="notice full">${esc(t("nc.l1_note"))}</div>`;
  }

  function submitNc() {
    const descr = val("n-descr");
    if (descr.length < 10) return t("err.descr_long");
    const level = val("n-level"), reg = val("n-reg") || null;
    const id = nextId("nc", "NC", 3);
    const due = addDays(NC_DELAY[level]);
    const owner = (one("SELECT id FROM users WHERE role='QUALITY' AND active=1") || S.me).id;
    safe(() => transact(() => {
      run("INSERT INTO nc(id,level,reg,descr,source,opened,due,status,owner) VALUES(?,?,?,?,?,?,?,?,?)", [id, level, reg, descr, val("n-src"), isoD(new Date()), due, "open", owner]);
      log("nc_open", "log.nc_open", { id, level });
    }), "toast.nc", { id });
    S.filters.nc = "open";
    showNc(id);
    location.hash = "#nc";
  }

  function newNc() {
    if (!can("nc.create")) return deny("nc.create");
    formDlg(t("nc.new"), ncFields(), t("nc.open"), submitNc);
  }

  function saveNc(id) {
    if (!can("nc.edit")) return deny("nc.edit");
    safe(() => transact(() => {
      run("UPDATE nc SET cause=?, action=? WHERE id=?", [val("nc-cause") || null, val("nc-action") || null, id]);
      log("nc_update", "log.nc_update", { id });
    }), "toast.saved");
  }

  /** Closing requires a root cause and a corrective action, then a signature. */
  function closeNc(id) {
    if (!can("nc.close")) return deny("nc.close");
    // Read the texts now: the signature dialog replaces the finding form.
    const cause = val("nc-cause"), action = val("nc-action");
    if (cause.length < 5 || action.length < 5) {
      $("#nc-err").textContent = t("err.nc_close");
      return;
    }
    sign("sign.purpose_nc", { id }, () => {
      safe(() => transact(() => {
        run("UPDATE nc SET cause=?, action=?, status='closed', closed_at=? WHERE id=?", [cause, action, isoD(new Date()), id]);
        log("nc_close", "log.nc_close", { id });
      }), "toast.nc_closed", { id });
      showNc(id);
    });
  }

  /* ---------------------------------------------------------
     Audits
     --------------------------------------------------------- */

  const AUDIT_SCOPES = [["Part-145", "Part-145"], ["Part-CAMO", "Part-CAMO"], ["Part-M", "Part-M"], ["Part-21", "Part-21"]];

  function newAudit() {
    if (!can("audit.manage")) return deny("audit.manage");
    const fields = field("au-title", "col.subject", `<input id="au-title" class="input" maxlength="100">`, true) +
      field("au-scope", "col.scope", select("au-scope", [...AUDIT_SCOPES, ["@scope.store", t("scope.store")]])) +
      field("au-date", "col.date", `<input id="au-date" class="input" type="date" value="${addDays(14)}">`);
    formDlg(t("aud.new"), fields, t("aud.plan"), () => {
      const title = val("au-title"), date = val("au-date");
      if (title.length < 3) return t("err.title");
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return t("err.date");
      const id = "AUD-" + date.slice(0, 4) + "-" + String(one("SELECT COUNT(*) n FROM audit").n + 1).padStart(2, "0") + "b";
      safe(() => transact(() => {
        run("INSERT INTO audit(id,title,scope,planned,auditor,status,findings) VALUES(?,?,?,?,?,?,0)", [id, title, val("au-scope"), date, S.me.id, "planned"]);
        log("audit_plan", "log.audit_plan", { id });
      }), "toast.saved");
      closeDlg();
    });
  }

  /** planned -> in_progress -> closed */
  function nextAuditStatus(id) {
    if (!can("audit.manage")) return deny("audit.manage");
    const a = one("SELECT * FROM audit WHERE id=?", [id]);
    const next = a.status === "planned" ? "in_progress" : "closed";
    safe(() => transact(() => {
      run("UPDATE audit SET status=? WHERE id=?", [next, id]);
      log("audit_status", "log.audit_status", { id, s: "@auds." + next });
    }), "toast.saved");
  }

  /* ---------------------------------------------------------
     Documents and modifications
     --------------------------------------------------------- */

  /** Approves the pending revision of a controlled document (signed). */
  function approveDoc(id) {
    if (!can("doc.approve")) return deny("doc.approve");
    const d = one("SELECT * FROM doc WHERE id=?", [id]);
    sign("sign.purpose_doc", { id, r: d.pending }, () => {
      safe(() => transact(() => {
        run("UPDATE doc SET rev=pending, pending=NULL, status='current', rev_date=? WHERE id=?", [isoD(new Date()), id]);
        log("doc_approve", "log.doc_approve", { id, rev: d.pending });
      }), "toast.doc", { id });
      closeDlg();
    });
  }

  const MOD_NEXT = { draft: "approved", approved: "in_work", in_work: "embodied" };

  /** Advances a modification; it is embodied only once its work orders are closed. */
  function nextModStatus(id) {
    if (!can("mod.manage")) return deny("mod.manage");
    const m = one("SELECT * FROM modif WHERE id=?", [id]);
    const next = MOD_NEXT[m.status];
    if (next === "embodied" && one("SELECT 1 FROM wo WHERE mod_id=? AND status!='closed'", [id])) return toast(t("err.mod_wo"), true);
    safe(() => transact(() => {
      run("UPDATE modif SET status=? WHERE id=?", [next, id]);
      log("mod_status", "log.mod_status", { id, s: "@mods." + next });
    }), "toast.saved");
  }

  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, {
    "new-nc": newNc,
    "nc-save": saveNc,
    "nc-close": closeNc,
    "new-audit": newAudit,
    "audit-next": nextAuditStatus,
    "doc-approve": approveDoc,
    "mod-next": nextModStatus
  });
})();
