/**
 * @file File download helper and CSV export of the table on screen.
 *
 * CSV uses ";" (or "," in English), a UTF-8 BOM for spreadsheet software,
 * and neutralises formula injection (cells starting with = + - @ tab CR).
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const { t, isoD, toast, safe, logNow } = MIS;

  /** Starts a browser download of `blob` named `name`. */
  function download(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast(t("toast.download", { f: name }));
  }

  /** "fleet-2026-11-03" style file name from the current export title. */
  function fileBase() {
    const title = S.exportSpec ? t(S.exportSpec.title) : "export";
    const slug = title.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    return (S.exportSpec ? slug : "export") + "-" + isoD(new Date());
  }

  /** Exported columns (action columns without a header are skipped). */
  const exportCols = () => S.exportSpec.cols.filter(c => c.h);

  /** One CSV cell: formula injection neutralised (prefix '), then quoted if needed. */
  function csvCell(value) {
    let s = String(value ?? "");
    if (s !== "-" && /^[=+\-@\t\r]/.test(s)) s = "'" + s;
    return /[";,\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function exportCsv() {
    const spec = S.exportSpec;
    if (!spec) return;
    const sep = S.lang === "en" ? "," : ";";
    const cols = exportCols();
    const lines = [cols.map(c => csvCell(t(c.h))).join(sep), ...spec.rows.map(r => cols.map(c => csvCell(c.v(r))).join(sep))];
    if (spec.note) lines.push("", csvCell(spec.note));
    download(new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }), fileBase() + ".csv");
    safe(() => logNow("export", "log.export", { f: "CSV", what: "@" + spec.title }));
  }

  Object.assign(MIS, { download, fileBase, exportCols, exportCsv });
  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, { csv: exportCsv });
})();
