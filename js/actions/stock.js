/**
 * @file Logistics actions: goods reception, Form 1 release from quarantine,
 * purchase orders.
 *
 * A part received without a valid EASA Form 1 goes to quarantine (Q-01) and
 * cannot be installed until a Form 1 is attached.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;
  const {
    esc, t, isoD, TODAY, one, run, transact, log, can, form1Check, nextId,
    val, field, select, formDlg, closeDlg, safe, deny
  } = MIS;

  const PN_PATTERN = /^[A-Z0-9][A-Z0-9-]{3,29}$/;
  const QUARANTINE = "Q-01";
  const RELEASE_LOCATION = "A-11";

  const input = (id, attrs) => `<input id="${id}" class="input${attrs.mono ? " mono" : ""}" ${attrs.html || ""}>`;

  /** Form 1 reference, issuing organisation and date fields (prefix "r" or "d"). */
  function form1Fields(prefix, required) {
    const req = required ? " required" : "";
    return field(prefix + "-f1", "col.form1", input(prefix + "-f1", { mono: true, html: `maxlength="30" placeholder="F1-ORG-26-00000"${req}` }), prefix === "d") +
      field(prefix + "-f1org", "col.form1_org", input(prefix + "-f1org", { mono: true, html: `maxlength="20" placeholder="FR.21G.0000"${req}` })) +
      field(prefix + "-f1date", "col.form1_date", input(prefix + "-f1date", { html: `type="date" max="${isoD(TODAY)}"${req}` }));
  }

  /* ---------------------------------------------------------
     Reception
     --------------------------------------------------------- */

  function receptionFields() {
    return field("r-pn", "col.pn", input("r-pn", { mono: true, html: `maxlength="30" required placeholder="145A00-0000-00"` })) +
      field("r-descr", "col.descr", input("r-descr", { html: `maxlength="80" required` })) +
      field("r-sn", "col.sn", input("r-sn", { mono: true, html: `maxlength="30"` })) +
      field("r-lot", "col.lot", input("r-lot", { mono: true, html: `maxlength="30"` })) +
      field("r-qty", "col.qty", input("r-qty", { html: `type="number" min="1" max="999" value="1"` })) +
      field("r-loc", "col.location", input("r-loc", { mono: true, html: `maxlength="10" value="A-10"` })) +
      form1Fields("r", false) +
      field("r-lim", "col.limit_h", input("r-lim", { html: `type="number" min="0" step="1"` })) +
      `<p class="small muted full">${esc(t("stock.receive_note"))}</p>`;
  }

  /** Reads the reception form. */
  function readReception() {
    return {
      pn: val("r-pn").toUpperCase(), descr: val("r-descr"), sn: val("r-sn").toUpperCase(), lot: val("r-lot").toUpperCase(),
      qty: parseInt(val("r-qty"), 10), loc: val("r-loc").toUpperCase(), lim: val("r-lim"),
      f1: val("r-f1").toUpperCase(), f1org: val("r-f1org").toUpperCase(), f1date: val("r-f1date")
    };
  }

  /** Returns a translated error, or null when the reception is valid. */
  function validateReception(r) {
    if (!PN_PATTERN.test(r.pn)) return t("err.pn");
    if (r.descr.length < 3) return t("err.descr");
    if (!r.sn && !r.lot) return t("err.snlot");
    if (r.sn && r.qty !== 1) return t("err.sn_qty");
    if (!(r.qty >= 1 && r.qty <= 999)) return t("err.qty");
    if (r.sn && one("SELECT 1 FROM part WHERE pn=? AND sn=?", [r.pn, r.sn])) return t("err.dup_sn");
    if (r.f1) return form1Check(r.f1, r.f1org, r.f1date);
    return null;
  }

  /** Inserts the part in stock (with Form 1) or in quarantine (without). */
  function recordReception(r) {
    const id = "PT-" + String(one("SELECT COUNT(*) n FROM part").n + 1).padStart(4, "0");
    const hasF1 = !!r.f1;
    const location = hasF1 ? r.loc : QUARANTINE;
    run("INSERT INTO part(id,pn,descr,sn,lot,qty,form1,form1_org,form1_date,status,location,tsn,limit_h,received) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      [id, r.pn, r.descr, r.sn || null, r.lot || null, r.qty, r.f1 || null, hasF1 ? r.f1org : null, hasF1 ? r.f1date : null,
        hasF1 ? "stock" : "quarantine", location, r.sn ? 0 : null, r.lim ? +r.lim : null, isoD(new Date())]);
    run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,uid) VALUES(?,?,?,?,?,?)",
      [id, new Date().toISOString(), hasF1 ? "receive" : "quarantine", "@loc.supplier", location, S.me.id]);
    log(hasF1 ? "part_receive" : "part_quarantine", hasF1 ? "log.part_receive" : "log.part_quarantine", { pn: r.pn, sn: r.sn || r.lot });
  }

  function receive() {
    if (!can("part.receive")) return deny("part.receive");
    formDlg(t("stock.receive"), receptionFields(), t("stock.receive_btn"), () => {
      const r = readReception();
      const err = validateReception(r);
      if (err) return err;
      safe(() => transact(() => recordReception(r)), r.f1 ? "toast.received" : "toast.quarantined");
      closeDlg();
    });
  }

  /* ---------------------------------------------------------
     Release from quarantine with a Form 1
     --------------------------------------------------------- */

  function recordRelease(id, f1, f1org, f1date) {
    const p = one("SELECT * FROM part WHERE id=?", [id]);
    run("UPDATE part SET form1=?, form1_org=?, form1_date=?, status='stock', location=? WHERE id=?", [f1, f1org, f1date, RELEASE_LOCATION, id]);
    run("INSERT INTO part_move(part_id,at,kind,from_loc,to_loc,uid) VALUES(?,?,?,?,?,?)", [id, new Date().toISOString(), "release", QUARANTINE, RELEASE_LOCATION, S.me.id]);
    run("UPDATE po SET status='received' WHERE pn=? AND status='awaiting_doc'", [p.pn]);
    log("part_release", "log.part_release", { pn: p.pn, sn: p.sn || p.lot, f1 });
  }

  function attachForm1(id) {
    if (!can("part.doc")) return deny("part.doc");
    const fields = form1Fields("d", true) + `<p class="small muted full">${esc(t("p.attach_note"))}</p>`;
    formDlg(t("p.attach"), fields, t("btn.save"), () => {
      const f1 = val("d-f1").toUpperCase(), f1org = val("d-f1org").toUpperCase(), f1date = val("d-f1date");
      const err = form1Check(f1, f1org, f1date);
      if (err) return err;
      S.current = null; // close the dialog: the toast confirms the release
      if (safe(() => transact(() => recordRelease(id, f1, f1org, f1date)), "toast.released")) closeDlg();
    });
  }

  /* ---------------------------------------------------------
     Purchase orders
     --------------------------------------------------------- */

  function newPo() {
    if (!can("po.create")) return deny("po.create");
    const fields = field("o-pn", "col.pn", input("o-pn", { mono: true, html: `maxlength="30"` })) +
      field("o-descr", "col.descr", input("o-descr", { html: `maxlength="80"` })) +
      field("o-qty", "col.qty", input("o-qty", { html: `type="number" min="1" max="999" value="1"` })) +
      field("o-sup", "col.supplier", select("o-sup", [["@sup.a", t("sup.a")], ["@sup.b", t("sup.b")]]));
    formDlg(t("po.new"), fields, t("po.create"), () => {
      const pn = val("o-pn").toUpperCase(), descr = val("o-descr"), qty = parseInt(val("o-qty"), 10);
      if (!PN_PATTERN.test(pn)) return t("err.pn");
      if (descr.length < 3) return t("err.descr");
      if (!(qty >= 1 && qty <= 999)) return t("err.qty");
      const id = nextId("po", "PO", 4);
      safe(() => transact(() => {
        run("INSERT INTO po(id,pn,descr,qty,supplier,status,ordered,uid) VALUES(?,?,?,?,?,?,?,?)", [id, pn, descr, qty, val("o-sup"), "ordered", isoD(new Date()), S.me.id]);
        log("po_create", "log.po_create", { id, pn });
      }), "toast.po", { id });
      closeDlg();
    });
  }

  /** Goods received: the order now waits for its Form 1. */
  function receivePo(id) {
    if (!can("po.receive")) return deny("po.receive");
    safe(() => transact(() => {
      run("UPDATE po SET status='awaiting_doc' WHERE id=?", [id]);
      log("po_receive", "log.po_receive", { id });
    }), "toast.po_received");
  }

  Object.assign(MIS.ACTIONS = MIS.ACTIONS || {}, {
    receive,
    "part-doc": attachForm1,
    "new-po": newPo,
    "po-receive": receivePo
  });
})();
