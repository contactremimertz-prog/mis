/**
 * @file Airworthiness and business rules (no DOM access).
 *
 * - Maintenance programme dues by hours, cycles and calendar.
 * - Airworthiness directive (AD) compliance.
 * - Aircraft status: AOG (open level 1 finding), overdue, due soon, airworthy.
 * - Life-limited parts (LLP), EASA Form 1 checks, part installability.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const { q, one, addMonths, addDays, daysTo, isoD, TODAY, t } = MIS;

  /** "Due soon" thresholds. */
  const SOON = { hours: 25, cycles: 30, days: 30 };

  /** Part number of the LED kit used by the Part-21 modification demo scenario. */
  const LED_KIT_PN = "125A55-0012-01";

  /** Display name of a user id ("-" if unknown). */
  function uname(id) {
    const u = one("SELECT name FROM users WHERE id=?", [id]);
    return u ? u.name : "-";
  }

  /** Authorisation number of a user id (never displayed unmasked). */
  function uauth(id) {
    const u = one("SELECT auth FROM users WHERE id=?", [id]);
    return u ? u.auth : "-";
  }

  /* ---------------------------------------------------------
     Maintenance programme
     --------------------------------------------------------- */

  /** Scheduled tasks with their due status, for one aircraft or the whole fleet. */
  function taskRows(reg) {
    const sql = `SELECT a.*, m.code, m.title, m.interval_h, m.interval_c, m.interval_m, m.ref, c.hours, c.cycles, c.model
                 FROM ac_task a JOIN mp_task m ON m.id=a.task_id JOIN aircraft c ON c.reg=a.reg
                 ${reg ? "WHERE a.reg=?" : ""} ORDER BY a.reg, m.code`;
    return q(sql, reg ? [reg] : []).map(dueOf);
  }

  /** Remaining hours/cycles/days before the next due point, and status. */
  function dueOf(row) {
    const remH = row.interval_h ? Math.round((row.last_h + row.interval_h - row.hours) * 10) / 10 : null;
    const remC = row.interval_c ? row.last_c + row.interval_c - row.cycles : null;
    const nextDate = row.interval_m ? addMonths(row.last_date, row.interval_m) : null;
    const remD = nextDate ? daysTo(nextDate) : null;
    return Object.assign(row, {
      remH, remC, remD, nextDate,
      nextH: row.interval_h ? row.last_h + row.interval_h : null,
      nextC: row.interval_c ? row.last_c + row.interval_c : null,
      st: dueStatus(remH, remC, remD)
    });
  }

  /** "overdue" if any limit is exceeded, "soon" if any is close, else "ok". */
  function dueStatus(remH, remC, remD) {
    const below = (v, limit) => v !== null && v < limit;
    const within = (v, limit) => v !== null && v <= limit;
    if (below(remH, 0) || below(remC, 0) || below(remD, 0)) return "overdue";
    if (within(remH, SOON.hours) || within(remC, SOON.cycles) || within(remD, SOON.days)) return "soon";
    return "ok";
  }

  /* ---------------------------------------------------------
     Airworthiness directives
     --------------------------------------------------------- */

  /** AD applicability rows with status, for one aircraft or the whole fleet. */
  function adRows(reg) {
    const sql = `SELECT x.*, a.title, a.kind, a.interval_h, a.effective, a.comply_days, a.model, c.hours
                 FROM ac_ad x JOIN ad a ON a.id=x.ad_id JOIN aircraft c ON c.reg=x.reg
                 ${reg ? "WHERE x.reg=?" : ""} ORDER BY x.reg`;
    return q(sql, reg ? [reg] : []).map(adStatus);
  }

  /** Open AD: due by date. Applied repetitive AD: due by hours. */
  function adStatus(row) {
    let st = "ok", due = null, remH = null;
    if (row.status === "open") {
      due = addDays(daysTo(row.effective) + row.comply_days);
      const d = daysTo(due);
      st = d < 0 ? "overdue" : d <= SOON.days ? "soon" : "ok";
    } else if (row.status === "applied" && row.kind === "repeat") {
      remH = Math.round((row.last_h + row.interval_h - row.hours) * 10) / 10;
      st = remH < 0 ? "overdue" : remH <= SOON.hours ? "soon" : "ok";
    }
    return Object.assign(row, { st, due, remH });
  }

  /* ---------------------------------------------------------
     Aircraft status
     --------------------------------------------------------- */

  /** True when the aircraft has an open level 1 finding (Aircraft On Ground). */
  const isAog = reg => !!one("SELECT 1 FROM nc WHERE reg=? AND level='L1' AND status='open'", [reg]);

  /**
   * Overall status of an aircraft.
   * @returns {{k:string, code:string, tasks:Array, ads:Array, arcD:number}}
   *   k = colour class, code = "aog" | "overdue" | "soon" | "airworthy"
   */
  function acStatus(a) {
    const tasks = taskRows(a.reg), ads = adRows(a.reg);
    const arcD = daysTo(a.arc_expiry);
    const any = st => tasks.some(x => x.st === st) || ads.some(x => x.st === st);
    const result = (k, code) => ({ k, code, tasks, ads, arcD });
    if (isAog(a.reg)) return result("crit", "aog");
    if (any("overdue") || arcD < 0) return result("crit", "overdue");
    if (any("soon") || arcD <= SOON.days) return result("warn", "soon");
    return result("ok", "airworthy");
  }

  /** Colour classes of the status pills. */
  const ST_K = { ok: "ok", soon: "warn", overdue: "crit" };
  const WO_K = { open: "plain", in_progress: "info", awaiting_crs: "warn", closed: "ok" };
  const NC_K = { L1: "crit", L2: "warn", OBS: "info" };
  const PART_K = { stock: "ok", installed: "info", quarantine: "crit", consumed: "plain" };

  /* ---------------------------------------------------------
     Parts
     --------------------------------------------------------- */

  /** Life-limited part status: percentage of life used, or days to the limit date. */
  function llp(part) {
    if (part.limit_h) {
      const pct = Math.round(100 * part.tsn / part.limit_h);
      return { pct, k: pct >= 95 ? "crit" : pct >= 85 ? "warn" : "ok" };
    }
    if (part.limit_date) {
      const days = daysTo(part.limit_date);
      return { days, k: days < 0 ? "crit" : days <= SOON.days ? "warn" : "ok" };
    }
    return null;
  }

  /** A part may be installed only with a complete Form 1 and remaining life. */
  function isInstallable(p) {
    if (!p.form1 || !p.form1_org) return false;
    if (p.limit_date && p.limit_date < isoD(TODAY)) return false;
    if (p.limit_h && p.tsn >= p.limit_h) return false;
    return true;
  }

  /** Serviceable stock that can be installed on an aircraft. */
  function installableStock() {
    return q(`SELECT * FROM part WHERE status='stock' AND form1 IS NOT NULL AND form1_org IS NOT NULL
              AND (limit_date IS NULL OR limit_date>=?) AND (limit_h IS NULL OR tsn<limit_h) ORDER BY pn`, [isoD(TODAY)]);
  }

  /** True when the modification work order is blocked by the quarantined LED kit. */
  function isModBlocked(wo) {
    if (wo.kind !== "mod") return false;
    if (one("SELECT 1 FROM part WHERE wo_id=? AND status='installed'", [wo.id])) return false;
    return !!one("SELECT 1 FROM part WHERE pn=? AND status='quarantine'", [LED_KIT_PN]);
  }

  /** True when a modification cannot start: kit in quarantine and none in stock. */
  function isKitMissing() {
    return !!one("SELECT 1 FROM part WHERE pn=? AND status='quarantine'", [LED_KIT_PN]) &&
      !one("SELECT 1 FROM part WHERE pn=? AND status='stock'", [LED_KIT_PN]);
  }

  /**
   * Validates an EASA Form 1 entry.
   * @returns {string|null} translated error message, or null when valid
   */
  function form1Check(ref, org, date) {
    if (!/^F1-[A-Z0-9]{2,10}-\d{2}-\d{4,6}$/.test(ref)) return t("err.form1");
    if (!/^[A-Z]{2}\.(21G|145|21J)\.[A-Z0-9]{2,8}$/.test(org) || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return t("err.form1_fields");
    if (date > isoD(TODAY)) return t("err.form1_date");
    if (one("SELECT 1 FROM part WHERE form1=?", [ref])) return t("err.form1_dup");
    return null;
  }

  /** Next sequential id of the year, e.g. nextId("wo", "WO", 4) -> "WO-2026-0426". */
  function nextId(table, prefix, width) {
    const year = TODAY.getFullYear();
    const last = one(`SELECT id FROM ${table} WHERE id LIKE ? ORDER BY id DESC LIMIT 1`, [prefix + "-" + year + "-%"]);
    const n = last ? parseInt(last.id.split("-").pop(), 10) + 1 : 1;
    return prefix + "-" + year + "-" + String(n).padStart(width, "0");
  }

  Object.assign(MIS, {
    uname, uauth, taskRows, adRows, acStatus, isAog, llp, isInstallable, installableStock,
    isModBlocked, isKitMissing, form1Check, nextId, ST_K, WO_K, NC_K, PART_K
  });
})();
