/**
 * @file Sign-in screen and profile switch dialog.
 *
 * No screen is available before sign-in. Switching profile from the header
 * asks for the new profile's personal code.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { $, esc, t, q, openDlg, closeDlg, toast, signIn } = MIS;

  const activeUsers = () => q("SELECT * FROM users WHERE active=1 ORDER BY role, name");

  function profileOptions(selected) {
    return activeUsers().map(u =>
      `<option value="${esc(u.id)}" ${u.id === selected ? "selected" : ""}>${esc(u.name)} · ${esc(t("role." + u.role))}</option>`).join("");
  }

  const authField = id => `<div class="field"><label for="${id}">${esc(t("login.auth"))}</label>` +
    `<input id="${id}" class="input mono" type="password" autocomplete="off" spellcheck="false" required></div>`;

  /** Sign-in page shown in the main area while nobody is signed in. */
  function loginView() {
    return `<section class="card login"><h1>${esc(t("login.title"))}</h1><p class="sub">${esc(t("login.sub"))}</p>
      <form id="f-login" class="fields one" novalidate>
        <div class="field"><label for="login-user">${esc(t("login.profile"))}</label><select id="login-user" class="input">${profileOptions("u2")}</select></div>
        ${authField("login-auth")}
        <p class="err" id="login-err" role="alert"></p>
        <div class="field end"><button class="btn primary" type="submit">${esc(t("login.submit"))}</button></div>
      </form>
      <p class="small muted">${esc(t("login.hint"))}</p></section>`;
  }

  /**
   * Submits a sign-in form: disables the button while the hash is computed,
   * shows the error, or calls `onOk` once signed in.
   */
  function bindSignInForm(form, getUid, inputId, errId, onOk) {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const button = form.querySelector("button[type=submit]") || document.querySelector(`button[form="${form.id}"]`);
      if (button) { button.disabled = true; button.dataset.label = button.textContent; button.textContent = t("login.checking"); }
      const err = await signIn(getUid(), $("#" + inputId).value);
      if (button) { button.disabled = false; button.textContent = button.dataset.label; }
      if (err) {
        $("#" + errId).textContent = err;
        $("#" + inputId).value = "";
        return;
      }
      onOk();
    });
  }

  /** Wires the sign-in page after it has been rendered. */
  function bindLoginView() {
    const form = $("#f-login");
    if (!form) return;
    setTimeout(() => { const i = $("#login-auth"); if (i) i.focus(); }, 30);
    bindSignInForm(form, () => $("#login-user").value, "login-auth", "login-err", () => {
      toast(t("toast.login", { name: S.me.name, role: t("role." + S.me.role) }));
      MIS.afterSignIn();
    });
  }

  /** Header profile switch: asks for the chosen profile's code first. */
  function askProfileSwitch(uid) {
    const user = MIS.one("SELECT * FROM users WHERE id=? AND active=1", [uid]);
    if (!user) return MIS.render();
    openDlg(t("login.switch_title", { name: user.name }),
      `<form id="f-switch" class="fields one" novalidate>${authField("switch-auth")}<p class="err" id="switch-err" role="alert"></p></form>
       <p class="small muted">${esc(t("login.hint"))}</p>`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button><button class="btn primary" type="submit" form="f-switch">${esc(t("login.submit"))}</button>`);
    // Until the switch succeeds, the header keeps showing the current profile.
    $("#user").value = S.me.id;
    setTimeout(() => { const i = $("#switch-auth"); if (i) i.focus(); }, 30);
    bindSignInForm($("#f-switch"), () => uid, "switch-auth", "switch-err", () => {
      closeDlg();
      toast(t("toast.login", { name: S.me.name, role: t("role." + S.me.role) }));
      MIS.afterSignIn();
    });
  }

  Object.assign(MIS, { loginView, bindLoginView, askProfileSwitch });
})();
