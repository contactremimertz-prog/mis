/**
 * @file Administration actions: users and roles, database download and reset,
 * audit log verification and head hash copy.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    $, t, isoD, q, one, run, transact, log, addLog, verifyLog, persist, freshDb, can,
    openDlg, closeDlg, toast, safe, deny, sign, esc
  } = MIS;

  /** True when `user` is the last active administrator (who must never be removed). */
  const isLastAdmin = user => user.role === "ADMIN" && !!user.active &&
    one("SELECT COUNT(*) n FROM users WHERE role='ADMIN' AND active=1").n <= 1;

  /* ---------------------------------------------------------
     Users
     --------------------------------------------------------- */

  function toggleUser(id) {
    if (!can("user.manage")) return deny("user.manage");
    const u = one("SELECT * FROM users WHERE id=?", [id]);
    if (isLastAdmin(u)) return toast(t("err.last_admin"), true);
    safe(() => transact(() => {
      run("UPDATE users SET active=? WHERE id=?", [u.active ? 0 : 1, id]);
      log("user", u.active ? "log.user_off" : "log.user_on", { name: u.name });
    }), "toast.saved");
  }

  /** Role change from the select box of the users screen. */
  function changeRole(userId, newRole) {
    if (!can("user.manage")) return deny("user.manage");
    const u = one("SELECT * FROM users WHERE id=?", [userId]);
    if (newRole !== "ADMIN" && isLastAdmin(u)) {
      toast(t("err.last_admin"), true);
      return MIS.render();
    }
    safe(() => transact(() => {
      run("UPDATE users SET role=? WHERE id=?", [newRole, u.id]);
      log("user", "log.user_role", { name: u.name, from: "@role." + u.role, to: "@role." + newRole });
    }), "toast.saved");
  }

  /* ---------------------------------------------------------
     Database
     --------------------------------------------------------- */

  function downloadDb() {
    if (!can("user.manage")) return deny("db.reset");
    MIS.download(new Blob([S.db.export()], { type: "application/x-sqlite3" }), "mis-demo-" + isoD(new Date()) + ".sqlite");
  }

  function confirmReset() {
    if (!can("db.reset")) return deny("db.reset");
    openDlg(t("admin.reset"), `<p>${esc(t("admin.reset_confirm"))}</p>`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button><button class="btn danger-btn" data-act="db-reset-ok">${esc(t("admin.reset_btn"))}</button>`);
  }

  /** The reset needs a re-authentication (signature). */
  function resetAfterSignature() {
    if (!can("db.reset")) return deny("db.reset");
    sign("sign.purpose_reset", {}, doReset);
  }

  /** Restores the demo data while keeping the whole audit log, then logs the reset. */
  function doReset() {
    if (!can("db.reset")) return deny("db.reset");
    const who = S.me.id;
    const keep = q("SELECT * FROM log ORDER BY id");
    S.db.close();
    freshDb(keep);
    S.me = one("SELECT * FROM users WHERE id=?", [who]) || one("SELECT * FROM users WHERE role='ADMIN'");
    addLog(S.me.id, "db_reset", "log.db_reset", { n: keep.length });
    persist();
    closeDlg();
    toast(t("toast.reset"));
    MIS.render();
  }

  /* ---------------------------------------------------------
     Audit log
     --------------------------------------------------------- */

  function verify() {
    const ok = verifyLog();
    const count = one("SELECT COUNT(*) n FROM log").n;
    toast(ok ? t("log.ok", { n: count }) + (S.shaOk ? " " + t("log.webcrypto") : "") : t("log.ko"), !ok);
  }

  function selectText(el) {
    if (!el) return;
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  /** Copies the head hash; falls back to selecting it when the clipboard is unavailable. */
  function copyAnchor() {
    const el = $("#anchor");
    const hash = el ? el.textContent : "";
    const fallback = () => { selectText(el); toast(t("log.anchor_select")); };
    try {
      navigator.clipboard.writeText(hash).then(() => toast(t("log.anchor_copied")), fallback);
    } catch (e) {
      fallback();
    }
  }

  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, {
    "user-toggle": toggleUser,
    "db-download": downloadDb,
    "db-reset": confirmReset,
    "db-reset-ok": resetAfterSignature,
    verify,
    "copy-anchor": copyAnchor
  });
  MIS.changeRole = changeRole;
})();
