/**
 * @file Interactive 3D view of an aircraft, shown on the fleet screen.
 *
 * The aircraft is drawn with one of the four reference models in models/*.glb
 * (loaded with three.js and its GLTF loader, both vendored). Parts are grouped
 * into four maintenance zones by their names in the model:
 *   rotor  : parts of the main rotor group (grp_rotor)
 *   bte    : gearbox parts (name contains "gearbox")
 *   turb   : engine group (grp_prop)
 *   train  : landing gear group (grp_train)
 * Each zone is coloured by the most urgent maintenance task that feeds it:
 *   overdue -> high urgency (red), due soon -> medium (orange), no task -> neutral, otherwise grey.
 * Clicking a zone moves its parts out of the airframe and brings the camera close.
 * Each zone is also a button in the page, so the information stays available
 * without WebGL. The models are reference shapes, not the configuration of the real aircraft.
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const { esc, t, tx, remText } = MIS;

  /** Zones of the airframe: the maintenance task codes that feed each one. */
  const ZONES = [
    { id: "rotor", codes: ["INSP-600"] },
    { id: "bte", codes: ["MGB-OIL"] },
    { id: "turb", codes: ["ENG-BOR"] },
    { id: "train", codes: ["LDG-CYC"] }
  ];

  /** Reference models shipped in models/. */
  const MODELS = [
    { id: "h135", label: "H135", file: "models/h135.glb" },
    { id: "h145", label: "H145", file: "models/h145.glb" },
    { id: "nh90", label: "NH90", file: "models/nh90.glb" },
    { id: "super-puma", label: "Super Puma", file: "models/super-puma.glb" }
  ];

  /** Colour of each urgency level, in the 3D view (hex) and in the page. */
  const LEVEL = {
    crit: { hex: 0xb42318, css: "var(--crit)", key: "heli.lvl_crit" },
    warn: { hex: 0xc2410c, css: "var(--warn)", key: "heli.lvl_warn" },
    ok: { hex: 0x64748b, css: "var(--muted)", key: "heli.lvl_ok" },
    none: { hex: 0x475569, css: "var(--muted)", key: "heli.lvl_none" }
  };

  /** Largest dimension of a model in scene units, and distance a selected zone moves out. */
  const SIZE = 6;
  const EXPLODE = 1.3;

  /** Data of the block being rendered, read by mount() once the page is in the DOM. */
  let pending = null;
  /** Running 3D view, released by dispose() before the next render. */
  let live = null;

  /** Model used when the user has not picked one: the closest reference to the aircraft type. */
  function modelFor(aircraftModel) {
    const m = String(aircraftModel || "");
    if (/145/.test(m)) return "h145";
    if (/125|130|135/.test(m)) return "h135";
    return "h145";
  }

  /** Urgency of each zone of an aircraft, from its maintenance tasks (a.s.tasks). */
  function zoneStates(a) {
    const out = {};
    ZONES.forEach(z => {
      const rows = a.s.tasks.filter(x => z.codes.includes(x.code));
      const k = !rows.length ? "none" : rows.some(x => x.st === "overdue") ? "crit" : rows.some(x => x.st === "soon") ? "warn" : "ok";
      out[z.id] = { k, rows };
    });
    return out;
  }

  /** Page block: aircraft and model choosers, 3D canvas, zone details and a text list of the zones. */
  function heliBlock(a, regs) {
    const states = zoneStates(a);
    const F = MIS.state.filters;
    const modelId = MODELS.some(m => m.id === F.heliModel) ? F.heliModel : modelFor(a.model);
    pending = { reg: a.reg, states, model: modelId };
    const chooser = MIS.chips("heli", regs, a.reg, v => v);
    const modelChooser = MIS.chips("heliModel", MODELS.map(m => m.id), modelId, id => MODELS.find(m => m.id === id).label);
    const legend = ["crit", "warn", "ok", "none"].map(k =>
      `<span class="heli-key"><i style="background:${LEVEL[k].css}"></i>${esc(t(LEVEL[k].key))}</span>`).join("");
    const list = ZONES.map(z => {
      const s = states[z.id];
      return `<li><button type="button" class="heli-zone" data-zone="${z.id}" aria-pressed="false">` +
        `<span>${esc(t("heli.zone." + z.id))}</span><span class="heli-lvl" style="color:${LEVEL[s.k].css}">${esc(t(LEVEL[s.k].key))}</span></button></li>`;
    }).join("");
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
          <ul class="heli-list" aria-label="${esc(t("heli.zones"))}">${list}</ul>
          <p class="small muted">${esc(t("heli.demo"))}</p>
        </div>
      </div>
    </section>`;
  }

  /** Details of the selected zone: urgency and the tasks that feed it. */
  function infoHtml(id, states) {
    if (!id) return `<p class="muted">${esc(t("heli.pick"))}</p>`;
    const s = states[id];
    const tasks = s.rows.length
      ? "<ul>" + s.rows.map(x => `<li>${esc(tx(x.title))} · ${esc(remText(x))}</li>`).join("") + "</ul>"
      : `<p class="muted">${esc(t("heli.none"))}</p>`;
    return `<h3>${esc(t("heli.zone." + id))}</h3><p style="color:${LEVEL[s.k].css};font-weight:600">${esc(t(LEVEL[s.k].key))}</p>${tasks}`;
  }

  /** Zone of a model part, from its own name or the name of its groups; null if none. */
  function zoneOf(obj) {
    if (/gearbox/i.test(obj.name)) return "bte";
    for (let o = obj; o; o = o.parent) {
      if (o.name === "grp_train") return "train";
      if (o.name === "grp_prop") return "turb";
      if (o.name === "grp_rotor") return "rotor";
    }
    return null;
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
    live.renderer.dispose();
    live.renderer.forceContextLoss && live.renderer.forceContextLoss();
    live = null;
  }

  /** Parses a model file. Each mount parses its own copy, so parts can move without affecting another view. */
  function loadModel(file) {
    return new Promise((resolve, reject) => {
      new window.THREE.GLTFLoader().load(file, resolve, undefined, reject);
    });
  }

  /** Builds the scene for the pending block and starts the view. Called after each render. */
  function mount() {
    dispose();
    const host = document.getElementById("heli-view");
    if (!host || !pending) { pending = null; return; }
    const data = pending;
    pending = null;
    const THREE = window.THREE;
    let renderer = null;
    try {
      renderer = THREE && new THREE.WebGLRenderer({ antialias: true });
    } catch (e) {
      renderer = null;
    }
    if (!renderer) {
      host.innerHTML = `<p class="muted" style="padding:16px">${esc(t("heli.nogl"))}</p>`;
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e2630);
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
    const HOME = new THREE.Vector3(8.5, 3.2, 11);
    const CENTER = new THREE.Vector3(0, 0, 0);
    camera.position.copy(HOME);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(4, 8, 5);
    scene.add(sun);
    const grid = new THREE.GridHelper(14, 14, 0x334155, 0x273244);
    grid.position.y = -3.2;
    scene.add(grid);

    const heli = new THREE.Group();
    scene.add(heli);

    const pickable = [];
    const zoneView = {};
    const token = {};
    let selected = null;
    let camGoal = HOME.clone();
    let targetGoal = CENTER.clone();
    const lookAt = CENTER.clone();
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let dragging = false;
    let lastX = 0;
    let moved = 0;

    const info = document.getElementById("heli-info");
    const buttons = Array.from(document.querySelectorAll(".heli-zone"));
    const status = document.createElement("p");
    status.className = "heli-status muted";
    status.textContent = t("heli.loading");
    host.appendChild(status);

    /** Selects a zone (or none): moves it out, aims the camera at it, updates the page. */
    function select(id) {
      selected = id || null;
      info.innerHTML = infoHtml(selected, data.states);
      buttons.forEach(b => b.setAttribute("aria-pressed", String(b.dataset.zone === selected)));
      if (!selected) {
        camGoal = HOME.clone();
        targetGoal = CENTER.clone();
        return;
      }
      const v = zoneView[selected];
      if (!v) return;
      targetGoal = v.center.clone();
      camGoal = v.center.clone().add(v.offset);
    }

    /** Places the parts of the loaded model in the scene and records each zone's parts. */
    function build(gltf) {
      const src = gltf.scene;
      const box = new THREE.Box3().setFromObject(src);
      const size = box.getSize(new THREE.Vector3());
      const k = SIZE / Math.max(size.x, size.y, size.z, 1e-6);
      src.scale.setScalar(k);
      src.position.copy(box.getCenter(new THREE.Vector3()).multiplyScalar(-k));
      heli.add(src);
      src.updateMatrixWorld(true);
      scene.userData.model = src;

      const byZone = { rotor: [], bte: [], turb: [], train: [] };
      src.traverse(obj => {
        if (!obj.isMesh) return;
        const z = zoneOf(obj);
        if (z) byZone[z].push(obj);
      });

      ZONES.forEach(z => {
        const meshes = byZone[z.id];
        if (!meshes.length) return;
        const hex = LEVEL[data.states[z.id].k].hex;
        const union = new THREE.Box3();
        meshes.forEach(m => {
          m.material = Array.isArray(m.material) ? m.material.map(x => x.clone()) : m.material.clone();
          [].concat(m.material).forEach(x => x.color && x.color.setHex(hex));
          const wc = new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());
          const off = wc.clone().sub(new THREE.Vector3(0, 0, 0));
          if (off.lengthSq() < 1e-6) off.set(0, 1, 0);
          off.y += 0.35;
          off.normalize();
          const p = m.parent;
          const a0 = p.worldToLocal(wc.clone());
          const a1 = p.worldToLocal(wc.clone().add(off));
          m.userData = { zone: z.id, home: m.position.clone(), dir: a1.sub(a0).normalize() };
          union.expandByObject(m);
          pickable.push(m);
        });
        const center = union.getCenter(new THREE.Vector3());
        const span = Math.max(1.5, union.getSize(new THREE.Vector3()).length());
        zoneView[z.id] = { center, offset: new THREE.Vector3(0.9, 0.4, 1.2).multiplyScalar(span) };
      });
      status.remove();
    }

    const onDown = e => { dragging = true; lastX = e.clientX; moved = 0; };
    const onUp = e => {
      if (!dragging) return;
      dragging = false;
      if (moved < 5) {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const hit = raycaster.intersectObjects(pickable, false)[0];
        select(hit ? hit.object.userData.zone : null);
      }
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
      const dist = THREE.MathUtils.clamp(offset.length() * (1 + Math.sign(e.deltaY) * 0.08), 1.5, 22);
      camGoal = targetGoal.clone().add(offset.setLength(dist));
    };
    const onButton = e => {
      const b = e.target.closest(".heli-zone");
      if (b) select(selected === b.dataset.zone ? null : b.dataset.zone);
    };
    const body = host.parentNode.parentNode;
    const canvas = renderer.domElement;
    const listeners = [
      [canvas, "pointerdown", onDown],
      [window, "pointerup", onUp],
      [window, "pointermove", onMove],
      [canvas, "wheel", onWheel, { passive: false }],
      [body, "click", onButton]
    ];
    listeners.forEach(([target, type, fn, opts]) => target.addEventListener(type, fn, opts));

    function resize() {
      const w = host.clientWidth || 1;
      const h = host.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    if (ro) ro.observe(host);
    listeners.push([window, "resize", resize]);
    window.addEventListener("resize", resize);
    resize();

    select(null);
    live = { renderer, raf: 0, ro, listeners, scene, token };
    const loop = () => {
      live.raf = requestAnimationFrame(loop);
      if (!dragging) heli.rotation.y += 0.002;
      pickable.forEach(m => {
        const goal = m.userData.zone === selected
          ? m.userData.home.clone().add(m.userData.dir.clone().multiplyScalar(EXPLODE))
          : m.userData.home;
        m.position.lerp(goal, 0.12);
      });
      camera.position.lerp(camGoal, 0.08);
      lookAt.lerp(targetGoal, 0.08);
      camera.lookAt(lookAt);
      renderer.render(scene, camera);
    };
    loop();

    const file = (MODELS.find(m => m.id === data.model) || MODELS[1]).file;
    loadModel(file).then(gltf => {
      if (!live || live.token !== token) return;
      build(gltf);
      select(selected);
    }).catch(() => {
      if (!live || live.token !== token) return;
      status.textContent = t("heli.model_error");
    });
  }

  MIS.heliBlock = heliBlock;
  MIS.heliMount = mount;
})();
