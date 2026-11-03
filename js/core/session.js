/**
 * @file Demo session: sign-in of a profile with its authorisation number.
 *
 * The number is checked against the PBKDF2 hash stored in `users.auth_hash`;
 * it is never stored or displayed in clear. Every success and failure is
 * written to the audit log. After MAX_FAILURES consecutive failures, sign-in
 * is locked for LOCK_SECONDS.
 *
 * Demo limit: this runs in the browser. Production needs server-side
 * authentication (see README, "Limites").
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { one, transact, addLog, verifySecret, t } = MIS;

  const MAX_FAILURES = 5;
  const LOCK_SECONDS = 30;
  let failures = 0, lockedUntil = 0;

  /** Seconds left before sign-in is allowed again (0 when not locked). */
  const lockRemaining = () => Math.max(0, Math.ceil((lockedUntil - Date.now()) / 1000));

  /** Active user by id, or null. */
  const activeUser = id => one("SELECT * FROM users WHERE id=? AND active=1", [id]);

  /**
   * Checks the authorisation number typed for profile `uid`.
   * @returns {Promise<string|null>} translated error, or null when signed in (state.me is set)
   */
  async function signIn(uid, typed) {
    const wait = lockRemaining();
    if (wait) return t("err.login_locked", { n: wait });
    const user = activeUser(uid);
    if (!user) return t("err.login");
    const ok = await verifySecret(user.auth_hash, String(typed || "").trim().toUpperCase());
    if (!ok) {
      failures += 1;
      if (failures >= MAX_FAILURES) { lockedUntil = Date.now() + LOCK_SECONDS * 1000; failures = 0; }
      transact(() => addLog(user.id, "login_fail", "log.login_fail", { role: "@role." + user.role }));
      return t("err.login");
    }
    failures = 0;
    S.me = user;
    transact(() => addLog(user.id, "login", "log.login", { role: "@role." + user.role }));
    return null;
  }

  /** Checks the active profile's number without changing the session (signatures). */
  async function checkMySecret(typed) {
    if (!S.me) return false;
    return verifySecret(S.me.auth_hash, String(typed || "").trim().toUpperCase());
  }

  Object.assign(MIS, { signIn, checkMySecret, lockRemaining });
})();
