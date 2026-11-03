/**
 * @file SIMULATED electronic signature (demo only).
 *
 * The user re-types their personal code, which is checked against its PBKDF2
 * hash and never displayed. A wrong value is refused and logged ("sign_fail");
 * repeated failures lock the profile (see js/core/session.js). Production would use strong authentication and a qualified
 * signature instead.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { $, esc, t, openDlg, checkMySecret } = MIS;

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
      const err = await checkMySecret($("#sign-auth").value); // logs failures and applies the lock
      if (button) button.disabled = false;
      if (err) {
        MIS.render(); // refresh the header and the open screen (new log entry)
        $("#sign-err").textContent = err;
        $("#sign-auth").value = "";
        return;
      }
      onOk();
    });
  }

  MIS.sign = sign;
})();
