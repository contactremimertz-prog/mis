/**
 * @file MIS assistant panel (validated answers only, static site).
 *
 * A floating button at the bottom right opens a panel over the page. The
 * assistant answers from window.MIS_KB through MIS.chatEngine; it never
 * writes to the database. The conversation and the "useful / not useful"
 * votes live in memory only (state.chat): nothing is stored, logged or sent,
 * and everything is cleared on sign-out, profile change or page close.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { $, esc, t, canSee } = MIS;
  const { SUGGESTED } = window.MIS_KB;

  S.chat = { open: false, owner: null, history: [], votes: {} };

  const fab = () => $("#chat-fab");
  const panel = () => $("#chat-panel");

  /* ---------------------------------------------------------
     Content helpers
     --------------------------------------------------------- */

  /** Texts of entry `id` in the UI language. */
  const textOf = id => MIS.chatEngine.entry(id)[S.lang] || MIS.chatEngine.entry(id).fr;

  /** Question button (frequent question or clarification choice). */
  const askBtn = (id, cls) =>
    `<button type="button" class="${cls}" data-chat="ask" data-id="${esc(id)}">${esc(textOf(id).q)}</button>`;

  /** Link to the screen of an answer, only when the profile may open it. */
  function screenLink(entry) {
    if (!entry.screen || !canSee(entry.screen)) return "";
    const name = t("nav." + entry.screen);
    return `<a class="chat-link" href="#${esc(entry.screen)}">${esc(t("chat.open_screen", { s: name }))}</a>`;
  }

  /** Yes / no feedback buttons of the answer at history index `i`. */
  function feedback(i) {
    const vote = S.chat.votes[i];
    const btn = (v, key) =>
      `<button type="button" class="chat-vote" data-chat="vote" data-i="${i}" data-v="${v}" aria-pressed="${vote === v}">${esc(t(key))}</button>`;
    const thanks = vote ? `<span class="chat-thanks">${esc(t("chat.thanks"))}</span>` : "";
    return `<div class="chat-feedback"><span>${esc(t("chat.useful"))}</span>${btn("up", "chat.yes")}${btn("down", "chat.no")}${thanks}</div>`;
  }

  /* ---------------------------------------------------------
     Messages
     --------------------------------------------------------- */

  function answerHtml(m, i) {
    const entry = MIS.chatEngine.entry(m.id);
    const tx = textOf(m.id);
    const badge = entry.refusal ? `<span class="chat-badge">${esc(t("chat.out_scope"))}</span>` : "";
    const lines = tx.a.map(p => `<p>${esc(p)}</p>`).join("");
    const sources = `<div class="chat-src"><strong>${esc(t("chat.sources"))}</strong> ${esc(tx.src.join(" · "))}</div>`;
    return `<div class="chat-msg bot">${badge}${lines}${sources}${screenLink(entry)}${feedback(i)}</div>`;
  }

  function clarifyHtml(m) {
    return `<div class="chat-msg bot ask"><p>${esc(t("chat.clarify"))}</p>` +
      `<div class="chat-choices">${m.ids.map(id => askBtn(id, "chat-chip")).join("")}</div></div>`;
  }

  function noneHtml() {
    const ids = SUGGESTED[S.me.role] || [];
    return `<div class="chat-msg bot ask"><p>${esc(t("chat.none"))}</p>` +
      `<div class="chat-choices">${ids.map(id => askBtn(id, "chat-chip")).join("")}</div></div>`;
  }

  /** One history item: the user's words, an answer, a clarification or "no answer". */
  function messageHtml(m, i) {
    if (m.kind === "user") return `<div class="chat-msg user">${esc(m.text)}</div>`;
    if (m.kind === "answer") return answerHtml(m, i);
    if (m.kind === "clarify") return clarifyHtml(m);
    return noneHtml();
  }

  const welcomeHtml = () => `<div class="chat-msg bot"><p>${esc(t("chat.welcome", { name: S.me.name }))}</p></div>`;

  /* ---------------------------------------------------------
     Panel
     --------------------------------------------------------- */

  function headerHtml() {
    const langs = MIS.LANGS.map(([code]) =>
      `<button type="button" data-chat="lang" data-v="${code}" aria-pressed="${code === S.lang}">${code.toUpperCase()}</button>`).join("");
    return `<header class="chat-head">
      <div><h2 id="chat-title">${esc(t("chat.title"))}</h2><p>${esc(t("chat.sub"))}</p></div>
      <div class="chat-langs" role="group" aria-label="${esc(t("chat.lang"))}">${langs}</div>
    </header>`;
  }

  function faqHtml() {
    const ids = SUGGESTED[S.me.role] || [];
    return `<div class="chat-faq-head"><span>${esc(t("chat.faq"))}</span>` +
      `<button type="button" class="chat-clear" data-chat="clear">${esc(t("chat.clear"))}</button></div>` +
      `<div class="chat-faq">${ids.map(id => askBtn(id, "chat-chip")).join("")}</div>`;
  }

  function formHtml() {
    return `<form id="chat-form" class="chat-form" novalidate>
      <label for="chat-input">${esc(t("chat.input"))}</label>
      <div class="chat-row">
        <textarea id="chat-input" rows="2" maxlength="200" placeholder="${esc(t("chat.placeholder"))}"></textarea>
        <button type="submit" class="btn primary">${esc(t("chat.send"))}</button>
      </div>
      <p class="chat-hint">${esc(t("chat.hint"))}</p>
    </form>`;
  }

  function panelHtml() {
    const log = welcomeHtml() + S.chat.history.map(messageHtml).join("");
    return headerHtml() +
      `<div class="chat-note" role="note">${esc(t("chat.disclaimer"))}</div>` +
      faqHtml() +
      `<div class="chat-log" id="chat-log" aria-live="polite">${log}</div>` +
      formHtml();
  }

  /** Redraws the button and, when open, the panel (the typed text and focus are kept). */
  function renderChat() {
    if (!S.me) { closeAndReset(); return; }
    if (S.chat.owner !== S.me.id) { S.chat.history = []; S.chat.votes = {}; S.chat.owner = S.me.id; }
    fab().hidden = false;
    fab().textContent = S.chat.open ? "×" : "?";
    fab().setAttribute("aria-expanded", String(S.chat.open));
    fab().setAttribute("aria-label", t(S.chat.open ? "chat.fab_close" : "chat.fab_open"));
    panel().hidden = !S.chat.open;
    if (!S.chat.open) return;
    const input = $("#chat-input");
    const typed = input ? input.value : "";
    const hadFocus = input && document.activeElement === input;
    panel().innerHTML = panelHtml();
    $("#chat-input").value = typed;
    if (hadFocus) $("#chat-input").focus();
    const log = $("#chat-log");
    log.scrollTop = log.scrollHeight;
  }

  /** Signed out: hide everything and forget the conversation. */
  function closeAndReset() {
    S.chat = { open: false, owner: null, history: [], votes: {} };
    fab().hidden = true;
    panel().hidden = true;
    panel().innerHTML = "";
  }

  /* ---------------------------------------------------------
     Actions
     --------------------------------------------------------- */

  function toggle(open) {
    S.chat.open = open;
    renderChat();
    if (open) $("#chat-input").focus();
    else fab().focus();
  }

  /** Answers a frequent question or a clarification choice. */
  function ask(id) {
    S.chat.history.push({ kind: "user", text: textOf(id).q }, { kind: "answer", id });
    renderChat();
  }

  /** Answers a typed question through the matching engine. */
  function send(text) {
    const clean = String(text || "").trim().slice(0, 200);
    if (!clean) return;
    const result = MIS.chatEngine.match(clean);
    S.chat.history.push({ kind: "user", text: clean }, result);
    $("#chat-input").value = "";
    renderChat();
    $("#chat-input").focus();
  }

  function onPanelClick(e) {
    const el = e.target.closest("[data-chat]");
    if (!el) return;
    const what = el.dataset.chat;
    if (what === "ask") ask(el.dataset.id);
    else if (what === "clear") { S.chat.history = []; S.chat.votes = {}; renderChat(); }
    else if (what === "vote") { S.chat.votes[el.dataset.i] = el.dataset.v; renderChat(); }
    else if (what === "lang") { MIS.setLang(el.dataset.v); MIS.render(); }
  }

  function onPanelKey(e) {
    if (e.key === "Escape") { e.preventDefault(); toggle(false); return; }
    if (e.key === "Enter" && !e.shiftKey && e.target.id === "chat-input") {
      e.preventDefault();
      send(e.target.value);
    }
  }

  /** Wires the button and the panel once, at start-up. */
  function bindChat() {
    fab().addEventListener("click", () => toggle(!S.chat.open));
    panel().addEventListener("click", onPanelClick);
    panel().addEventListener("keydown", onPanelKey);
    panel().addEventListener("submit", e => {
      if (e.target.id !== "chat-form") return;
      e.preventDefault();
      send($("#chat-input").value);
    });
  }

  Object.assign(MIS, { renderChat, bindChat });
})();
