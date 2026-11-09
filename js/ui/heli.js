/**
 * @file Interactive 3D view of an aircraft, shown on the fleet screen.
 *
 * A generic helicopter is built with three.js (vendor/three.min.js). Each zone
 * is coloured by the most urgent maintenance task that feeds it:
 *   overdue -> high urgency (red), due soon -> medium urgency (orange), otherwise grey.
 * Clicking a zone moves it out of the airframe and brings the camera close to it.
 * Each zone is also a button in the page, so the information stays available
 * without WebGL. The model is a demonstration shape, not the real airframe.
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

  /** Colour of each urgency level, in the 3D view (hex) and in the page. */
  const LEVEL = {
    crit: { hex: 0xb42318, css: "var(--crit)", key: "heli.lvl_crit" },
    warn: { hex: 0xc2410c, css: "var(--warn)", key: "heli.lvl_warn" },
    ok: { hex: 0x64748b, css: "var(--muted)", key: "heli.lvl_ok" }
  };

  /** Data of the block being rendered, read by mount() once the page is in the DOM. */
  let pending = null;
  /** Running 3D view, released by dispose() before the next render. */
  let live = null;

  /** Urgency of each zone of an aircraft, from its maintenance tasks (a.s.tasks). */
  function zoneStates(a) {
    const out = {};
    ZONES.forEach(z => {
      const rows = a.s.tasks.filter(x => z.codes.includes(x.code));
      const k = rows.some(x => x.st === "overdue") ? "crit" : rows.some(x => x.st === "soon") ? "warn" : "ok";
      out[z.id] = { k, rows };
    });
    return out;
  }

  /** Page block: aircraft chooser, 3D canvas, zone details and a text list of the zones. */
  function heliBlock(a, regs) {
    const states = zoneStates(a);
    pending = { reg: a.reg, states, selected: null };
    const chooser = MIS.chips("heli", regs, a.reg, v => v);
    const legend = ["crit", "warn", "ok"].map(k =>
      `<span class="heli-key"><i style="background:${LEVEL[k].css}"></i>${esc(t(LEVEL[k].key))}</span>`).join("");
    const list = ZONES.map(z => {
      const s = states[z.id];
      return `<li><button type="button" class="heli-zone" data-zone="${z.id}" aria-pressed="false">` +
        `<span>${esc(t("heli.zone." + z.id))}</span><span class="heli-lvl" style="color:${LEVEL[s.k].css}">${esc(t(LEVEL[s.k].key))}</span></button></li>`;
    }).join("");
    return `<section class="card heli" aria-labelledby="heli-title">
      <div class="card-head"><h2 id="heli-title">${esc(t("heli.title"))} · ${esc(a.reg)} · ${esc(a.model)}</h2></div>
      ${chooser}
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

  /** Releases the WebGL context, the animation frame and the listeners of the running view. */
  function dispose() {
    if (!live) return;
    cancelAnimationFrame(live.raf);
    live.ro && live.ro.disconnect();
    live.listeners.forEach(([target, type, fn, opts]) => target.removeEventListener(type, fn, opts));
    live.renderer.dispose();
    live.renderer.forceContextLoss && live.renderer.forceContextLoss();
    live = null;
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
    const HOME = new THREE.Vector3(5.5, 2.6, 7.5);
    const CENTER = new THREE.Vector3(0, 0.3, 0);
    camera.position.copy(HOME);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(4, 8, 5);
    scene.add(sun);
    const grid = new THREE.GridHelper(14, 14, 0x334155, 0x273244);
    grid.position.y = -1.9;
    scene.add(grid);

    const heli = new THREE.Group();
    heli.position.y = 0.1;
    scene.add(heli);

    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.2, roughness: 0.5 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x9bb7c9, transparent: true, opacity: 0.45, roughness: 0.1 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });
    const pickable = [];

    /** Mesh of a zone: coloured by its urgency, clickable, and moved out when selected. */
    function zoneMesh(geo, pos, zoneId, rotation) {
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: LEVEL[data.states[zoneId].k].hex, roughness: 0.4 }));
      m.position.copy(pos);
      if (rotation) m.rotation.z = rotation;
      m.userData.zone = zoneId;
      m.userData.home = pos.clone();
      m.userData.dir = pos.clone().normalize().add(new THREE.Vector3(0, 0.6, 0)).normalize();
      pickable.push(m);
      heli.add(m);
      return m;
    }
    const part = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); heli.add(m); return m; };

    // Fuselage and canopy
    const cabin = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), bodyMat);
    cabin.scale.set(1.3, 0.85, 0.85);
    heli.add(cabin);
    const canopy = new THREE.Mesh(new THREE.SphereGeometry(0.9, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2), glassMat);
    canopy.scale.set(1.0, 0.8, 0.8);
    canopy.position.set(0.7, 0.1, 0);
    heli.add(canopy);

    // Tail boom and fin
    part(new THREE.BoxGeometry(2.6, 0.22, 0.22), bodyMat, -2.6, 0.2, 0);
    part(new THREE.BoxGeometry(0.06, 0.7, 0.3), darkMat, -3.85, 0.65, 0);
    part(new THREE.BoxGeometry(0.06, 0.06, 0.6), darkMat, -3.85, 0.3, 0);

    // Landing gear (train), mast, gearbox (bte), turbine (turb), main rotor (rotor)
    const skidGeo = new THREE.BoxGeometry(2.8, 0.09, 0.09);
    zoneMesh(skidGeo, new THREE.Vector3(0, -1.2, 0.75), "train");
    zoneMesh(skidGeo, new THREE.Vector3(0, -1.2, -0.75), "train");
    [[0.6, 0.75], [-0.6, 0.75], [0.6, -0.75], [-0.6, -0.75]].forEach(([x, z]) => part(new THREE.BoxGeometry(0.08, 0.5, 0.08), darkMat, x, -0.9, z));
    zoneMesh(new THREE.BoxGeometry(0.7, 0.42, 0.55), new THREE.Vector3(0, 1.05, 0), "bte");
    part(new THREE.CylinderGeometry(0.08, 0.08, 0.45, 16), darkMat, 0, 1.4, 0);
    zoneMesh(new THREE.CylinderGeometry(0.22, 0.28, 0.95, 20), new THREE.Vector3(0.95, 0.6, 0), "turb", Math.PI / 2);

    // Main rotor: fixed in this view (no spin)
    const rotor = new THREE.Group();
    rotor.position.set(0, 1.7, 0);
    heli.add(rotor);
    const bladeA = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.03, 0.24), new THREE.MeshStandardMaterial({ color: LEVEL[data.states.rotor.k].hex, roughness: 0.4 }));
    const bladeB = bladeA.clone();
    bladeB.rotation.y = Math.PI;
    rotor.add(bladeA, bladeB);
    [bladeA, bladeB].forEach(b => {
      b.userData.zone = "rotor";
      b.userData.home = new THREE.Vector3(0, 0, 0);
      b.userData.dir = new THREE.Vector3(0, 1, 0);
      pickable.push(b);
    });

    const tail = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.9, 0.12), darkMat);
    tail.position.set(-3.9, 0.6, 0.2);
    heli.add(tail);

    // Interaction state
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
      const target = pickable.find(m => m.userData.zone === selected);
      const world = new THREE.Vector3();
      target.getWorldPosition(world);
      targetGoal = world.clone();
      camGoal = world.clone().add(new THREE.Vector3(3.0, 1.2, 4.0));
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
      camGoal.sub(targetGoal).multiplyScalar(1 + Math.sign(e.deltaY) * 0.08).add(targetGoal);
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
    const loop = () => {
      live.raf = requestAnimationFrame(loop);
      if (!dragging) heli.rotation.y += 0.002;
      pickable.forEach(m => {
        if (m.parent === rotor) return;
        const goal = m.userData.zone === selected
          ? m.userData.home.clone().add(m.userData.dir.clone().multiplyScalar(0.9))
          : m.userData.home;
        m.position.lerp(goal, 0.12);
      });
      camera.position.lerp(camGoal, 0.08);
      lookAt.lerp(targetGoal, 0.08);
      camera.lookAt(lookAt);
      renderer.render(scene, camera);
    };
    live = { renderer, raf: 0, ro, listeners };
    loop();
  }

  MIS.heliBlock = heliBlock;
  MIS.heliMount = mount;
})();
