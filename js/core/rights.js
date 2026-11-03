/**
 * @file Roles, screens and permissions.
 *
 * Access control is enforced in the browser only (demo limit, documented in
 * the README). Every refused action is written to the audit log by the caller.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const S = MIS.state;

  const ROLES = ["CAMO", "PLANNER", "TECH", "CERT", "STORE", "QUALITY", "ADMIN"];

  /** Actions each role may perform. */
  const PERMS = {
    CAMO: ["fleet.hours", "wo.create", "ad.manage", "mod.manage", "nc.create"],
    PLANNER: ["wo.create", "wo.assign", "fleet.hours", "po.create", "nc.create"],
    TECH: ["wo.start", "card.tech", "part.install", "nc.create"],
    CERT: ["card.insp", "crs.issue", "nc.create"],
    STORE: ["part.receive", "part.doc", "part.issue", "po.create", "po.receive", "nc.create"],
    QUALITY: ["nc.create", "nc.edit", "nc.close", "audit.manage", "doc.approve", "log.export"],
    ADMIN: ["user.manage", "db.reset", "log.export"]
  };

  const ALL = ROLES;
  const CAMO_SCREENS = ["CAMO", "PLANNER", "CERT", "QUALITY", "ADMIN"];
  const MRO_SCREENS = ["CAMO", "PLANNER", "TECH", "CERT", "QUALITY", "ADMIN"];

  /** Navigation groups and, for each screen, the roles allowed to see it. */
  const SCREENS = [
    { group: "nav.g.overview", items: [["dashboard", ALL], ["fleet", ALL]] },
    { group: "nav.g.camo", items: [["maintenance", CAMO_SCREENS], ["directives", CAMO_SCREENS]] },
    { group: "nav.g.mro", items: [["workorders", MRO_SCREENS], ["certificates", MRO_SCREENS]] },
    { group: "nav.g.p21", items: [["part21", ["CAMO", "CERT", "QUALITY", "ADMIN"]]] },
    { group: "nav.g.log", items: [["stock", ["PLANNER", "TECH", "STORE", "QUALITY", "ADMIN", "CAMO"]], ["orders", ["PLANNER", "STORE", "ADMIN"]]] },
    { group: "nav.g.quality", items: [["nc", ALL], ["audits", ["QUALITY", "CAMO", "ADMIN"]], ["documents", ALL]] },
    { group: "nav.g.admin", items: [["users", ["ADMIN", "QUALITY"]], ["auditlog", ["ADMIN", "QUALITY"]]] }
  ];

  /** Flat map screen id -> allowed roles. */
  const SCREEN_ROLES = { search: ALL };
  SCREENS.forEach(g => g.items.forEach(([id, roles]) => (SCREEN_ROLES[id] = roles)));

  /** True when the active, non-suspended profile holds permission `perm`. */
  const can = perm => !!S.me && !!S.me.active && PERMS[S.me.role].includes(perm);

  /** True when the active profile may open screen `screen`. */
  const canSee = screen => !!S.me && (SCREEN_ROLES[screen] || []).includes(S.me.role);

  /**
   * Masks the personal code (sign-in and signature secret). Only its hash is
   * stored; the mask has a fixed length and gives no hint about the code.
   */
  const maskAuth = auth => (auth ? "••••••" : "-");

  Object.assign(MIS, { ROLES, PERMS, SCREENS, can, canSee, maskAuth });
})();
