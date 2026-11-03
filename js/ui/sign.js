/**
 * @file SIMULATED electronic signature (demo only).
 *
 * The user re-types their authorisation number, which is checked against
 * its PBKDF2 hash and never displayed. A wrong value is refused and logged
 * ("sign_fail"). Production would use strong authentication and a qualified
 * signature instead.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { $, esc, t, openDlg, safe, logNow, checkMySecret } = MIS;

  function signForm() {
    return `<form id="f-sign" class="fields one" novalidate>
      <div class="field"><label for="sign-auth">${esc(t("sign.label", { name: S.me.name }))}</label><input id="sign-auth" class="input mono" type="password" autocomplete="off" spellcheck="false" required></div>
      <p class="small muted">${esc(t("sign.hint"))}</p>
      <p class="err" id="sign-err" role="alert"></p>
    </form>`;
  }

  /**
   * Asks for the signature, then calls `onOk` when it matches.
   * @param {string} purposeKey translation key describing what is signed
   * @param {object} params placeholders of `purposeKey`
   * @param {Function} onOk called once the signature is accepted
   */
  function sign(purposeKey, params, onOk) {
    openDlg(t("sign.title"),
      `<div class="notice">${esc(t("sign.simulated"))}</div><p>${esc(t(purposeKey, params))}</p>${signForm()}`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button>` +
      `<button class="btn primary" type="submit" form="f-sign">${esc(t("sign.confirm"))}</button>`);
    setTimeout(() => { const input = $("#sign-auth"); if (input) input.focus(); }, 30);
    $("#f-sign").addEventListener("submit", async e => {
      e.preventDefault();
      const button = document.querySelector('button[form="f-sign"]');
      if (button) button.disabled = true;
      const ok = await checkMySecret($("#sign-auth").value);
      if (button) button.disabled = false;
      if (!ok) {
        safe(() => logNow("sign_fail", "log.sign_fail", {}));
        $("#sign-err").textContent = t("err.sign");
        $("#sign-auth").value = "";
        return;
      }
      onOk();
    });
  }

  MIS.sign = sign;
})();
