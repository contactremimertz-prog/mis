/**
 * @file Demo session: sign-in and signature checks with a personal code.
 *
 * The code is checked against the PBKDF2 hash stored in `users.auth_hash`;
 * it is never stored or displayed in clear. Every success and failure is
 * written to the audit log.
 *
 * Throttling is computed from the audit log itself (persisted in IndexedDB),
 * so reloading the page does not reset it:
 * - per profile: MAX_FAILURES failed sign-ins or signatures within WINDOW_MS
 *   lock that profile for LOCK_MS after the last failure;
 * - globally: GLOBAL_MAX failed sign-ins within WINDOW_MS (all profiles)
 *   lock every sign-in, to slow down guessing across profiles.
 *
 * Demo limit: this runs in the browser. Clearing the site data or editing
 * the code bypasses it; production needs server-side authentication.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { q, one, transact, addLog, verifySecret, t } = MIS;

  const MAX_FAILURES = 5;
  const GLOBAL_MAX = 20;
  const WINDOW_MS = 10 * 60 * 1000;
  const LOCK_MS = 5 * 60 * 1000;
  const FAIL_ACTIONS = "('login_fail','sign_fail')";

  /** Codes are typed with or without dashes/spaces, in any case. */
  const normalize = typed => String(typed || "").toUpperCase().replace(/[\s-]/g, "");

  const isoAgo = ms => new Date(Date.now() - ms).toISOString();

  /** Failures of `uid` in the window, after its last successful sign-in. */
  function profileFailures(uid) {
    const lastOk = (one("SELECT MAX(ts) t FROM log WHERE uid=? AND action='login'", [uid]) || {}).t || "";
    const since = isoAgo(WINDOW_MS);
    const from = lastOk > since ? lastOk : since;
    return q(`SELECT ts FROM log WHERE uid=? AND action IN ${FAIL_ACTIONS} AND ts>? ORDER BY ts`, [uid, from]).map(r => r.ts);
  }

  /** Failed sign-ins of all profiles in the window. */
  const globalFailures = () => q("SELECT ts FROM log WHERE action='login_fail' AND ts>? ORDER BY ts", [isoAgo(WINDOW_MS)]).map(r => r.ts);

  /** Seconds left before the lock ends, given failure timestamps and a limit (0 if not locked). */
  function lockSeconds(failures, limit) {
    if (failures.length < limit) return 0;
    const until = Date.parse(failures[failures.length - 1]) + LOCK_MS;
    return Math.max(0, Math.ceil((until - Date.now()) / 1000));
  }

  /** Seconds before `uid` may try again (profile lock or global sign-in lock). */
  function lockRemaining(uid, forSignIn) {
    const own = lockSeconds(profileFailures(uid), MAX_FAILURES);
    return forSignIn ? Math.max(own, lockSeconds(globalFailures(), GLOBAL_MAX)) : own;
  }

  /** Active user by id, or null. */
  const activeUser = id => one("SELECT * FROM users WHERE id=? AND active=1", [id]);

  const logFor = (user, action, msg) => transact(() => addLog(user.id, action, msg, { role: "@role." + user.role }));

  /**
   * Checks the personal code typed for profile `uid`.
   * @returns {Promise<string|null>} translated error, or null when signed in (state.me is set)
   */
  async function signIn(uid, typed) {
    const user = activeUser(uid);
    if (!user) return t("err.login");
    const wait = lockRemaining(user.id, true);
    if (wait) return t("err.login_locked", { n: wait });
    if (!(await verifySecret(user.auth_hash, normalize(typed)))) {
      logFor(user, "login_fail", "log.login_fail");
      const locked = lockRemaining(user.id, true);
      return locked ? t("err.login_locked", { n: locked }) : t("err.login");
    }
    S.me = user;
    logFor(user, "login", "log.login");
    return null;
  }

  /**
   * Checks the signed-in profile's code for a signature (same lock as sign-in).
   * Failures are logged as "sign_fail".
   * @returns {Promise<string|null>} translated error, or null when the code is right
   */
  async function checkMySecret(typed) {
    if (!S.me) return t("err.sign");
    const wait = lockRemaining(S.me.id, false);
    if (wait) return t("err.login_locked", { n: wait });
    if (await verifySecret(S.me.auth_hash, normalize(typed))) return null;
    transact(() => addLog(S.me.id, "sign_fail", "log.sign_fail", {}));
    const locked = lockRemaining(S.me.id, false);
    return locked ? t("err.login_locked", { n: locked }) : t("err.sign");
  }

  Object.assign(MIS, { signIn, checkMySecret, lockRemaining });
})();
