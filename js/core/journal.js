/**
 * @file Audit log (SIMULATED, demo only).
 *
 * - Append-only: SQL triggers in js/seed.js forbid UPDATE and DELETE on `log`.
 * - Hash chain: each entry stores the previous hash and
 *   SHA-256(prev | ts | uid | role | action | msg | params).
 * The head hash can be kept outside the workstation to detect a full rewrite.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;

  /** Fields hashed for an entry, in a fixed order. */
  const entryHash = (prev, ts, uid, role, action, msg, params) =>
    MIS.sha256([prev, ts, uid, role, action, msg, params].join("|"));

  /**
   * Appends an entry for user `uid`.
   * @param {string} action short code (e.g. "crs_issue"), translated as "act.<action>"
   * @param {string} msg translation key of the detail text
   * @param {object} params placeholders of `msg`
   * @param {string} [ts] ISO timestamp (defaults to now; the seed passes past dates)
   */
  function addLog(uid, action, msg, params, ts) {
    const last = MIS.one("SELECT h FROM log ORDER BY id DESC LIMIT 1");
    const prev = last ? last.h : MIS.GENESIS;
    const user = MIS.one("SELECT role FROM users WHERE id=?", [uid]);
    const role = user ? user.role : "";
    const at = ts || new Date().toISOString();
    const json = JSON.stringify(params || {});
    const h = entryHash(prev, at, uid, role, action, msg, json);
    MIS.run("INSERT INTO log(ts,uid,role,action,msg,params,prev,h) VALUES(?,?,?,?,?,?,?,?)", [at, uid, role, action, msg, json, prev, h]);
  }

  /** Appends an entry for the active profile. */
  const log = (action, msg, params) => addLog(S.me.id, action, msg, params);

  /** Recomputes the whole chain; false as soon as one link or hash is wrong. */
  function verifyLog() {
    let prev = MIS.GENESIS;
    for (const e of MIS.q("SELECT * FROM log ORDER BY id")) {
      if (e.prev !== prev) return false;
      if (entryHash(prev, e.ts, e.uid, e.role, e.action, e.msg, e.params) !== e.h) return false;
      prev = e.h;
    }
    return true;
  }

  /** Writes a single log entry in its own transaction (used for denials, logins, exports). */
  const logNow = (action, msg, params) => MIS.transact(() => log(action, msg, params));

  Object.assign(MIS, { addLog, log, logNow, verifyLog });
})();
