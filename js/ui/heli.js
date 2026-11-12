/**
 * @file Interactive 3D view of an aircraft, shown on the fleet screen.
 *
 * The aircraft is drawn with one of the four reference models in models/*.glb
 * (loaded with three.js and its GLTF loader, both vendored).
 *
 * Every part of the model can be clicked. Parts are grouped into zones by their
 * names or groups in the model (rotor, gearbox, engines, landing gear, tail,
 * airframe, doors and glazing, lights and antennas, interior).
 *
 * Two sources of maintenance status:
 *  - the maintenance programme tasks of the database, for the rotor, gearbox,
 *    engine and landing-gear zones (codes listed in ZONES);
 *  - simulated part revisions: at least 30 parts per aircraft, generated from
 *    the registration so the same aircraft always shows the same values. They
 *    are labelled as a simulation and have no airworthiness value.
 * Overdue -> high urgency (red), due soon -> medium (orange). Only urgent parts
 * are recoloured; the other parts keep the model's own look.
 * Clicking a part or a zone moves it out of the airframe and brings the camera
 * close to it. Zones and urgent parts are also listed as buttons in the page.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const { esc, t, tx, remText } = MIS;

  /** Zones: maintenance programme task codes that feed them (database), and how parts are matched. */
  const ZONES = [
    { id: "rotor", codes: ["INSP-600"] },
    { id: "bte", codes: ["MGB-OIL"] },
    { id: "turb", codes: ["ENG-BOR"] },
    { id: "train", codes: ["LDG-CYC"] },
    { id: "queue", codes: [] },
    { id: "cellule", codes: [] },
    { id: "portes", codes: [] },
    { id: "feux", codes: [] },
    { id: "interieur", codes: [] }
  ];
  const CORE = ["rotor", "bte", "turb", "train"];

  /** Model groups -> zone. Parts outside these groups (markings) have no zone. */
  const GROUP_ZONE = {
    grp_rotor: "rotor", grp_prop: "turb", grp_train: "train", grp_queue: "queue",
    grp_cellule: "cellule", grp_portes: "portes", grp_feux: "feux", grp_interieur: "interieur"
  };

  /** Reference models shipped in models/. */
  const MODELS = [
    { id: "h135", label: "H135", file: "models/h135.glb" },
    { id: "h145", label: "H145", file: "models/h145.glb" },
    { id: "nh90", label: "NH90", file: "models/nh90.glb" },
    { id: "super-puma", label: "Super Puma", file: "models/super-puma.glb" }
  ];

  /** Simulated revision types: matched on the part name, with their interval in flight hours. */
  const REVS = [
    { id: "gearbox", re: /gearbox/i, h: 100 },
    { id: "dyn", re: /pale|blade|rotor_head|moyeu|mast|swashplate|servo|fenestron_rotor|tail_rotor/i, h: 100 },
    { id: "engine", re: /engine|intake|exhaust|entree|echappement|naca/i, h: 300 },
    { id: "gear", re: /skid|gear|wheel|cross_tube|step|marchepied/i, h: 300 },
    { id: "door", re: /door|hatch|ramp|clamshell/i, h: 300 },
    { id: "glass", re: /window|windshield|skylight/i, h: 600 },
    { id: "light", re: /light|feu|beacon|collision/i, h: 100 },
    { id: "avionics", re: /antenna|antenne|gps|pitot|static|statique|sensor|radome|hoist|hook/i, h: 300 },
    { id: "cabin", re: /seat|floor|plancher|panel|planche|console|commande/i, h: 600 },
    { id: "struct", re: /./, h: 600 }
  ];

  /** Minimum number of parts with a simulated revision on each aircraft. */
  const MIN_REVS = 30;

  /** Colour of each urgency level, in the 3D view (hex) and in the page. */
  const LEVEL = {
    crit: { hex: 0xb42318, css: "var(--crit)", key: "heli.lvl_crit" },
    warn: { hex: 0xc2410c, css: "var(--warn)", key: "heli.lvl_warn" },
    ok: { hex: 0x64748b, css: "var(--muted)", key: "heli.lvl_ok" },
    none: { hex: 0x475569, css: "var(--muted)", key: "heli.lvl_none" }
  };
  const RANK = { none: 0, ok: 1, warn: 2, crit: 3 };
  const worst = levels => levels.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "none");
  const levelOf = st => (st === "overdue" ? "crit" : st === "soon" ? "warn" : "ok");

  /** Largest dimension of a model in scene units, and distance a selected part moves out. */
  const SIZE = 6;
  const EXPLODE = 1.3;

  /** Data of the block being rendered, read by mount() once the page is in the DOM. */
  let pending = null;
  /** Running view, released by dispose() before the next render. */
  let live = null;

  /** Model used when the user has not picked one: the closest reference to the aircraft type. */
  function modelFor(aircraftModel) {
    const m = String(aircraftModel || "");
    if (/145/.test(m)) return "h145";
    if (/125|130|135/.test(m)) return "h135";
    return "h145";
  }

  /** Maintenance programme tasks of each core zone, with their urgency (database). */
  function zoneStates(a) {
    const out = {};
    ZONES.forEach(z => {
      const rows = a.s.tasks.filter(x => z.codes.includes(x.code));
      out[z.id] = { id: z.id, k: rows.length ? worst(rows.map(x => levelOf(x.st))) : "none", rows };
    });
    return out;
  }

  /** Deterministic random numbers from a text seed (same aircraft -> same simulation). */
  function seeded(text) {
    let h = 2166136261;
    for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
    let s = h >>> 0;
    return () => {
      s = (s + 0x6d2b79f5) | 0;
      let r = Math.imul(s ^ (s >>> 15), 1 | s);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  /** Readable part name from the model's node name ("cockpit_door_rh" -> "Cockpit door RH"). */
  function partLabel(name) {
    const s = String(name || "").replace(/_/g, " ").replace(/\b(rh|lh)\b/gi, w => w.toUpperCase()).trim();
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : "?";
  }

  /** Zone of a model part, from its own name or the name of its groups; null if none. */
  function zoneOf(obj) {
    if (/gearbox/i.test(obj.name)) return "bte";
    for (let o = obj; o; o = o.parent) {
      if (GROUP_ZONE[o.name]) return GROUP_ZONE[o.name];
    }
    return null;
  }

  /**
   * Parts of a loaded model, each with its zone and, for at least MIN_REVS of
   * them, a simulated revision (type, interval, remaining hours, status).
   */
  function partsOf(src, reg, modelId) {
    // A part is a node of the model: a node with several materials is loaded as a group of meshes.
    const parts = [];
    const byObj = new Map();
    src.traverse(m => {
      if (!m.isMesh) return;
      const multi = m.parent && m.parent.type === "Group" && m.name.indexOf(m.parent.name + "_mesh") === 0;
      const obj = multi ? m.parent : m;
      let p = byObj.get(obj);
      if (!p) {
        p = { idx: parts.length, obj, meshes: [], name: obj.name, label: partLabel(obj.name), zone: zoneOf(obj), rev: null };
        byObj.set(obj, p);
        parts.push(p);
      }
      p.meshes.push(m);
    });
    const rand = seeded(reg + "|" + modelId);
    const pool = parts.filter(p => p.zone);
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    const n = Math.min(pool.length, Math.max(MIN_REVS, Math.round(pool.length * 0.5)));
    pool.slice(0, n).forEach(p => {
      const type = REVS.find(r => r.re.test(p.name));
      const roll = rand();
      const st = roll < 0.12 ? "overdue" : roll < 0.35 ? "soon" : "ok";
      const rem = st === "overdue" ? -(1 + Math.floor(rand() * 25))
        : st === "soon" ? 1 + Math.floor(rand() * 24)
          : 25 + Math.floor(rand() * (type.h - 25));
      p.rev = { type: type.id, h: type.h, rem, st };
    });
    return parts;
  }

  /** Zone summaries: database tasks, parts, tracked parts and overall urgency. */
  function zonesOf(parts, states) {
    const out = {};
    ZONES.forEach(z => {
      const zp = parts.filter(p => p.zone === z.id);
      const rows = states[z.id] ? states[z.id].rows : [];
      const tracked = zp.filter(p => p.rev);
      const k = worst(rows.map(x => levelOf(x.st)).concat(tracked.map(p => levelOf(p.rev.st))));
      out[z.id] = { id: z.id, rows, parts: zp, tracked, k };
    });
    return out;
  }

  /** Urgency of a part: its own simulated revision, and the database task of its core zone. */
  function partLevel(p, zones) {
    const own = p.rev ? levelOf(p.rev.st) : "none";
    const core = p.zone && CORE.includes(p.zone) && zones[p.zone].rows.length ? worst(zones[p.zone].rows.map(x => levelOf(x.st))) : "none";
    return worst([own, core]);
  }

  /** Remaining time of a simulated revision, as text. */
  const revText = rev => (rev.rem < 0 ? t("heli.rev_over", { n: -rev.rem }) : t("heli.rev_rem", { n: rev.rem }));

  /** Button for a part in a list: name, and remaining time coloured by urgency. */
  function partButton(p) {
    const k = p.rev ? levelOf(p.rev.st) : "none";
    const right = p.rev ? revText(p.rev) : t("heli.lvl_none");
    return `<li><button type="button" class="heli-part" data-part="${p.idx}"><span>${esc(p.label)}</span>` +
      `<span class="heli-lvl" style="color:${LEVEL[k].css}">${esc(right)}</span></button></li>`;
  }

  /** Parts sorted by urgency, then by remaining hours. */
  const byUrgency = list => list.slice().sort((a, b) => (RANK[levelOf(b.rev.st)] - RANK[levelOf(a.rev.st)]) || (a.rev.rem - b.rev.rem));

  /** Zone buttons of the side list. Before the model is loaded, only the database zones are known. */
  function zoneListHtml(zones) {
    return ZONES.filter(z => zones[z.id] && (zones[z.id].parts || CORE.includes(z.id))).map(z => {
      const s = zones[z.id];
      const count = s.tracked ? ` <span class="small muted">(${s.tracked.length})</span>` : "";
      return `<li><button type="button" class="heli-zone" data-zone="${z.id}" aria-pressed="false">` +
        `<span>${esc(t("heli.zone." + z.id))}${count}</span><span class="heli-lvl" style="color:${LEVEL[s.k].css}">${esc(t(LEVEL[s.k].key))}</span></button></li>`;
    }).join("");
  }

  /** Overview (nothing selected): counts and the urgent parts. */
  function overviewHtml(parts) {
    if (!parts) return `<p class="muted">${esc(t("heli.pick"))}</p>`;
    const tracked = parts.filter(p => p.rev);
    const crit = tracked.filter(p => p.rev.st === "overdue").length;
    const warn = tracked.filter(p => p.rev.st === "soon").length;
    const urgent = byUrgency(tracked.filter(p => p.rev.st !== "ok")).slice(0, 12);
    return `<p>${esc(t("heli.summary", { n: tracked.length, c: crit, w: warn }))}</p>` +
      `<h4>${esc(t("heli.urgent"))}</h4>` +
      (urgent.length ? `<ul class="heli-parts">${urgent.map(partButton).join("")}</ul>` : `<p class="muted">${esc(t("heli.no_urgent"))}</p>`) +
      `<p class="small muted">${esc(t("heli.pick"))}</p>`;
  }

  /** Details of a zone: urgency, database tasks and tracked parts. */
  function zoneHtml(z) {
    const tasks = z.rows.length
      ? `<h4>${esc(t("heli.zone_tasks"))}</h4><ul>` + z.rows.map(x => `<li>${esc(tx(x.title))} · ${esc(remText(x))}</li>`).join("") + "</ul>"
      : "";
    const tracked = z.tracked ? byUrgency(z.tracked) : [];
    const parts = tracked.length
      ? `<h4>${esc(t("heli.zone_parts"))}</h4><ul class="heli-parts">${tracked.map(partButton).join("")}</ul>`
      : (z.rows.length ? "" : `<p class="muted">${esc(t("heli.none"))}</p>`);
    return `<h3>${esc(t("heli.zone." + z.id))}</h3><p style="color:${LEVEL[z.k].css};font-weight:600">${esc(t(LEVEL[z.k].key))}</p>${tasks}${parts}`;
  }

  /** Details of a part: zone, simulated revision if any. */
  function partHtml(p, zones) {
    const zone = p.zone ? `<p class="small muted">${esc(t("heli.zone_label", { z: t("heli.zone." + p.zone) }))}</p>` : "";
    const k = partLevel(p, zones);
    let body;
    if (p.rev) {
      body = `<p style="color:${LEVEL[levelOf(p.rev.st)].css};font-weight:600">${esc(t(LEVEL[levelOf(p.rev.st)].key))}</p>` +
        `<ul><li>${esc(t("heli.rev." + p.rev.type))}</li><li>${esc(t("heli.rev_every", { n: p.rev.h }))}</li><li>${esc(revText(p.rev))}</li></ul>` +
        `<p class="small muted">${esc(t("heli.sim"))}</p>`;
    } else {
      body = `<p class="muted">${esc(t("heli.part_none"))}</p>`;
    }
    const zoneTask = !p.rev && k !== "none"
      ? `<p style="color:${LEVEL[k].css}">${esc(t(LEVEL[k].key))} · ${esc(t("heli.zone_tasks"))}</p>` : "";
    return `<h3>${esc(p.label)}</h3>${zone}${body}${zoneTask}`;
  }

  /** Page block: aircraft and model choosers, 3D canvas, details and zone list. */
  function heliBlock(a, regs) {
    const states = zoneStates(a);
    const F = MIS.state.filters;
    const modelId = MODELS.some(m => m.id === F.heliModel) ? F.heliModel : modelFor(a.model);
    pending = { reg: a.reg, states, model: modelId };
    const chooser = MIS.chips("heli", regs, a.reg, v => v);
    const modelChooser = MIS.chips("heliModel", MODELS.map(m => m.id), modelId, id => MODELS.find(m => m.id === id).label);
    const legend = ["crit", "warn"].map(k =>
      `<span class="heli-key"><i style="background:${LEVEL[k].css}"></i>${esc(t(LEVEL[k].key))}</span>`).join("");
    return `<section class="card heli" aria-labelledby="heli-title">
      <div class="card-head"><h2 id="heli-title">${esc(t("heli.title"))} · ${esc(a.reg)} · ${esc(a.model)}</h2></div>
      ${chooser}
      <div class="heli-models"><span class="small muted">${esc(t("heli.model"))}</span>${modelChooser}</div>
      <div class="heli-body">
        <div class="heli-stage">
          <div class="heli-view" id="heli-view" role="application" aria-label="${esc(t("heli.aria", { reg: a.reg }))}"></div>
          <p class="heli-hint small muted">${esc(t("heli.hint"))}</p>
        </div>
        <div class="heli-side">
          <div class="heli-legend">${legend}</div>
          <div id="heli-info" class="heli-info" aria-live="polite"></div>
          <ul id="heli-zones" class="heli-list" aria-label="${esc(t("heli.zones"))}">${zoneListHtml(states)}</ul>
          <p class="small muted">${esc(t("heli.sim"))} ${esc(t("heli.demo"))}</p>
        </div>
      </div>
    </section>`;
  }

  /** Releases the WebGL context, the model, the animation frame and the listeners of the running view. */
  function dispose() {
    if (!live) return;
    cancelAnimationFrame(live.raf);
    live.ro && live.ro.disconnect();
    live.listeners.forEach(([target, type, fn, opts]) => target.removeEventListener(type, fn, opts));
    if (live.scene) {
      live.scene.traverse(o => {
        if (o.geometry) o.geometry.dispose();
        if (o.material) [].concat(o.material).forEach(m => m.dispose());
      });
    }
    if (live.renderer) {
      live.renderer.dispose();
      live.renderer.forceContextLoss && live.renderer.forceContextLoss();
    }
    live = null;
  }

  /** Parses a model file. Each mount parses its own copy, so parts can move without affecting another view. */
  function loadModel(file) {
    return new Promise((resolve, reject) => {
      new window.THREE.GLTFLoader().load(file, resolve, undefined, reject);
    });
  }

  /** Builds the view for the pending block. Called after each render. */
  function mount() {
    dispose();
    const host = document.getElementById("heli-view");
    if (!host || !pending) { pending = null; return; }
    const data = pending;
    pending = null;
    const THREE = window.THREE;
    const token = {};
    const listeners = [];
    live = { token, listeners, raf: 0 };

    const info = document.getElementById("heli-info");
    const zoneList = document.getElementById("heli-zones");
    const body = host.parentNode.parentNode;
    let parts = null;
    let meshes = [];
    let zones = data.states;
    let sel = null;

    let renderer = null;
    try {
      renderer = THREE && new THREE.WebGLRenderer({ antialias: true });
    } catch (e) {
      renderer = null;
    }
    const status = document.createElement("p");
    status.className = "heli-status muted";
    status.textContent = renderer ? t("heli.loading") : t("heli.nogl");
    host.appendChild(status);

    // 3D scene (only when WebGL is available)
    let scene = null, camera = null, heli = null;
    const HOME = THREE ? new THREE.Vector3(6.2, 2.4, 8) : null;
    const CENTER = THREE ? new THREE.Vector3(0, 0, 0) : null;
    let camGoal = HOME && HOME.clone();
    let targetGoal = CENTER && CENTER.clone();
    const zoneView = {};
    if (renderer) {
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      host.insertBefore(renderer.domElement, status);
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x1e2630);
      camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      camera.position.copy(HOME);
      scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
      const sun = new THREE.DirectionalLight(0xffffff, 1.1);
      sun.position.set(4, 8, 5);
      scene.add(sun);
      const grid = new THREE.GridHelper(14, 14, 0x334155, 0x273244);
      grid.position.y = -3.2;
      scene.add(grid);
      heli = new THREE.Group();
      scene.add(heli);
      live.renderer = renderer;
      live.scene = scene;
    }

    /** Updates the side panel and the camera for the current selection. */
    function select(next) {
      sel = next;
      if (!sel) info.innerHTML = overviewHtml(parts);
      else if (sel.kind === "zone") info.innerHTML = zoneHtml(zones[sel.id]);
      else info.innerHTML = partHtml(parts[sel.id], zones);
      zoneList.querySelectorAll(".heli-zone").forEach(b =>
        b.setAttribute("aria-pressed", String(!!sel && sel.kind === "zone" && b.dataset.zone === sel.id)));
      if (!renderer) return;
      if (!sel) {
        camGoal = HOME.clone();
        targetGoal = CENTER.clone();
        return;
      }
      let center, span;
      if (sel.kind === "zone") {
        const v = zoneView[sel.id];
        if (!v) return;
        center = v.center; span = v.span;
      } else {
        const box = new THREE.Box3().setFromObject(parts[sel.id].obj);
        center = box.getCenter(new THREE.Vector3());
        span = Math.max(1.2, box.getSize(new THREE.Vector3()).length() * 1.5);
      }
      targetGoal = center.clone();
      camGoal = center.clone().add(new THREE.Vector3(0.9, 0.4, 1.2).multiplyScalar(span));
    }

    /** Model loaded: parts, simulated revisions, zones, then the 3D placement if any. */
    function onModel(gltf) {
      const src = gltf.scene;
      parts = partsOf(src, data.reg, data.model);
      meshes = [].concat(...parts.map(p => p.meshes));
      zones = zonesOf(parts, data.states);
      zoneList.innerHTML = zoneListHtml(zones);
      if (renderer) {
        place(src);
        status.remove();
      }
      select(null);
    }

    /** Scales and centres the model, recolours urgent parts and prepares the explode moves. */
    function place(src) {
      const box = new THREE.Box3().setFromObject(src);
      const size = box.getSize(new THREE.Vector3());
      const k = SIZE / Math.max(size.x, size.y, size.z, 1e-6);
      src.scale.setScalar(k);
      src.position.copy(box.getCenter(new THREE.Vector3()).multiplyScalar(-k));
      heli.add(src);
      src.updateMatrixWorld(true);
      const unions = {};
      parts.forEach(p => {
        const m = p.obj;
        const lvl = partLevel(p, zones);
        p.meshes.forEach(mesh => {
          mesh.userData.part = p.idx;
          if (lvl !== "crit" && lvl !== "warn") return;
          mesh.material = Array.isArray(mesh.material) ? mesh.material.map(x => x.clone()) : mesh.material.clone();
          [].concat(mesh.material).forEach(x => x.color && x.color.setHex(LEVEL[lvl].hex));
        });
        const wc = new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());
        const off = wc.clone();
        if (off.lengthSq() < 1e-6) off.set(0, 1, 0);
        off.y += 0.35;
        off.normalize();
        const a0 = m.parent.worldToLocal(wc.clone());
        const a1 = m.parent.worldToLocal(wc.clone().add(off));
        m.userData.home = m.position.clone();
        m.userData.dir = a1.sub(a0).normalize();
        if (p.zone) (unions[p.zone] = unions[p.zone] || new THREE.Box3()).expandByObject(m);
      });
      Object.keys(unions).forEach(id => {
        zoneView[id] = { center: unions[id].getCenter(new THREE.Vector3()), span: Math.max(1.5, unions[id].getSize(new THREE.Vector3()).length()) };
      });
    }

    // Clicks on the side panel: zones and parts
    const onSide = e => {
      const z = e.target.closest(".heli-zone");
      if (z) { select(sel && sel.kind === "zone" && sel.id === z.dataset.zone ? null : { kind: "zone", id: z.dataset.zone }); return; }
      const p = e.target.closest("[data-part]");
      if (p && parts) select({ kind: "part", id: Number(p.dataset.part) });
    };
    listeners.push([body, "click", onSide]);
    body.addEventListener("click", onSide);

    if (renderer) {
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      const lookAt = CENTER.clone();
      let dragging = false, lastX = 0, moved = 0;
      const canvas = renderer.domElement;
      const onDown = e => { dragging = true; lastX = e.clientX; moved = 0; };
      const onUp = e => {
        if (!dragging) return;
        dragging = false;
        if (moved >= 5 || !parts) return;
        const rect = canvas.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const hit = raycaster.intersectObjects(meshes, false)[0];
        if (!hit) { select(null); return; }
        const idx = hit.object.userData.part;
        select(sel && sel.kind === "part" && sel.id === idx ? null : { kind: "part", id: idx });
      };
      const onMove = e => {
        if (!dragging) return;
        const dx = e.clientX - lastX;
        moved += Math.abs(dx);
        lastX = e.clientX;
        heli.rotation.y += dx * 0.01;
      };
      const onWheel = e => {
        e.preventDefault();
        const offset = camGoal.clone().sub(targetGoal);
        const dist = THREE.MathUtils.clamp(offset.length() * (1 + Math.sign(e.deltaY) * 0.08), 1.2, 22);
        camGoal = targetGoal.clone().add(offset.setLength(dist));
      };
      const resize = () => {
        const w = host.clientWidth || 1;
        const h = host.clientHeight || 1;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      };
      [[canvas, "pointerdown", onDown], [window, "pointerup", onUp], [window, "pointermove", onMove],
        [canvas, "wheel", onWheel, { passive: false }], [window, "resize", resize]].forEach(l => {
        listeners.push(l);
        l[0].addEventListener(l[1], l[2], l[3]);
      });
      live.ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
      if (live.ro) live.ro.observe(host);
      resize();

      const loop = () => {
        live.raf = requestAnimationFrame(loop);
        if (!dragging) heli.rotation.y += 0.002;
        if (parts) {
          parts.forEach(p => {
            const m = p.obj;
            if (!m.userData.home) return;
            const out = sel && ((sel.kind === "zone" && p.zone === sel.id) || (sel.kind === "part" && p.idx === sel.id));
            const goal = out ? m.userData.home.clone().add(m.userData.dir.clone().multiplyScalar(EXPLODE)) : m.userData.home;
            m.position.lerp(goal, 0.12);
          });
        }
        camera.position.lerp(camGoal, 0.08);
        lookAt.lerp(targetGoal, 0.08);
        camera.lookAt(lookAt);
        renderer.render(scene, camera);
      };
      loop();
    }

    select(null);
    if (!THREE || !THREE.GLTFLoader) return;
    const file = (MODELS.find(m => m.id === data.model) || MODELS[1]).file;
    loadModel(file).then(gltf => {
      if (!live || live.token !== token) return;
      onModel(gltf);
    }).catch(() => {
      if (!live || live.token !== token) return;
      status.textContent = t("heli.model_error");
    });
  }

  MIS.heliBlock = heliBlock;
  MIS.heliMount = mount;
  MIS.heliParts = partsOf;
})();
