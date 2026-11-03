/**
 * @file PDF exports (jsPDF + AutoTable): current table, CRS, and record sheets
 * (aircraft, work order, part). Personal codes are never printed.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    t, tx, fD, fTs, fH, fN, q, one, maskAuth, uname, uauth, acStatus, remText,
    toast, safe, logNow, download, fileBase, exportCols, crsRecord
  } = MIS;

  const NAVY = [0, 32, 91];
  const INK = [15, 27, 45];
  const MUTED = [90, 100, 120];
  const MARGIN = { left: 12, right: 12 };
  const TABLE_STYLE = { styles: { fontSize: 8.5 }, headStyles: { fillColor: NAVY }, margin: MARGIN };

  /** Replaces characters missing from the standard PDF fonts. */
  const pdfSafe = s => String(s ?? "").replace(/[  ]/g, " ").replace(/[→]/g, "->").replace(/[’]/g, "'").replace(/[●✓]/g, "x");

  /** New A4 document, or null (with an error toast) when jsPDF is not loaded. */
  function newPdf(landscape) {
    if (!window.jspdf) { toast(t("err.pdf"), true); return null; }
    return new window.jspdf.jsPDF({ orientation: landscape ? "landscape" : "portrait", unit: "mm", format: "a4" });
  }

  /** Navy banner (application name, author and date) and the document title. */
  function pdfHeader(doc, title) {
    const w = doc.internal.pageSize.getWidth();
    doc.setFillColor(...NAVY); doc.rect(0, 0, w, 18, "F");
    doc.setTextColor(255, 255, 255); doc.setFont("helvetica", "bold"); doc.setFontSize(12);
    doc.text(pdfSafe(t("app.name")), 12, 11.5);
    doc.setFont("helvetica", "normal"); doc.setFontSize(9);
    doc.text(pdfSafe(t("pdf.generated", { d: fTs(new Date().toISOString()), u: S.me.name })), w - 12, 11.5, { align: "right" });
    doc.setTextColor(...INK); doc.setFont("helvetica", "bold"); doc.setFontSize(15);
    doc.text(pdfSafe(title), 12, 30);
  }

  /** Demo disclaimer and page numbers on every page. */
  function pdfFooter(doc) {
    const n = doc.getNumberOfPages(), w = doc.internal.pageSize.getWidth(), h = doc.internal.pageSize.getHeight();
    for (let i = 1; i <= n; i++) {
      doc.setPage(i);
      doc.setFont("helvetica", "normal"); doc.setFontSize(7.5); doc.setTextColor(...MUTED);
      doc.text(pdfSafe(t("pdf.footer")), 12, h - 8);
      doc.text(i + " / " + n, w - 12, h - 8, { align: "right" });
    }
  }

  /** Two-column label/value block; returns the next y position. */
  function pdfKv(doc, y, pairs) {
    doc.autoTable({
      startY: y, body: pairs.map(([k, v]) => [pdfSafe(t(k)), pdfSafe(v)]), theme: "plain",
      styles: { fontSize: 9.5, cellPadding: 1.6 }, columnStyles: { 0: { fontStyle: "bold", cellWidth: 55, textColor: [80, 90, 110] } }, margin: MARGIN
    });
    return doc.lastAutoTable.finalY + 6;
  }

  /** Data table with translated headers; returns the next y position. */
  function pdfTable(doc, y, headKeys, rows) {
    doc.autoTable(Object.assign({ startY: y, head: [headKeys.map(k => pdfSafe(k.startsWith("#") ? k : t(k)))], body: rows }, TABLE_STYLE));
    return doc.lastAutoTable.finalY + 6;
  }

  /** Finishes, downloads and logs the export. */
  function finish(doc, fileName, what) {
    pdfFooter(doc);
    download(doc.output("blob"), fileName);
    safe(() => logNow("export", "log.export", { f: "PDF", what }));
  }

  /* ---------------------------------------------------------
     Current table
     --------------------------------------------------------- */

  function exportPdf() {
    const spec = S.exportSpec;
    if (!spec) return;
    const cols = exportCols();
    const doc = newPdf(cols.length > 5);
    if (!doc) return;
    pdfHeader(doc, t(spec.title));
    doc.autoTable({
      startY: 36, head: [cols.map(c => pdfSafe(t(c.h)))], body: spec.rows.map(r => cols.map(c => pdfSafe(c.v(r)))),
      styles: { fontSize: 8, cellPadding: 2 }, headStyles: { fillColor: NAVY }, margin: { left: 12, right: 12, bottom: 16 }
    });
    if (spec.note) { // audit log: head hash
      doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.setTextColor(...INK);
      doc.text(doc.splitTextToSize(pdfSafe(spec.note), doc.internal.pageSize.getWidth() - 24), 12, doc.lastAutoTable.finalY + 8);
    }
    finish(doc, fileBase() + ".pdf", "@" + spec.title);
  }

  /* ---------------------------------------------------------
     Certificate of Release to Service
     --------------------------------------------------------- */

  function pdfCrs(id) {
    const doc = newPdf(false);
    if (!doc) return;
    const c = crsRecord(id);
    const width = doc.internal.pageSize.getWidth();
    pdfHeader(doc, t("crs.heading"));
    doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.setTextColor(...MUTED);
    doc.text(pdfSafe(t("crs.org", { a: c.approval })), 12, 37);
    const certifier = uname(c.certifier) + " (" + maskAuth(c.cert_auth) + (c.cert_cat ? ", " + t("col.cat") + " " + c.cert_cat : "") + ")";
    let y = pdfKv(doc, 42, [
      ["col.crs", c.id], ["col.wo", c.wo_id], ["col.aircraft", c.reg + " - " + c.model + " MSN " + c.msn], ["col.task", tx(c.title)],
      ["col.hours", fH(c.hours) + " h / " + fN(c.cycles) + " cyc"], ["col.date", fTs(c.at)], ["col.certifier", certifier]
    ]);
    // Release statement in a frame
    doc.setDrawColor(...NAVY); doc.setLineWidth(0.4); doc.rect(12, y, width - 24, 30);
    doc.setTextColor(...INK); doc.setFontSize(10.5);
    doc.text(doc.splitTextToSize(pdfSafe(t("crs.statement")), width - 32), 16, y + 8);
    // Simulated signature notice
    y += 40;
    doc.setFontSize(8.5); doc.setTextColor(180, 35, 24);
    doc.text(doc.splitTextToSize(pdfSafe(t("crs.simulated", { fp: String(c.fp).slice(0, 16) })), width - 24), 12, y);
    finish(doc, c.id + ".pdf", c.id);
  }

  /* ---------------------------------------------------------
     Record sheets
     --------------------------------------------------------- */

  function sheetAircraft(doc, reg) {
    const a = one("SELECT * FROM aircraft WHERE reg=?", [reg]);
    const s = acStatus(a);
    pdfHeader(doc, t("pdf.ac_title", { reg: a.reg }));
    let y = pdfKv(doc, 36, [
      ["col.model", a.model], ["col.msn", a.msn], ["col.base", a.base + " - " + tx(a.mission)], ["col.hours", fH(a.hours) + " h"],
      ["col.cycles", fN(a.cycles)], ["col.arc", fD(a.arc_expiry)], ["col.status", t("acst." + s.code)]
    ]);
    y = pdfTable(doc, y, ["col.task", "col.remaining", "col.status"], s.tasks.map(r => [tx(r.title), remText(r), t("st." + r.st)].map(pdfSafe)));
    pdfTable(doc, y, ["col.ad", "col.subject", "col.status"], s.ads.map(r => [r.ad_id, tx(r.title), t("ads." + r.status)].map(pdfSafe)));
    return reg;
  }

  /** "Name •••••• date" signature text of a task card. */
  const signedText = (uid, at) => (uid ? uname(uid) + " " + maskAuth(uauth(uid)) + " " + fTs(at) : "-");

  function sheetWorkOrder(doc, id) {
    const w = one("SELECT * FROM wo WHERE id=?", [id]);
    pdfHeader(doc, t("pdf.wo_title", { id }));
    const y = pdfKv(doc, 36, [
      ["col.aircraft", w.reg], ["col.kind", t("wok." + w.kind)], ["col.task", tx(w.title)], ["col.status", t("wost." + w.status)],
      ["col.opened", fD(w.opened)], ["col.assignee", w.assignee ? uname(w.assignee) : "-"], ["col.crs", w.crs_id || "-"]
    ]);
    const cards = q("SELECT * FROM card WHERE wo_id=? ORDER BY seq", [id]);
    pdfTable(doc, y, ["#", "col.task", "card.tech", "card.insp"],
      cards.map(c => [c.seq, tx(c.title), signedText(c.tech, c.tech_at), signedText(c.insp, c.insp_at)].map(pdfSafe)));
    return id;
  }

  function sheetPart(doc, id) {
    const p = one("SELECT * FROM part WHERE id=?", [id]);
    pdfHeader(doc, t("pdf.part_title", { pn: p.pn }));
    const limit = p.limit_h ? fN(p.limit_h) + " h" : p.limit_date ? fD(p.limit_date) : t("p.nolimit");
    const y = pdfKv(doc, 36, [
      ["col.descr", tx(p.descr)], ["col.snlot", p.sn || "Lot " + p.lot], ["col.form1", p.form1 || t("p.missing")], ["col.status", t("ps." + p.status)],
      ["col.location", p.reg || p.location || "-"], ["col.tsn", p.tsn !== null ? fH(p.tsn) + " h" : "-"], ["col.limit", limit]
    ]);
    const moves = q("SELECT * FROM part_move WHERE part_id=? ORDER BY at", [id])
      .map(m => [fTs(m.at), t("mv." + m.kind), tx(m.from_loc), tx(m.to_loc), uname(m.uid)].map(pdfSafe));
    const rows = moves.length ? moves : [[{ content: pdfSafe(t("p.no_moves")), colSpan: 5 }]];
    pdfTable(doc, y, ["col.date", "col.action", "p.from", "p.to", "col.user"], rows);
    return p.pn + "-" + (p.sn || p.lot);
  }

  const SHEETS = { ac: sheetAircraft, wo: sheetWorkOrder, part: sheetPart };

  /** Record sheet PDF; `kind` is "ac", "wo" or "part". */
  function pdfSheet(kind, id) {
    const doc = newPdf(false);
    if (!doc) return;
    const name = SHEETS[kind](doc, id);
    finish(doc, name + ".pdf", name);
  }

  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, {
    pdf: exportPdf,
    "pdf-crs": pdfCrs,
    "pdf-wo": id => pdfSheet("wo", id),
    "pdf-ac": id => pdfSheet("ac", id),
    "pdf-part": id => pdfSheet("part", id)
  });
})();
