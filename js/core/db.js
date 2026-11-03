/**
 * @file Database access (sql.js) and local persistence (IndexedDB).
 *
 * Every write goes through transact(), which commits or rolls back as a whole
 * and then saves the database file in the browser.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;

  /* ---------------------------------------------------------
     Query helpers
     --------------------------------------------------------- */

  /** Runs a SELECT and returns all rows as plain objects. */
  function q(sql, params) {
    const st = S.db.prepare(sql);
    st.bind(params || []);
    const rows = [];
    while (st.step()) rows.push(st.getAsObject());
    st.free();
    return rows;
  }

  /** Runs a SELECT and returns the first row, or null. */
  const one = (sql, params) => q(sql, params)[0] || null;

  /** Runs a statement that returns no rows (INSERT, UPDATE, ...). */
  const run = (sql, params) => S.db.run(sql, params || []);

  /**
   * Runs `fn` inside a transaction. On error everything is rolled back
   * (no partial write) and the error is re-thrown; on success the database
   * is persisted.
   */
  function transact(fn) {
    run("BEGIN");
    try {
      const result = fn();
      run("COMMIT");
      persist();
      return result;
    } catch (e) {
      try { run("ROLLBACK"); } catch (_) { /* nothing to roll back */ }
      throw e;
    }
  }

  /* ---------------------------------------------------------
     IndexedDB persistence (one key holding the SQLite file)
     --------------------------------------------------------- */

  function idbOpen() {
    return new Promise((resolve, reject) => {
      try {
        const req = indexedDB.open("mis-demo", 1);
        req.onupgradeneeded = () => req.result.createObjectStore("kv");
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      } catch (e) {
        reject(e);
      }
    });
  }

  /** Returns the saved SQLite file (Uint8Array) or null. */
  async function loadSaved() {
    try {
      const idb = await idbOpen();
      return await new Promise(resolve => {
        const req = idb.transaction("kv").objectStore("kv").get(MIS.KEYS.store);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch (e) {
      return null;
    }
  }

  /** Saves the database; falls back to "memory only" when storage is unavailable. */
  async function persist() {
    setSaveState("saving");
    try {
      const data = S.db.export();
      const idb = await idbOpen();
      await new Promise((resolve, reject) => {
        const tr = idb.transaction("kv", "readwrite");
        tr.objectStore("kv").put(data, MIS.KEYS.store);
        tr.oncomplete = resolve;
        tr.onerror = () => reject(tr.error);
      });
      setSaveState("saved");
    } catch (e) {
      setSaveState("memory");
    }
  }

  function setSaveState(value) {
    S.saveState = value;
    renderSaveState();
  }

  /** Updates the persistence indicator in the status bar. */
  function renderSaveState() {
    const el = MIS.$("#save-state");
    if (!el) return;
    el.textContent = MIS.t("save." + S.saveState);
    el.className = "save " + S.saveState;
  }

  /**
   * Creates a new database with the demo data.
   * @param {Array|undefined} keepLog existing audit log rows to copy unchanged
   *   (same hashes), used by the admin reset so the log is never lost.
   */
  function freshDb(keepLog) {
    const d = new S.SQL.Database();
    S.db = d;
    window.MIS_SEED.seed(d, MIS.TODAY, MIS.addDays, MIS.addMonths, MIS.addLog, { skipLog: !!keepLog });
    if (keepLog) {
      const st = d.prepare("INSERT INTO log(ts,uid,role,action,msg,params,prev,h) VALUES(?,?,?,?,?,?,?,?)");
      keepLog.forEach(e => st.run([e.ts, e.uid, e.role, e.action, e.msg, e.params, e.prev, e.h]));
      st.free();
    }
    return d;
  }

  Object.assign(MIS, { q, one, run, transact, loadSaved, persist, renderSaveState, freshDb });
})();
