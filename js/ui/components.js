/**
 * @file Reusable HTML building blocks, dialogs, toasts and the action wrapper.
 *
 * Every function returns an HTML string built with esc() for all dynamic
 * values, so data from the database can never inject markup.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { $, esc, t, fH, fN } = MIS;

  /* ---------------------------------------------------------
     Small components
     --------------------------------------------------------- */

  /** Coloured status pill. `k` is a colour class: ok, warn, crit, info, plain. */
  const pill = (k, label) => `<span class="pill ${k}">${esc(label)}</span>`;

  /** Pill of an aircraft status returned by acStatus(). */
  const acPill = status => pill(status.k, t("acst." + status.code));

  /** One part of a "remaining" text; negative values use the "_over" wording. */
  function remPart(value, key, format) {
    if (value === null || value === undefined) return null;
    return value < 0 ? t(key + "_over", { n: format(-value) }) : t(key, { n: format(value) });
  }

  /** "12.5 h · 30 cyc · 40 days" style remaining text of a due row. */
  function remText(row) {
    return [remPart(row.remH, "rem.h", fH), remPart(row.remC, "rem.c", fN), remPart(row.remD, "rem.d", x => x)]
      .filter(Boolean).join(" · ");
  }

  /** Page title, subtitle and toolbar. */
  function pageHead(titleKey, subKey, actions, params) {
    const sub = subKey ? `<p class="sub">${esc(t(subKey, params))}</p>` : "";
    return `<div class="page-head">
      <div><h1>${esc(t(titleKey, params))}</h1>${sub}</div>
      <div class="toolbar">${actions || ""}</div>
    </div>`;
  }

  /** CSV and PDF export buttons of the current table. */
  function exportBtns() {
    return `<button class="btn" data-act="csv">${esc(t("btn.csv"))}</button>` +
      `<button class="btn" data-act="pdf">${esc(t("btn.pdf"))}</button>`;
  }

  /** Primary toolbar button, shown only when `allowed` is true. */
  const actionBtn = (allowed, act, labelKey) =>
    (allowed ? `<button class="btn primary" data-act="${act}">${esc(t(labelKey))}</button>` : "");

  /** Small inline row button (`act` + record id), shown only when `allowed`. */
  const rowBtn = (allowed, act, id, label) =>
    (allowed ? `<button class="btn small" data-act="${act}" data-id="${esc(id)}">${esc(label)}</button>` : "");

  /** Filter chips; clicking one sets state.filters[name] and re-renders. */
  function chips(name, values, current, labelFn) {
    const buttons = values.map(v =>
      `<button class="chip" data-chip="${name}" data-v="${esc(v)}" aria-pressed="${current === v}">${esc(labelFn(v))}</button>`);
    return `<div class="toolbar" role="group">${buttons.join("")}</div>`;
  }

  /** Marks a string as trusted HTML (already escaped) for kv(). */
  const html = markup => ({ html: String(markup) });

  /** Renders a kv() value: escaped text by default, raw only when marked with html(). */
  const kvValue = v => (v && typeof v === "object" && "html" in v ? v.html : esc(v ?? "-"));

  /**
   * Key/value list. `pairs` = [[labelKey, value], ...]. Values are escaped
   * unless wrapped with html(), so a caller cannot forget to escape data.
   */
  function kv(pairs) {
    return `<dl class="kv">${pairs.map(([k, v]) => `<div><dt>${esc(t(k))}</dt><dd>${kvValue(v)}</dd></div>`).join("")}</dl>`;
  }

  /** Simple list of rows, with an "empty" line when there is nothing. */
  function list(items, renderItem) {
    const body = items.map(renderItem).join("");
    return `<div class="list">${body || `<div class="muted">${esc(t("tbl.empty"))}</div>`}</div>`;
  }

  /** Link that opens a record dialog ("ac:F-XXXA", "wo:WO-...", ...). */
  const openLink = (ref, label, cls) => `<button class="link${cls ? " " + cls : ""}" data-open="${esc(ref)}">${esc(label)}</button>`;

  /* ---------------------------------------------------------
     Tables
     --------------------------------------------------------- */

  /**
   * Builds a table and registers it as the current export.
   * @param {object} spec {title, cols:[{h, v:(row)=>text, html?:(row)=>html, cls?}], rows, open?:(row)=>"type:id", empty?}
   *   `v` gives the plain text used for exports, `html` the optional rich cell.
   */
  function table(spec) {
    S.exportSpec = spec;
    const head = spec.cols.map(c => `<th scope="col">${esc(t(c.h))}</th>`).join("");
    const body = spec.rows.length ? spec.rows.map(r => tableRow(spec, r)).join("") : emptyRow(spec);
    return `<div class="tablewrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function tableRow(spec, row) {
    const ref = spec.open ? spec.open(row) : null;
    const attrs = ref ? ` class="click" tabindex="0" data-open="${esc(ref)}"` : "";
    const cells = spec.cols.map(c => `<td class="${c.cls || ""}">${c.html ? c.html(row) : esc(c.v(row))}</td>`).join("");
    return `<tr${attrs}>${cells}</tr>`;
  }

  const emptyRow = spec => `<tr><td colspan="${spec.cols.length}" class="empty">${esc(t(spec.empty || "tbl.empty"))}</td></tr>`;

  /** Same as table() but leaves the current export unchanged (secondary tables). */
  function tableNoExport(spec) {
    const keep = S.exportSpec;
    const html = table(spec);
    S.exportSpec = keep;
    return html;
  }

  /* ---------------------------------------------------------
     Forms
     --------------------------------------------------------- */

  /** Trimmed value of an input by id ("" if absent). */
  const val = id => ($("#" + id) ? $("#" + id).value.trim() : "");

  /** Labelled form field; `full` spans the whole form width. */
  const field = (id, label, input, full) =>
    `<div class="field${full ? " full" : ""}"><label for="${id}">${esc(t(label))}</label>${input}</div>`;

  /** Select box. `options` = [[value, label], ...]. */
  function select(id, options, current) {
    const opts = options.map(([v, l]) => `<option value="${esc(v)}" ${v === current ? "selected" : ""}>${esc(l)}</option>`);
    return `<select id="${id}" class="input">${opts.join("")}</select>`;
  }

  /* ---------------------------------------------------------
     Dialog, toast
     --------------------------------------------------------- */

  const dlg = () => $("#dlg");

  /** Opens (or replaces the content of) the modal dialog. */
  function openDlg(title, body, foot) {
    const close = `<button class="btn small" data-act="close" aria-label="${esc(t("btn.close"))}">${esc(t("btn.close"))}</button>`;
    $("#dlg-inner").innerHTML =
      `<div class="dlg-head"><h2 id="dlg-title">${esc(title)}</h2>${close}</div>` +
      `<div class="dlg-body">${body}</div>` +
      (foot ? `<div class="dlg-foot">${foot}</div>` : "");
    if (!dlg().open) dlg().showModal();
  }

  function closeDlg() {
    if (dlg().open) dlg().close();
  }

  /**
   * Generic form dialog. `onSubmit` returns an error message to display,
   * or nothing when the form was accepted.
   */
  function formDlg(title, fieldsHtml, submitLabel, onSubmit) {
    openDlg(title,
      `<form id="f-gen" class="fields" novalidate>${fieldsHtml}<p class="err full" id="gen-err" role="alert"></p></form>`,
      `<button class="btn" data-act="close">${esc(t("btn.cancel"))}</button>` +
      `<button class="btn primary" type="submit" form="f-gen">${esc(submitLabel)}</button>`);
    $("#f-gen").addEventListener("submit", e => {
      e.preventDefault();
      const err = onSubmit();
      if (err) $("#gen-err").textContent = err;
    });
  }

  let toastTimer;

  /** Shows a transient message; `bad` styles it as an error. */
  function toast(message, bad) {
    const el = $("#toast");
    el.textContent = message;
    el.className = bad ? "bad" : "";
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (el.hidden = true), 4200);
  }

  /* ---------------------------------------------------------
     Action wrapper
     --------------------------------------------------------- */

  /**
   * Runs a write action and refreshes the screen.
   * On success: optional toast `okKey`, re-render, and refresh of the open
   * record dialog (state.current). On error: error toast, nothing written.
   * @returns {boolean} true when the action succeeded
   */
  function safe(fn, okKey, params) {
    try {
      fn();
      if (okKey) toast(t(okKey, params));
      MIS.render();
      if (dlg().open && S.current && okKey) reopen();
      return true;
    } catch (e) {
      console.error(e);
      toast(t("err.generic", { m: e.message }), true);
      return false;
    }
  }

  /** Re-displays the record dialog named by state.current ("type:id"). */
  function reopen() {
    MIS.showRecord(S.current);
  }

  /** Logs a refused action and tells the user. */
  function deny(permKey) {
    safe(() => MIS.logNow("denied", "log.denied", { what: "@perm." + permKey }));
    toast(t("toast.denied"), true);
  }

  Object.assign(MIS, {
    pill, acPill, remText, pageHead, exportBtns, actionBtn, rowBtn, chips, kv, html, list, openLink,
    table, tableNoExport, val, field, select, dlg, openDlg, closeDlg, formDlg, toast, safe, reopen, deny
  });
})();
