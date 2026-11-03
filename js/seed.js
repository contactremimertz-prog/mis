/**
 * @file SQLite schema and FICTITIOUS demo data.
 *
 * All registrations (F-XXXA to F-XXXM), serial numbers, part numbers, ADs and
 * Form 1 references are invented. Texts starting with "@" are translation
 * keys (see js/i18n), so the seeded data follows the selected language.
 *
 * Public API: window.MIS_SEED = { seed, SCHEMA }.
 */
(function () {
  "use strict";

  /**
   * Database schema. The `log` table is append-only: two triggers reject any
   * UPDATE or DELETE, so audit entries can only be added.
   */
  const SCHEMA = `
  CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
  CREATE TABLE users(id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL, auth TEXT NOT NULL UNIQUE, cat TEXT, active INTEGER NOT NULL DEFAULT 1);
  CREATE TABLE aircraft(reg TEXT PRIMARY KEY, model TEXT NOT NULL, msn TEXT NOT NULL UNIQUE, base TEXT, mission TEXT, hours REAL NOT NULL CHECK(hours>=0), cycles INTEGER NOT NULL CHECK(cycles>=0), arc_expiry TEXT, mfg_year INTEGER);
  CREATE TABLE mp_task(id TEXT PRIMARY KEY, model TEXT NOT NULL, code TEXT NOT NULL, title TEXT NOT NULL, interval_h REAL, interval_c INTEGER, interval_m INTEGER, ref TEXT);
  CREATE TABLE ac_task(id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT NOT NULL REFERENCES aircraft(reg), task_id TEXT NOT NULL REFERENCES mp_task(id), last_h REAL, last_c INTEGER, last_date TEXT);
  CREATE TABLE ad(id TEXT PRIMARY KEY, model TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL, interval_h REAL, effective TEXT, comply_days INTEGER);
  CREATE TABLE ac_ad(id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT NOT NULL REFERENCES aircraft(reg), ad_id TEXT NOT NULL REFERENCES ad(id), status TEXT NOT NULL, last_h REAL, last_date TEXT, wo_id TEXT);
  CREATE TABLE wo(id TEXT PRIMARY KEY, reg TEXT NOT NULL REFERENCES aircraft(reg), title TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, opened TEXT NOT NULL, planner TEXT, assignee TEXT, ac_task_id INTEGER, ac_ad_id INTEGER, mod_id TEXT, crs_id TEXT, closed_at TEXT);
  CREATE TABLE card(id INTEGER PRIMARY KEY AUTOINCREMENT, wo_id TEXT NOT NULL REFERENCES wo(id), seq INTEGER NOT NULL, title TEXT NOT NULL, tech TEXT, tech_at TEXT, insp TEXT, insp_at TEXT);
  CREATE TABLE crs(id TEXT PRIMARY KEY, wo_id TEXT NOT NULL UNIQUE REFERENCES wo(id), reg TEXT NOT NULL, certifier TEXT NOT NULL, cert_auth TEXT NOT NULL, cert_cat TEXT, approval TEXT NOT NULL, at TEXT NOT NULL, hours REAL, cycles INTEGER, fp TEXT);
  CREATE TABLE part(id TEXT PRIMARY KEY, pn TEXT NOT NULL, descr TEXT NOT NULL, sn TEXT, lot TEXT, qty INTEGER NOT NULL DEFAULT 1 CHECK(qty>=0), form1 TEXT UNIQUE, form1_org TEXT, form1_date TEXT, status TEXT NOT NULL, location TEXT, reg TEXT, wo_id TEXT, tsn REAL, limit_h REAL, limit_date TEXT, received TEXT);
  CREATE TABLE part_move(id INTEGER PRIMARY KEY AUTOINCREMENT, part_id TEXT NOT NULL REFERENCES part(id), at TEXT NOT NULL, kind TEXT NOT NULL, from_loc TEXT, to_loc TEXT, wo_id TEXT, uid TEXT);
  CREATE TABLE po(id TEXT PRIMARY KEY, pn TEXT NOT NULL, descr TEXT NOT NULL, qty INTEGER NOT NULL CHECK(qty>0), supplier TEXT NOT NULL, status TEXT NOT NULL, ordered TEXT NOT NULL, uid TEXT);
  CREATE TABLE modif(id TEXT PRIMARY KEY, reg TEXT, title TEXT NOT NULL, cls TEXT NOT NULL, approval TEXT, status TEXT NOT NULL, opened TEXT);
  CREATE TABLE nc(id TEXT PRIMARY KEY, level TEXT NOT NULL, reg TEXT, descr TEXT NOT NULL, source TEXT, opened TEXT NOT NULL, due TEXT NOT NULL, status TEXT NOT NULL, cause TEXT, action TEXT, closed_at TEXT, owner TEXT);
  CREATE TABLE audit(id TEXT PRIMARY KEY, title TEXT NOT NULL, scope TEXT NOT NULL, planned TEXT NOT NULL, auditor TEXT, status TEXT NOT NULL, findings INTEGER NOT NULL DEFAULT 0);
  CREATE TABLE doc(id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL, rev TEXT NOT NULL, rev_date TEXT, status TEXT NOT NULL, pending TEXT);
  CREATE TABLE log(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, uid TEXT, role TEXT, action TEXT NOT NULL, msg TEXT NOT NULL, params TEXT, prev TEXT NOT NULL, h TEXT NOT NULL);
  CREATE TRIGGER log_no_update BEFORE UPDATE ON log BEGIN SELECT RAISE(ABORT,'append-only'); END;
  CREATE TRIGGER log_no_delete BEFORE DELETE ON log BEGIN SELECT RAISE(ABORT,'append-only'); END;
  `;

  /** Returns ins(table, rows): bulk insert of plain objects (missing fields become NULL). */
  function makeInserter(db) {
    return (table, rows) => {
      if (!rows.length) return;
      const cols = Object.keys(rows[0]);
      const st = db.prepare(`INSERT INTO ${table}(${cols.join(",")}) VALUES(${cols.map(() => "?").join(",")})`);
      rows.forEach(r => st.run(cols.map(c => (r[c] === undefined ? null : r[c]))));
      st.free();
    };
  }

  /** Returns ts(dayOffset, hour): ISO timestamp `dayOffset` days from today at hour:15. */
  function makeTimestamp(today) {
    return (d, h) => {
      const x = new Date(today);
      x.setDate(x.getDate() + d);
      x.setHours(h, 15, 0, 0);
      return x.toISOString();
    };
  }

  /** Metadata (schema version, organisation approval) and the 9 demo profiles. */
  function seedReference(c) {
    const { ins, today } = c;
    ins("meta", [{ k: "schema", v: "3" }, { k: "approval", v: "FR.145.DEMO" }, { k: "seeded_at", v: today.toISOString() }]);

    ins("users", [
      { id: "u1", name: "Rémi Quentel", role: "QUALITY", auth: "QA-001", active: 1 },
      { id: "u2", name: "Sophie Durand", role: "CAMO", auth: "CAM-0310", active: 1 },
      { id: "u3", name: "Claire Morand", role: "CERT", auth: "CRS-0872", cat: "B1", active: 1 },
      { id: "u8", name: "Hugo Lefèvre", role: "CERT", auth: "CRS-0915", cat: "B2", active: 1 },
      { id: "u4", name: "Nadia Benali", role: "TECH", auth: "TEC-1140", active: 1 },
      { id: "u5", name: "Yanis Torres", role: "TECH", auth: "TEC-1187", active: 1 },
      { id: "u6", name: "Paul Garnier", role: "PLANNER", auth: "PLN-0207", active: 1 },
      { id: "u7", name: "Inès Roche", role: "STORE", auth: "MAG-0451", active: 1 },
      { id: "u9", name: "Alex Martin", role: "ADMIN", auth: "ADM-0001", active: 1 }
    ]);
  }

  /**
   * The 12 helicopters: [reg, model, msn, base, mission, hours, cycles, ARC days left, year].
   * @returns {Array} the fleet rows, reused by the programme and AD sections
   */
  function seedFleet(c) {
    const { ins, D } = c;
    const fleet = [
      ["F-XXXA", "H125", "9101", "Marignane", "aerial_work", 3421.6, 5120, 132, 2014],
      ["F-XXXB", "H125", "9134", "Annecy", "mountain", 1288.4, 2214, 260, 2019],
      ["F-XXXM", "H125", "9160", "Paris", "police", 4870.9, 7420, 88, 2012],
      ["F-XXXC", "H130", "8402", "Toulouse", "tourism", 2654.2, 3980, 201, 2016],
      ["F-XXXD", "H130", "8417", "Nice", "passenger", 4120.7, 6110, 175, 2013],
      ["F-XXXE", "H145", "20901", "Lyon", "hems", 2310.5, 3606, 18, 2018],
      ["F-XXXF", "H145", "20944", "Brest", "sar", 1544.2, 2390, 301, 2020],
      ["F-XXXG", "H145", "20987", "Grenoble", "hems", 812.0, 1290, 340, 2022],
      ["F-XXXH", "H160", "1101", "Le Bourget", "vip", 645.7, 880, 222, 2023],
      ["F-XXXJ", "H160", "1118", "Pau", "offshore", 1102.3, 1655, 156, 2022],
      ["F-XXXK", "H175", "5101", "Le Havre", "offshore", 3988.1, 4410, 64, 2017],
      ["F-XXXL", "H175", "5112", "Marignane", "offshore", 2210.6, 2480, 243, 2019]
    ];
    ins("aircraft", fleet.map(f => ({ reg: f[0], model: f[1], msn: f[2], base: f[3], mission: "@mission." + f[4], hours: f[5], cycles: f[6], arc_expiry: D(f[7]), mfg_year: f[8] })));
    return fleet;
  }

  /** Maintenance programme per model and last accomplishment per aircraft. */
  function seedProgramme(c, fleet) {
    const { ins, D } = c;
    // Maintenance programme templates (fictitious but representative intervals): [code, title, hours, cycles, months]
    const models = ["H125", "H130", "H145", "H160", "H175"];
    const mp = [];
    const tpl = [
      ["INSP-100", "@mp.insp100", 100, null, 12],
      ["INSP-600", "@mp.insp600", 600, null, 24],
      ["ENG-BOR", "@mp.boro", 500, null, null],
      ["MGB-OIL", "@mp.mgboil", 1200, null, 24],
      ["ELT-BAT", "@mp.elt", null, null, 12],
      ["LDG-CYC", "@mp.ldg", null, 3000, null]
    ];
    models.forEach(m => tpl.forEach(t => mp.push({ id: m + "-" + t[0], model: m, code: t[0], title: t[1], interval_h: t[2], interval_c: t[3], interval_m: t[4], ref: "MP-" + m + "-DEMO rev.4" })));
    ins("mp_task", mp);

    // Last accomplishment of each task: deterministic offsets, plus special cases used by the demo scenario
    const special = {
      "F-XXXD|INSP-100": { h: 104.2, d: -150 },      // overdue by hours
      "F-XXXB|INSP-100": { h: 88.4, d: -200 },       // due soon (11.6 h left)
      "F-XXXK|ELT-BAT": { d: -395 },                 // overdue by calendar
      "F-XXXM|LDG-CYC": { c: 2985 },                 // due soon by cycles
      "F-XXXE|INSP-600": { h: 590, d: -500 },        // due soon (10 h left)
      "F-XXXF|INSP-600": { h: 0, d: -9 }             // done recently (closed WO)
    };
    const act = [];
    let k = 7;
    fleet.forEach(f => {
      tpl.forEach(t => {
        k = (k * 37 + 11) % 97;
        const sp = special[f[0] + "|" + t[0]] || {};
        const frac = 0.15 + (k % 60) / 100; // 15 % to 74 % of the interval used
        const lh = t[2] ? Math.max(0, Math.round((f[5] - (sp.h !== undefined ? sp.h : t[2] * frac)) * 10) / 10) : Math.max(0, Math.round((f[5] - 40 * frac) * 10) / 10);
        const lc = t[3] ? Math.max(0, f[6] - (sp.c !== undefined ? sp.c : Math.round(t[3] * frac))) : Math.max(0, f[6] - Math.round(60 * frac));
        const ld = sp.d !== undefined ? D(sp.d) : D(-Math.round((t[4] ? t[4] * 30 : 365) * frac));
        act.push({ reg: f[0], task_id: f[1] + "-" + t[0], last_h: lh, last_c: lc, last_date: ld });
      });
    });
    ins("ac_task", act);
  }

  /** Airworthiness directives (one per model) and their status per aircraft. */
  function seedDirectives(c, fleet) {
    const { ins, D } = c;
    ins("ad", [
      { id: "AD-DEMO-2025-014", model: "H125", title: "@ad.t1", kind: "repeat", interval_h: 100, effective: D(-300), comply_days: 30 },
      { id: "AD-DEMO-2026-011", model: "H130", title: "@ad.t2", kind: "once", interval_h: null, effective: D(-20), comply_days: 60 },
      { id: "AD-DEMO-2026-003", model: "H145", title: "@ad.t3", kind: "once", interval_h: null, effective: D(-70), comply_days: 90 },
      { id: "AD-DEMO-2026-007", model: "H160", title: "@ad.t4", kind: "once", interval_h: null, effective: D(-40), comply_days: 45 },
      { id: "AD-DEMO-2025-021", model: "H175", title: "@ad.t5", kind: "repeat", interval_h: 300, effective: D(-400), comply_days: 30 }
    ]);
    const adRows = [];
    fleet.forEach(f => {
      const m = { H125: "AD-DEMO-2025-014", H130: "AD-DEMO-2026-011", H145: "AD-DEMO-2026-003", H160: "AD-DEMO-2026-007", H175: "AD-DEMO-2025-021" }[f[1]];
      let status = "applied", lh = Math.round((f[5] - 35) * 10) / 10, ld = D(-60);
      if (["F-XXXC", "F-XXXD", "F-XXXG", "F-XXXJ"].includes(f[0])) { status = "open"; lh = null; ld = null; }
      if (f[0] === "F-XXXK") { lh = Math.round((f[5] - 296) * 10) / 10; ld = D(-200); }
      adRows.push({ reg: f[0], ad_id: m, status, last_h: lh, last_date: ld, wo_id: null });
    });
    ins("ac_ad", adRows);
  }

  /** Work orders, task cards (signed or not) and the two existing CRS. */
  function seedWorkOrders(c) {
    const { db, ins, D, ts } = c;
    const tid = (reg, code) => db.exec(`SELECT a.id FROM ac_task a JOIN aircraft c ON c.reg=a.reg WHERE a.reg='${reg}' AND a.task_id=c.model||'-${code}'`)[0].values[0][0];
    const adid = reg => db.exec(`SELECT id FROM ac_ad WHERE reg='${reg}'`)[0].values[0][0];

    ins("wo", [
      { id: "WO-2026-0398", reg: "F-XXXH", title: "@mp.insp100", kind: "scheduled", status: "closed", opened: D(-22), planner: "u6", assignee: "u5", ac_task_id: tid("F-XXXH", "INSP-100"), crs_id: "CRS-2026-0081", closed_at: ts(-18, 16) },
      { id: "WO-2026-0412", reg: "F-XXXF", title: "@mp.insp600", kind: "scheduled", status: "closed", opened: D(-12), planner: "u6", assignee: "u4", ac_task_id: tid("F-XXXF", "INSP-600"), crs_id: "CRS-2026-0088", closed_at: ts(-9, 17) },
      { id: "WO-2026-0415", reg: "F-XXXB", title: "@mp.insp100", kind: "scheduled", status: "awaiting_crs", opened: D(-4), planner: "u6", assignee: "u5", ac_task_id: tid("F-XXXB", "INSP-100") },
      { id: "WO-2026-0418", reg: "F-XXXJ", title: "@wo.t.servo", kind: "defect", status: "in_progress", opened: D(-3), planner: "u6", assignee: "u4" },
      { id: "WO-2026-0421", reg: "F-XXXA", title: "@wo.t.led", kind: "mod", status: "open", opened: D(-2), planner: "u6", assignee: "u5", mod_id: "MOD-2026-004" },
      { id: "WO-2026-0423", reg: "F-XXXJ", title: "@ad.t4", kind: "ad", status: "open", opened: D(-2), planner: "u2", assignee: null, ac_ad_id: adid("F-XXXJ") },
      { id: "WO-2026-0425", reg: "F-XXXD", title: "@mp.insp100", kind: "scheduled", status: "open", opened: D(-1), planner: "u6", assignee: "u4", ac_task_id: tid("F-XXXD", "INSP-100") }
    ]);
    const cards = [];
    const std = ["@card.prep", "@card.perform", "@card.test", "@card.docs"];
    const addCards = (wo, list, tech, insp, nSigned, nInsp, day) => list.forEach((c, i) => cards.push({
      wo_id: wo, seq: i + 1, title: c,
      tech: i < nSigned ? tech : null, tech_at: i < nSigned ? ts(day, 9 + i) : null,
      insp: i < nInsp ? insp : null, insp_at: i < nInsp ? ts(day, 10 + i) : null
    }));
    addCards("WO-2026-0398", std, "u5", "u8", 4, 4, -18);
    addCards("WO-2026-0412", std, "u4", "u3", 4, 4, -9);
    addCards("WO-2026-0415", std, "u5", "u3", 4, 4, -1);
    addCards("WO-2026-0418", ["@card.prep", "@card.remove", "@card.install", "@card.test", "@card.docs"], "u4", "u8", 2, 1, -2);
    addCards("WO-2026-0421", ["@card.prep", "@card.install", "@card.test", "@card.docs"], "u5", "u3", 0, 0, 0);
    addCards("WO-2026-0423", ["@card.prep", "@card.perform", "@card.docs"], null, null, 0, 0, 0);
    addCards("WO-2026-0425", std, "u4", "u3", 0, 0, 0);
    ins("card", cards);
    ins("crs", [
      { id: "CRS-2026-0081", wo_id: "WO-2026-0398", reg: "F-XXXH", certifier: "u8", cert_auth: "CRS-0915", cert_cat: "B2", approval: "FR.145.DEMO", at: ts(-18, 16), hours: 640.2, cycles: 872, fp: "demo-0081" },
      { id: "CRS-2026-0088", wo_id: "WO-2026-0412", reg: "F-XXXF", certifier: "u3", cert_auth: "CRS-0872", cert_cat: "B1", approval: "FR.145.DEMO", at: ts(-9, 17), hours: 1544.2, cycles: 2390, fp: "demo-0088" }
    ]);

  }

  /** Parts (one in quarantine without Form 1), their movements and purchase orders. */
  function seedParts(c) {
    const { db, ins, D, ts } = c;
    ins("part", [
      { id: "PT-0001", pn: "130A11-0400-01", descr: "@part.mrb", sn: "MRB-24117", lot: null, qty: 1, form1: "F1-DEMO-26-11872", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXC", wo_id: null, tsn: 1820.4, limit_h: 20000, limit_date: null, received: D(-400) },
      { id: "PT-0002", pn: "145A33-1010-02", descr: "@part.tgb", sn: "TGB-08832", lot: null, qty: 1, form1: "F1-DEMO-25-90311", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXE", wo_id: null, tsn: 2310.5, limit_h: 4500, limit_date: null, received: D(-700) },
      { id: "PT-0003", pn: "145A41-2200-05", descr: "@part.starter", sn: "SG-55120", lot: null, qty: 1, form1: "F1-DEMO-26-12004", form1_org: "FR.21G.DEMO", form1_date: null, status: "stock", location: "A-03", reg: null, wo_id: null, tsn: 0, limit_h: null, limit_date: null, received: D(-30) },
      { id: "PT-0004", pn: "160A62-3100-11", descr: "@part.servo", sn: "SRV-30421", lot: null, qty: 1, form1: "F1-DEMO-26-12210", form1_org: "FR.21G.DEMO", form1_date: null, status: "stock", location: "A-07", reg: null, wo_id: null, tsn: 0, limit_h: null, limit_date: null, received: D(-6) },
      { id: "PT-0005", pn: "175A10-0501-07", descr: "@part.hub", sn: "MRH-11905", lot: null, qty: 1, form1: "F1-DEMO-24-40188", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXK", wo_id: null, tsn: 3988.1, limit_h: 4200, limit_date: null, received: D(-1500) },
      { id: "PT-0006", pn: "125A55-0012-01", descr: "@part.led", sn: "LGT-90017", lot: null, qty: 1, form1: null, form1_org: null, form1_date: null, status: "quarantine", location: "Q-01", reg: null, wo_id: null, tsn: 0, limit_h: null, limit_date: null, received: D(-5) },
      { id: "PT-0007", pn: "125A11-0700-04", descr: "@part.trb", sn: "TRB-40391", lot: null, qty: 1, form1: "F1-DEMO-26-10566", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXM", wo_id: null, tsn: 4870.9, limit_h: 5000, limit_date: null, received: D(-2000) },
      { id: "PT-0008", pn: "DEMO-ORK-145", descr: "@part.oring", sn: null, lot: "L-26-114", qty: 40, form1: "F1-DEMO-26-12100", form1_org: "FR.21G.DEMO", form1_date: null, status: "stock", location: "B-12", reg: null, wo_id: null, tsn: null, limit_h: null, limit_date: D(540), received: D(-40) },
      { id: "PT-0009", pn: "DEMO-OIL-T5", descr: "@part.oil", sn: null, lot: "L-26-090", qty: 24, form1: "C-OF-DEMO-26-0090", form1_org: "FR.21G.DEMO", form1_date: null, status: "stock", location: "C-02", reg: null, wo_id: null, tsn: null, limit_h: null, limit_date: D(20), received: D(-300) },
      { id: "PT-0010", pn: "160A21-1400-02", descr: "@part.mgb", sn: "MGB-61208", lot: null, qty: 1, form1: "F1-DEMO-25-70456", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXH", wo_id: null, tsn: 645.7, limit_h: 6000, limit_date: null, received: D(-900) },
      { id: "PT-0011", pn: "145A12-0100-03", descr: "@part.eltbat", sn: null, lot: "L-26-031", qty: 6, form1: "F1-DEMO-26-11950", form1_org: "FR.21G.DEMO", form1_date: null, status: "stock", location: "B-04", reg: null, wo_id: null, tsn: null, limit_h: null, limit_date: D(300), received: D(-60) },
      { id: "PT-0012", pn: "125A41-2200-02", descr: "@part.starter", sn: "SG-55188", lot: null, qty: 1, form1: "F1-DEMO-26-12301", form1_org: "FR.21G.DEMO", form1_date: null, status: "installed", location: null, reg: "F-XXXB", wo_id: "WO-2026-0415", tsn: 3.0, limit_h: null, limit_date: null, received: D(-15) }
    ]);
    db.run("UPDATE part SET form1_date=received WHERE form1 IS NOT NULL");
    ins("part_move", [
      { part_id: "PT-0012", at: ts(-15, 9), kind: "receive", from_loc: "@loc.supplier", to_loc: "A-05", wo_id: null, uid: "u7" },
      { part_id: "PT-0012", at: ts(-3, 10), kind: "issue", from_loc: "A-05", to_loc: "WO-2026-0415", wo_id: "WO-2026-0415", uid: "u7" },
      { part_id: "PT-0012", at: ts(-3, 14), kind: "install", from_loc: "WO-2026-0415", to_loc: "F-XXXB", wo_id: "WO-2026-0415", uid: "u5" },
      { part_id: "PT-0004", at: ts(-6, 11), kind: "receive", from_loc: "@loc.supplier", to_loc: "A-07", wo_id: null, uid: "u7" },
      { part_id: "PT-0006", at: ts(-5, 15), kind: "quarantine", from_loc: "@loc.supplier", to_loc: "Q-01", wo_id: null, uid: "u7" },
      { part_id: "PT-0003", at: ts(-30, 9), kind: "receive", from_loc: "@loc.supplier", to_loc: "A-03", wo_id: null, uid: "u7" }
    ]);
    ins("po", [
      { id: "PO-2026-0099", pn: "160A62-3100-11", descr: "@part.servo", qty: 1, supplier: "@sup.a", status: "received", ordered: D(-14), uid: "u7" },
      { id: "PO-2026-0101", pn: "DEMO-SEAL-160", descr: "@part.seal", qty: 2, supplier: "@sup.b", status: "ordered", ordered: D(-3), uid: "u6" },
      { id: "PO-2026-0102", pn: "125A55-0012-01", descr: "@part.led", qty: 1, supplier: "@sup.a", status: "awaiting_doc", ordered: D(-10), uid: "u7" }
    ]);
  }

  /** Part-21 modifications, findings, audits and controlled documents. */
  function seedQuality(c) {
    const { ins, D } = c;
    ins("modif", [
      { id: "MOD-2026-004", reg: "F-XXXA", title: "@mod.t1", cls: "minor", approval: "DOA-DEMO-21J-001", status: "in_work", opened: D(-25) },
      { id: "MOD-2026-002", reg: "F-XXXH", title: "@mod.t2", cls: "major", approval: "STC-DEMO-0001", status: "embodied", opened: D(-160) },
      { id: "MOD-2025-019", reg: null, title: "@mod.t3", cls: "minor", approval: "DOA-DEMO-21J-001", status: "approved", opened: D(-280) }
    ]);
    ins("nc", [
      { id: "NC-2026-031", level: "L1", reg: "F-XXXJ", descr: "@nc.d1", source: "@src.internal", opened: D(-3), due: D(0), status: "open", cause: null, action: null, owner: "u1" },
      { id: "NC-2026-029", level: "L2", reg: null, descr: "@nc.d2", source: "@src.audit", opened: D(-25), due: D(35), status: "open", cause: "@nc.c2", action: "@nc.a2", owner: "u1" },
      { id: "NC-2026-027", level: "L2", reg: "F-XXXA", descr: "@nc.d3", source: "@src.reception", opened: D(-5), due: D(25), status: "open", cause: null, action: null, owner: "u1" },
      { id: "NC-2026-022", level: "OBS", reg: null, descr: "@nc.d4", source: "@src.authority", opened: D(-50), due: D(-10), status: "closed", cause: "@nc.c4", action: "@nc.a4", closed_at: D(-12), owner: "u1" }
    ]);
    ins("audit", [
      { id: "AUD-2026-07", title: "@aud.t1", scope: "Part-145", planned: D(-60), auditor: "u1", status: "closed", findings: 2 },
      { id: "AUD-2026-11", title: "@aud.t2", scope: "@scope.store", planned: D(-1), auditor: "u1", status: "in_progress", findings: 1 },
      { id: "AUD-2026-12", title: "@aud.t3", scope: "Part-CAMO", planned: D(20), auditor: "u1", status: "planned", findings: 0 },
      { id: "AUD-2027-01", title: "@aud.t4", scope: "Part-21", planned: D(75), auditor: "u1", status: "planned", findings: 0 }
    ]);
    ins("doc", [
      { id: "DOC-AMM-H145", title: "@doc.amm145", kind: "@dk.data", rev: "R52", rev_date: D(-40), status: "current" },
      { id: "DOC-AMM-H160", title: "@doc.amm160", kind: "@dk.data", rev: "R18", rev_date: D(-12), status: "pending", pending: "R19" },
      { id: "DOC-MOE", title: "@doc.moe", kind: "@dk.org", rev: "E7 R3", rev_date: D(-1), status: "current" },
      { id: "DOC-CAE", title: "@doc.cae", kind: "@dk.org", rev: "E4 R1", rev_date: D(-90), status: "current" },
      { id: "DOC-MP-H130", title: "@doc.mp130", kind: "@dk.mp", rev: "R9", rev_date: D(-200), status: "current" },
      { id: "DOC-MEL-H175", title: "@doc.mel175", kind: "@dk.ops", rev: "R6", rev_date: D(-30), status: "current" },
      { id: "DOC-SB-H125", title: "@doc.sb125", kind: "@dk.data", rev: "R31", rev_date: D(-60), status: "pending", pending: "R32" },
      { id: "DOC-POE", title: "@doc.poe", kind: "@dk.org", rev: "E2 R0", rev_date: D(-120), status: "current" }
    ]);
  }

  /** Initial audit log entries (hash-chained through logFn). */
  function seedInitialLog(c, logFn) {
    const { ts } = c;
    [
      [-22, 8, "u6", "wo_create", "log.wo_create", { id: "WO-2026-0398", reg: "F-XXXH" }],
      [-18, 16, "u8", "crs_issue", "log.crs_issue", { id: "CRS-2026-0081", wo: "WO-2026-0398" }],
      [-9, 17, "u3", "crs_issue", "log.crs_issue", { id: "CRS-2026-0088", wo: "WO-2026-0412" }],
      [-6, 11, "u7", "part_receive", "log.part_receive", { pn: "160A62-3100-11", sn: "SRV-30421" }],
      [-5, 15, "u7", "part_quarantine", "log.part_quarantine", { pn: "125A55-0012-01", sn: "LGT-90017" }],
      [-3, 9, "u4", "nc_open", "log.nc_open", { id: "NC-2026-031", level: "L1" }],
      [-1, 14, "u5", "denied", "log.denied", { what: "@perm.crs.issue" }],
      [-1, 16, "u1", "doc_approve", "log.doc_approve", { id: "DOC-MOE", rev: "E7 R3" }]
    ].forEach(r => logFn(r[2], r[3], r[4], r[5], ts(r[0], r[1])));
  }

  /**
   * Creates the schema and the demo data in `db`.
   * @param {object} db sql.js database (empty)
   * @param {Date} today reference date: every date is relative to it
   * @param {Function} addDays (n) => ISO day n days from today
   * @param {Function} addMonths kept for API compatibility (unused here)
   * @param {Function} logFn (uid, action, msg, params, ts) => void, appends a chained log entry
   * @param {object} [opts] { skipLog: true } on an admin reset, when the existing log is kept
   */
  function seed(db, today, addDays, addMonths, logFn, opts) {
    db.exec(SCHEMA);
    const c = { db, today, ins: makeInserter(db), D: addDays, ts: makeTimestamp(today) };
    seedReference(c);
    const fleet = seedFleet(c);
    seedProgramme(c, fleet);
    seedDirectives(c, fleet);
    seedWorkOrders(c);
    seedParts(c);
    seedQuality(c);
    if (!(opts && opts.skipLog)) seedInitialLog(c, logFn);
  }

  window.MIS_SEED = { seed, SCHEMA };
})();
