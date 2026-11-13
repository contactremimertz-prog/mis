/* AHMIS – vue 3D d'un hélicoptère sur la fiche aéronef.
 *
 * Modèle de référence (H135, H145, NH90, Super Puma) chargé depuis static/ahmis/models/
 * avec three.js et son chargeur GLTF (static/ahmis/vendor/). Si le type n'a pas de
 * modèle ou si le chargement échoue, un modèle générique est construit à la place.
 * Toutes les pièces du modèle sont cliquables ; au moins 30 portent une révision
 * simulée (déterministe par immatriculation), signalée comme sans valeur de navigabilité.
 * Double-clic sur une pièce : vue isolée ou rayons X, avec retour à la vue globale.
 * Chaque zone prend la couleur fournie par le serveur (data-level des boutons),
 * calculée à partir des échéances CAMO. Le clic sur une zone (dans la vue ou dans
 * la liste) la sort de l'appareil et rapproche la caméra. Sans WebGL, la liste
 * des zones reste utilisable. Aucune donnée n'est injectée en HTML par ce script.
 */
(function () {
  "use strict";

  var COLORS = { crit: 0xb3261e, warn: 0xb44d00, ok: 0x1d7a46, none: 0x475569 };

  function init() {
    var card = document.querySelector("[data-heli3d]");
    if (!card) return;
    var host = card.querySelector("#heli-view");
    var buttons = Array.prototype.slice.call(card.querySelectorAll(".heli-zone"));
    var panels = Array.prototype.slice.call(card.querySelectorAll("[data-zone-info]"));
    var level = {}, names = {};
    buttons.forEach(function (b) {
      level[b.dataset.zone] = b.dataset.level in COLORS ? b.dataset.level : "none";
      names[b.dataset.zone] = b.dataset.label || "";
    });
    var toggle = card.querySelector("[data-heli-names]");
    var navLinks = Array.prototype.slice.call(card.querySelectorAll("[data-heli-nav]"));
    var navSelect = card.querySelector("[data-heli-select]");
    /** Adresse d'un autre appareil, en gardant la zone choisie. */
    function withZone(href, id) {
      var u = new URL(href, location.href);
      if (id) u.searchParams.set("zone", id); else u.searchParams.delete("zone");
      u.hash = "vue-3d";
      return u.pathname + u.search + u.hash;
    }

    var view = null;
    function select(id) {
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.zone === id)); });
      panels.forEach(function (p) { p.hidden = p.dataset.zoneInfo !== (id || ""); });
      navLinks.forEach(function (a) { a.setAttribute("href", withZone(a.getAttribute("href"), id)); });
      if (view) view.focus(id);
    }
    var current = null;
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        current = current === b.dataset.zone ? null : b.dataset.zone;
        select(current);
      });
    });

    var navForm = card.querySelector("[data-heli-form]");
    if (navForm && navSelect) {
      navForm.hidden = false;  // sans JS, seuls les liens précédent et suivant sont proposés
      // Le changement d'appareil attend le bouton « Ouvrir » : choisir dans la liste ne quitte pas la page.
      navForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var v = navSelect.value;
        // Seules les adresses internes proposées par le serveur sont suivies.
        if (v && new URL(v, location.origin).origin === location.origin) location.assign(withZone(v, current));
      });
    }
    var onPick = function (id) { current = id; select(id); };
    var texts = {};
    try { texts = JSON.parse(document.getElementById("heli-texts").textContent) || {}; } catch (e) { texts = {}; }
    var status = card.querySelector("[data-heli-status]");
    var modelUrl = card.dataset.model;
    if (modelUrl && window.THREE && window.THREE.GLTFLoader) {
      // Le modèle de référence remplace le modèle générique une fois chargé.
      view = buildGltf(card, host, level, names, onPick, texts);
      if (view && status) { status.textContent = texts.loading || ""; status.hidden = false; }
      if (view) {
        view.ready.then(function () { if (status) status.hidden = true; select(current); }, function () {
          view.dispose();
          view = build(host, level, names, onPick);
          if (view && toggle) view.showNames(toggle.checked);
          if (status) { status.textContent = texts.model_error || ""; status.hidden = false; }
          select(current);
        });
      }
    } else {
      view = build(host, level, names, onPick);
    }
    // Zone demandée par l'adresse (?zone=…), si elle existe sur cette page.
    var asked = new URLSearchParams(location.search).get("zone");
    if (!Object.prototype.hasOwnProperty.call(level, asked)) asked = null;
    current = asked;
    select(asked);  // sans JS, toutes les fiches de zone restent visibles
    if (toggle && view) {
      var saved = null;
      try { saved = localStorage.getItem("ahmis.heli.names"); } catch (e) { saved = null; }
      if (saved === "0") toggle.checked = false;
      view.showNames(toggle.checked);
      toggle.addEventListener("change", function () {
        view.showNames(toggle.checked);
        try { localStorage.setItem("ahmis.heli.names", toggle.checked ? "1" : "0"); } catch (e) { /* stockage indisponible */ }
      });
    }
    if (!view) {
      host.hidden = true;
      card.querySelector(".heli-hint").hidden = true;
      card.querySelector(".heli-nogl").hidden = false;
      if (toggle) toggle.parentNode.hidden = true;
    }
  }

  /** Construit la scène. Renvoie {focus(id), showNames(bool)} ou null si WebGL est indisponible. */
  function build(host, level, names, onPick) {
    var THREE = window.THREE;
    var renderer = null;
    try {
      renderer = THREE && new THREE.WebGLRenderer({ antialias: true });
    } catch (e) {
      renderer = null;
    }
    if (!renderer) return null;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e2630);
    var camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
    var HOME = new THREE.Vector3(5.5, 2.6, 7.5);
    var CENTER = new THREE.Vector3(0, 0.3, 0);
    camera.position.copy(HOME);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
    var sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(4, 8, 5);
    scene.add(sun);
    var grid = new THREE.GridHelper(14, 14, 0x334155, 0x273244);
    grid.position.y = -1.9;
    scene.add(grid);

    var heli = new THREE.Group();
    heli.position.y = 0.1;
    scene.add(heli);

    var bodyMat = new THREE.MeshStandardMaterial({ color: 0x8a97a8, metalness: 0.2, roughness: 0.5 });
    var glassMat = new THREE.MeshStandardMaterial({ color: 0x9bb7c9, transparent: true, opacity: 0.45, roughness: 0.1 });
    var darkMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });
    var pickable = [];
    function zoneMat(id) { return new THREE.MeshStandardMaterial({ color: COLORS[level[id] || "none"], roughness: 0.4 }); }

    /** Pièce d'une zone : colorée, cliquable, sortie de l'appareil quand elle est choisie. */
    function zoneMesh(geo, pos, id, rotZ, dir) {
      var m = new THREE.Mesh(geo, zoneMat(id));
      m.position.copy(pos);
      if (rotZ) m.rotation.z = rotZ;
      m.userData.zone = id;
      m.userData.home = pos.clone();
      m.userData.dir = dir || pos.clone().normalize().add(new THREE.Vector3(0, 0.6, 0)).normalize();
      pickable.push(m);
      heli.add(m);
      return m;
    }
    function part(geo, mat, x, y, z) { var m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); heli.add(m); return m; }

    // Fuselage et verrière
    var cabin = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), bodyMat);
    cabin.scale.set(1.3, 0.85, 0.85);
    heli.add(cabin);
    var canopy = new THREE.Mesh(new THREE.SphereGeometry(0.9, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2), glassMat);
    canopy.scale.set(1.0, 0.8, 0.8);
    canopy.position.set(0.7, 0.1, 0);
    heli.add(canopy);

    // Poutre de queue et dérive
    part(new THREE.BoxGeometry(2.6, 0.22, 0.22), bodyMat, -2.6, 0.2, 0);
    part(new THREE.BoxGeometry(0.06, 0.7, 0.3), darkMat, -3.85, 0.65, 0);

    // Train (patins), mât, BTP, moteur
    var skid = new THREE.BoxGeometry(2.8, 0.09, 0.09);
    zoneMesh(skid, new THREE.Vector3(0, -1.2, 0.75), "gear");
    zoneMesh(skid, new THREE.Vector3(0, -1.2, -0.75), "gear");
    [[0.6, 0.75], [-0.6, 0.75], [0.6, -0.75], [-0.6, -0.75]].forEach(function (p) { part(new THREE.BoxGeometry(0.08, 0.5, 0.08), darkMat, p[0], -0.9, p[1]); });
    zoneMesh(new THREE.BoxGeometry(0.7, 0.42, 0.55), new THREE.Vector3(0, 1.05, 0), "bte");
    part(new THREE.CylinderGeometry(0.08, 0.08, 0.45, 16), darkMat, 0, 1.4, 0);
    zoneMesh(new THREE.CylinderGeometry(0.22, 0.28, 0.95, 20), new THREE.Vector3(-0.85, 0.75, 0), "engine", Math.PI / 2);

    // Rotor anticouple (en bout de poutre) et arbre arrière
    zoneMesh(new THREE.BoxGeometry(0.04, 0.95, 0.14), new THREE.Vector3(-3.9, 0.6, 0.22), "tail", 0, new THREE.Vector3(0, 0, 1));
    zoneMesh(new THREE.CylinderGeometry(0.05, 0.05, 2.4, 10), new THREE.Vector3(-2.5, 0.38, 0), "tail", Math.PI / 2, new THREE.Vector3(0, 1, 0));

    // Rotor principal (fixe)
    var rotor = new THREE.Group();
    rotor.position.set(0, 1.7, 0);
    heli.add(rotor);
    var bladeA = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.03, 0.24), zoneMat("rotor"));
    var bladeB = bladeA.clone();
    bladeB.rotation.y = Math.PI / 2;
    rotor.add(bladeA, bladeB);
    [bladeA, bladeB].forEach(function (b) {
      b.userData.zone = "rotor";
      b.userData.home = new THREE.Vector3(0, 0, 0);
      b.userData.dir = new THREE.Vector3(0, 1, 0);
      pickable.push(b);
    });

    var selected = null;
    var camGoal = HOME.clone();
    var targetGoal = CENTER.clone();
    var lookAt = CENTER.clone();
    var raycaster = new THREE.Raycaster();
    var mouse = new THREE.Vector2();
    var dragging = false, lastX = 0, moved = 0, armed = false;
    var tmp = new THREE.Vector3();

    function focus(id) {
      selected = id || null;
      if (!selected) { camGoal = HOME.clone(); targetGoal = CENTER.clone(); return; }
      var target = pickable.filter(function (m) { return m.userData.zone === selected; })[0];
      if (!target) return;
      var world = new THREE.Vector3();
      target.getWorldPosition(world);
      targetGoal = world.clone();
      camGoal = world.clone().add(new THREE.Vector3(3.0, 1.2, 4.0));
    }

    var canvas = renderer.domElement;
    canvas.addEventListener("pointerdown", function (e) { dragging = true; armed = true; lastX = e.clientX; moved = 0; });
    // La molette ne zoome qu'après un clic dans la vue : sinon elle fait défiler la page.
    canvas.addEventListener("pointerleave", function () { armed = false; });
    window.addEventListener("pointerup", function (e) {
      if (!dragging) return;
      dragging = false;
      if (moved >= 5) return;
      var r = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      var hit = raycaster.intersectObjects(pickable, false)[0];
      var id = hit ? hit.object.userData.zone : null;
      onPick(id === selected ? null : id);
    });
    window.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var dx = e.clientX - lastX;
      moved += Math.abs(dx);
      lastX = e.clientX;
      heli.rotation.y += dx * 0.01;
    });
    canvas.addEventListener("wheel", function (e) {
      if (!armed && !e.ctrlKey) return;
      e.preventDefault();
      var offset = camGoal.clone().sub(targetGoal);
      var dist = THREE.MathUtils.clamp(offset.length() * (1 + Math.sign(e.deltaY) * 0.08), 1.5, 14);
      camGoal = targetGoal.clone().add(offset.setLength(dist));
    }, { passive: false });

    function resize() {
      var w = host.clientWidth || 1, h = host.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    if (typeof ResizeObserver !== "undefined") new ResizeObserver(resize).observe(host);
    window.addEventListener("resize", resize);
    resize();

    // Noms des zones : étiquettes HTML reliées à leur pièce par un trait, replacées à chaque image.
    var SVGNS = "http://www.w3.org/2000/svg";
    var overlay = document.createElement("div");
    overlay.className = "heli-labels";
    var lines = document.createElementNS(SVGNS, "svg");
    lines.setAttribute("aria-hidden", "true");
    overlay.appendChild(lines);
    host.appendChild(overlay);
    var labels = [];
    Object.keys(names).forEach(function (id) {
      var anchor = pickable.filter(function (m) { return m.userData.zone === id; })[0];
      if (!anchor || !names[id]) return;
      var el = document.createElement("button");
      el.type = "button";
      el.className = "heli-label lvl-" + (level[id] || "none");
      el.textContent = names[id];
      el.tabIndex = -1;  // la liste des zones porte déjà la navigation clavier
      el.setAttribute("aria-hidden", "true");
      el.addEventListener("click", function () { onPick(id === selected ? null : id); });
      var line = document.createElementNS(SVGNS, "line");
      line.setAttribute("class", "lvl-" + (level[id] || "none"));
      lines.appendChild(line);
      overlay.appendChild(el);
      labels.push({ id: id, anchor: anchor, el: el, line: line, left: null, y: null, ax: 0, ay: 0, on: false });
    });
    var world = new THREE.Vector3();
    function placeLabels() {
      var w = host.clientWidth || 1, h = host.clientHeight || 1;
      labels.forEach(function (l) {
        l.anchor.getWorldPosition(world);
        world.project(camera);
        l.on = world.z < 1 && Math.abs(world.x) < 1.05 && Math.abs(world.y) < 1.05;
        l.ax = (world.x + 1) / 2 * w;
        l.ay = (1 - world.y) / 2 * h;
        // Côté de l'étiquette : celui de la pièce, avec une marge pour éviter les sauts.
        if (l.left === null) l.left = l.ax < w / 2;
        else if (l.left && l.ax > w / 2 + 30) l.left = false;
        else if (!l.left && l.ax < w / 2 - 30) l.left = true;
      });
      [true, false].forEach(function (side) {
        var col = labels.filter(function (l) { return l.on && l.left === side; }).sort(function (a, b) { return a.ay - b.ay; });
        var prev = -100;
        col.forEach(function (l, i) {
          var goal = Math.max(prev + 30, Math.min(l.ay - 40, h - 34 - (col.length - 1 - i) * 30));
          goal = Math.max(8, goal);
          prev = goal;
          l.y = l.y === null ? goal : l.y + (goal - l.y) * 0.25;
        });
      });
      labels.forEach(function (l) {
        l.el.hidden = !l.on;
        l.line.style.display = l.on ? "" : "none";
        if (!l.on) return;
        l.el.style.top = l.y + "px";
        l.el.style.left = l.left ? "10px" : "auto";
        l.el.style.right = l.left ? "auto" : "10px";
        var lw = l.el.offsetWidth;
        l.line.setAttribute("x1", l.left ? 10 + lw : w - 10 - lw);
        l.line.setAttribute("y1", l.y + 12);
        l.line.setAttribute("x2", l.ax);
        l.line.setAttribute("y2", l.ay);
        l.el.classList.toggle("on", l.id === selected);
      });
    }
    var namesOn = true;

    var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var visible = true;
    if (typeof IntersectionObserver !== "undefined") {
      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; wake(); }).observe(host);
    }
    var raf = 0;
    function loop() {
      raf = 0;
      if (!visible || document.hidden) return;  // reprise par wake()
      raf = requestAnimationFrame(loop);
      if (!dragging && !still && !selected) heli.rotation.y += 0.002;
      pickable.forEach(function (m) {
        if (m.parent === rotor) return;
        if (m.userData.zone === selected) m.position.lerp(tmp.copy(m.userData.dir).multiplyScalar(0.9).add(m.userData.home), 0.12);
        else m.position.lerp(m.userData.home, 0.12);
      });
      rotor.position.y += ((selected === "rotor" ? 2.4 : 1.7) - rotor.position.y) * 0.12;
      camera.position.lerp(camGoal, 0.08);
      lookAt.lerp(targetGoal, 0.08);
      camera.lookAt(lookAt);
      renderer.render(scene, camera);
      if (namesOn) placeLabels();
    }
    function wake() { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(loop); }
    document.addEventListener("visibilitychange", wake);
    window.addEventListener("pagehide", function () {
      if (raf) cancelAnimationFrame(raf);
      raf = -1;
      renderer.dispose();
    });
    wake();

    return { focus: focus, showNames: function (on) { namesOn = !!on; overlay.hidden = !namesOn; } };
  }

  /* ------------------------------------------------------------------
     Modèle de référence (GLB) : pièces cliquables et révisions simulées
     ------------------------------------------------------------------ */

  /** Groupes du modèle -> zone. Les zones ATA (rotor, bte, tail, engine, gear) prennent le niveau CAMO. */
  var GROUP_ZONE = {
    grp_rotor: "rotor", grp_prop: "engine", grp_train: "gear", grp_queue: "tail",
    grp_cellule: "cellule", grp_portes: "portes", grp_feux: "feux", grp_interieur: "interieur"
  };
  /** Types de révision simulée, reconnus sur le nom de la pièce, avec leur intervalle (heures de vol). */
  var REVS = [
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
  var MIN_REVS = 30;
  var RANK = { none: 0, ok: 1, warn: 2, crit: 3 };
  var SIZE = 6, EXPLODE = 1.3;

  function worst(a, b) { return RANK[b] > RANK[a] ? b : a; }
  function revLevel(rev) { return !rev ? "none" : rev.st === "overdue" ? "crit" : rev.st === "soon" ? "warn" : "ok"; }
  function fmt(text, params) { return String(text || "").replace(/\{(\w+)\}/g, function (m, k) { return params[k] !== undefined ? params[k] : m; }); }

  /** Nombres pseudo-aléatoires déterministes : même appareil, même simulation. */
  function seeded(text) {
    var h = 2166136261;
    for (var i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
    var s = h >>> 0;
    return function () {
      s = (s + 0x6d2b79f5) | 0;
      var r = Math.imul(s ^ (s >>> 15), 1 | s);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  /** « cockpit_door_rh » -> « Cockpit door RH ». */
  function partLabel(name) {
    var s = String(name || "").replace(/_/g, " ").replace(/\b(rh|lh)\b/gi, function (w) { return w.toUpperCase(); }).trim();
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : "?";
  }

  function zoneOf(obj) {
    if (/gearbox/i.test(obj.name)) return "bte";
    for (var o = obj; o; o = o.parent) if (GROUP_ZONE[o.name]) return GROUP_ZONE[o.name];
    return null;
  }

  /** Pièces du modèle (un nœud à plusieurs matériaux est un groupe de maillages) et révisions simulées. */
  function partsOf(src, seed) {
    var parts = [], byObj = new Map();
    src.traverse(function (m) {
      if (!m.isMesh) return;
      var multi = m.parent && m.parent.type === "Group" && m.name.indexOf(m.parent.name + "_mesh") === 0;
      var obj = multi ? m.parent : m;
      var p = byObj.get(obj);
      if (!p) {
        p = { idx: parts.length, obj: obj, meshes: [], name: obj.name, label: partLabel(obj.name), zone: zoneOf(obj), rev: null };
        byObj.set(obj, p);
        parts.push(p);
      }
      p.meshes.push(m);
    });
    var rand = seeded(seed);
    var pool = parts.filter(function (p) { return p.zone; });
    for (var i = pool.length - 1; i > 0; i--) {
      var j = Math.floor(rand() * (i + 1));
      var t = pool[i]; pool[i] = pool[j]; pool[j] = t;
    }
    var n = Math.min(pool.length, Math.max(MIN_REVS, Math.round(pool.length * 0.5)));
    pool.slice(0, n).forEach(function (p) {
      var type = REVS.filter(function (r) { return r.re.test(p.name); })[0];
      var roll = rand();
      var st = roll < 0.12 ? "overdue" : roll < 0.35 ? "soon" : "ok";
      var rem = st === "overdue" ? -(1 + Math.floor(rand() * 25)) : st === "soon" ? 1 + Math.floor(rand() * 24) : 25 + Math.floor(rand() * (type.h - 25));
      p.rev = { type: type.id, h: type.h, rem: rem, st: st };
    });
    return parts;
  }

  /** Construit la vue sur le modèle GLB. Renvoie {focus, showNames, ready, dispose} ou null sans WebGL. */
  function buildGltf(card, host, level, names, onPick, texts) {
    var THREE = window.THREE;
    var renderer = null;
    try { renderer = new THREE.WebGLRenderer({ antialias: true }); } catch (e) { renderer = null; }
    if (!renderer) return null;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if ("outputEncoding" in renderer) renderer.outputEncoding = THREE.sRGBEncoding;
    host.appendChild(renderer.domElement);
    var COLORS = { crit: 0xb3261e, warn: 0xb44d00 };
    var zt = texts.zone || {}, rt = texts.rev || {}, lt = texts.lvl || {};
    var info = card.querySelector("[data-part-info]");
    var bar = card.querySelector("[data-heli-focusbar]");

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e2630);
    var camera = new THREE.PerspectiveCamera(40, 1, 0.05, 200);
    var HOME = new THREE.Vector3(6.2, 2.4, 8);
    var CENTER = new THREE.Vector3(0, 0, 0);
    camera.position.copy(HOME);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 1.0));
    var sun = new THREE.DirectionalLight(0xffffff, 1.0);
    sun.position.set(4, 8, 5);
    scene.add(sun);
    var grid = new THREE.GridHelper(16, 16, 0x334155, 0x273244);
    grid.position.y = -3.2;
    scene.add(grid);
    var heli = new THREE.Group();
    scene.add(heli);

    var parts = [], meshes = [], anchors = {};
    var selZone = null, selPart = null, focus = null;  // focus = {idx, mode: "iso"|"xray"}
    var camGoal = HOME.clone(), targetGoal = CENTER.clone(), lookAt = CENTER.clone();
    var ghost = new THREE.MeshBasicMaterial({ color: 0x9fb3c8, transparent: true, opacity: 0.08, depthWrite: false });
    var tmp = new THREE.Vector3();

    function partColour(p) {
      var k = worst(revLevel(p.rev), p.zone && level[p.zone] ? level[p.zone] : "none");
      return COLORS[k] || null;
    }
    function boxOf(obj) { return new THREE.Box3().setFromObject(obj); }

    /** Met le modèle à l'échelle, le pose sur la grille et prépare chaque pièce. */
    function place(src) {
      var box = boxOf(src), size = box.getSize(new THREE.Vector3()), mid = box.getCenter(new THREE.Vector3());
      var k = SIZE / Math.max(size.x, size.y, size.z, 1e-6);
      src.scale.multiplyScalar(k);
      src.position.sub(mid.multiplyScalar(k));
      heli.add(src);
      heli.updateMatrixWorld(true);
      parts = partsOf(src, (card.dataset.reg || "") + "|" + (card.dataset.modelId || ""));
      parts.forEach(function (p) {
        p.meshes.forEach(function (m) {
          m.userData.part = p.idx;
          m.userData.orig = m.material;
          var hex = partColour(p);
          if (hex !== null) m.material = new THREE.MeshStandardMaterial({ color: hex, roughness: 0.45, metalness: 0.1 });
          m.userData.shown = m.material;
          meshes.push(m);
        });
        var c = boxOf(p.obj).getCenter(new THREE.Vector3());
        var dir = c.clone().setY(c.y * 0.6);
        if (dir.lengthSq() < 1e-6) dir.set(0, 1, 0);
        dir.normalize();
        var par = p.obj.parent;
        var a = par.worldToLocal(c.clone()), b = par.worldToLocal(c.clone().add(dir.multiplyScalar(EXPLODE)));
        p.home = p.obj.position.clone();
        p.out = p.home.clone().add(b.sub(a));
        p.center = heli.worldToLocal(c.clone());
      });
      // Ancres des noms de zone : centre des pièces de chaque zone.
      Object.keys(names).forEach(function (id) {
        var zp = parts.filter(function (p) { return p.zone === id; });
        if (!zp.length) return;
        var box3 = new THREE.Box3();
        zp.forEach(function (p) { box3.union(boxOf(p.obj)); });
        var anchor = new THREE.Object3D();
        anchor.position.copy(heli.worldToLocal(box3.getCenter(new THREE.Vector3())));
        heli.add(anchor);
        anchors[id] = anchor;
      });
      makeLabels();
      showOverview();
    }

    var ready = new Promise(function (resolve, reject) {
      new THREE.GLTFLoader().load(card.dataset.model, function (g) {
        try { place(g.scene); resolve(); } catch (e) { reject(e); }
      }, undefined, reject);
    });

    /* ---------- panneau de la pièce (texte uniquement, aucune insertion HTML) ---------- */
    function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
    function revText(rev) { return rev.rem < 0 ? fmt(texts.rev_over, { n: -rev.rem }) : fmt(texts.rev_rem, { n: rev.rem }); }
    function zoneName(id) { return names[id] || zt[id] || ""; }
    function partButton(p) {
      var li = el("li"), b = el("button", "heli-part");
      b.type = "button";
      b.appendChild(el("span", "", p.label));
      b.appendChild(el("span", "heli-lvl lvl-" + revLevel(p.rev), revText(p.rev)));
      b.addEventListener("click", function () { pickPart(p.idx); });
      li.appendChild(b);
      return li;
    }
    function showOverview() {
      if (!info) return;
      info.textContent = "";
      var tracked = parts.filter(function (p) { return p.rev; });
      var c = tracked.filter(function (p) { return p.rev.st === "overdue"; }).length;
      var w = tracked.filter(function (p) { return p.rev.st === "soon"; }).length;
      info.appendChild(el("p", "small", fmt(texts.summary, { n: tracked.length, c: c, w: w })));
      var urgent = tracked.filter(function (p) { return p.rev.st !== "ok"; })
        .sort(function (a, b) { return (RANK[revLevel(b.rev)] - RANK[revLevel(a.rev)]) || (a.rev.rem - b.rev.rem); }).slice(0, 10);
      if (urgent.length) {
        info.appendChild(el("h4", "", texts.urgent));
        var ul = el("ul", "heli-parts");
        urgent.forEach(function (p) { ul.appendChild(partButton(p)); });
        info.appendChild(ul);
      }
      info.appendChild(el("p", "small muted", texts.pick));
      info.hidden = false;
    }
    function showPart(p) {
      if (!info) return;
      info.textContent = "";
      info.appendChild(el("h3", "", p.label));
      if (p.zone) {
        info.appendChild(el("p", "small muted", fmt(texts.zone_of, { z: zoneName(p.zone) })));
        if (level[p.zone] && Object.prototype.hasOwnProperty.call(names, p.zone)) {
          info.appendChild(el("p", "small lvl-" + level[p.zone], fmt(texts.zone_camo, { l: lt[level[p.zone]] || level[p.zone] })));
        }
      }
      if (p.rev) {
        info.appendChild(el("p", "heli-lvl lvl-" + revLevel(p.rev), (lt[revLevel(p.rev)] || "") + " · " + revText(p.rev)));
        var ul = el("ul", "small");
        [rt[p.rev.type], fmt(texts.rev_every, { n: p.rev.h })].forEach(function (s) { ul.appendChild(el("li", "", s)); });
        info.appendChild(ul);
        info.appendChild(el("p", "small muted", texts.sim));
      } else {
        info.appendChild(el("p", "small muted", texts.part_none));
      }
      var btns = el("div", "heli-focus-btns");
      [["iso", texts.iso], ["xray", texts.xray]].forEach(function (m) {
        var b = el("button", "btn small", m[1]);
        b.type = "button";
        b.addEventListener("click", function () { enterFocus(p.idx, m[0]); });
        btns.appendChild(b);
      });
      info.appendChild(btns);
      info.hidden = false;
    }

    /* ---------- sélection, vue isolée et rayons X ---------- */
    function aim(center, dist) {
      var w = heli.localToWorld(center.clone());
      targetGoal = w.clone();
      camGoal = w.clone().add(new THREE.Vector3(3, 1.2, 4).setLength(dist));
    }
    function home() { selPart = null; camGoal = HOME.clone(); targetGoal = CENTER.clone(); showOverview(); }
    function zoneFocus(id) {
      exitFocus(true);
      selZone = id || null;
      selPart = null;
      if (!selZone || !anchors[selZone]) { camGoal = HOME.clone(); targetGoal = CENTER.clone(); showOverview(); return; }
      aim(anchors[selZone].position, 5.5);
      showOverview();
    }
    function pickPart(idx) {
      var p = parts[idx];
      if (!p) return;
      if (focus && focus.idx !== idx) exitFocus(true);
      var hadZone = selZone;
      selZone = null;
      if (hadZone) onPick(null);  // désélectionne la zone de la liste (sans effet sur la vue)
      selPart = idx;
      var size = boxOf(p.obj).getSize(tmp).length();
      aim(p.center, Math.max(2.2, size * 2.2));
      showPart(p);
    }
    function applyFocus() {
      parts.forEach(function (p) {
        var mine = focus && p.idx === focus.idx;
        p.meshes.forEach(function (m) {
          m.visible = !focus || mine || focus.mode === "xray";
          m.material = focus && !mine && focus.mode === "xray" ? ghost : m.userData.shown;
        });
      });
      if (bar) bar.hidden = !focus;
    }
    function enterFocus(idx, mode) {
      if (selPart !== idx) pickPart(idx);
      focus = { idx: idx, mode: mode === "xray" ? "xray" : "iso" };
      applyFocus();
    }
    function exitFocus(quiet) {
      if (!focus) return;
      focus = null;
      applyFocus();
      if (!quiet && selPart !== null) pickPart(selPart);
    }
    if (bar) {
      Array.prototype.forEach.call(bar.querySelectorAll("[data-focus]"), function (b) {
        b.addEventListener("click", function () {
          if (b.dataset.focus === "exit") { exitFocus(true); home(); }
          else if (selPart !== null) enterFocus(selPart, b.dataset.focus);
        });
      });
    }

    /* ---------- souris ---------- */
    var raycaster = new THREE.Raycaster(), mouse = new THREE.Vector2();
    var dragging = false, lastX = 0, moved = 0, armed = false;
    var canvas = renderer.domElement;
    function hitAt(e) {
      var r = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      var list = meshes.filter(function (m) { return m.visible && (!focus || m.userData.part === focus.idx); });
      var hit = raycaster.intersectObjects(list, false)[0];
      return hit ? hit.object.userData.part : null;
    }
    canvas.addEventListener("pointerdown", function (e) { dragging = true; armed = true; lastX = e.clientX; moved = 0; });
    canvas.addEventListener("pointerleave", function () { armed = false; });
    function onUp(e) {
      if (!dragging) return;
      dragging = false;
      if (moved >= 5 || !parts.length) return;
      var idx = hitAt(e);
      if (idx !== null) pickPart(idx);
      else if (!focus) { home(); onPick(null); }
    }
    function onMove(e) {
      if (!dragging) return;
      var dx = e.clientX - lastX;
      moved += Math.abs(dx);
      lastX = e.clientX;
      if (focus) camGoal = targetGoal.clone().add(camGoal.clone().sub(targetGoal).applyAxisAngle(new THREE.Vector3(0, 1, 0), -dx * 0.01));
      else heli.rotation.y += dx * 0.01;
    }
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointermove", onMove);
    canvas.addEventListener("dblclick", function (e) {
      var idx = hitAt(e);
      if (idx !== null) enterFocus(idx, focus ? focus.mode : "iso");
    });
    canvas.addEventListener("wheel", function (e) {
      if (!armed && !e.ctrlKey) return;
      e.preventDefault();
      var offset = camGoal.clone().sub(targetGoal);
      var dist = THREE.MathUtils.clamp(offset.length() * (1 + Math.sign(e.deltaY) * 0.08), focus ? 0.3 : 1.2, 22);
      camGoal = targetGoal.clone().add(offset.setLength(dist));
    }, { passive: false });

    function resize() {
      var w = host.clientWidth || 1, h = host.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    var ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    if (ro) ro.observe(host);
    window.addEventListener("resize", resize);
    resize();

    /* ---------- noms des zones ---------- */
    var SVGNS = "http://www.w3.org/2000/svg";
    var overlay = el("div", "heli-labels");
    var lines = document.createElementNS(SVGNS, "svg");
    lines.setAttribute("aria-hidden", "true");
    overlay.appendChild(lines);
    host.appendChild(overlay);
    var labels = [], namesOn = true;
    function makeLabels() {
      Object.keys(anchors).forEach(function (id) {
        if (!names[id]) return;
        var b = el("button", "heli-label lvl-" + (level[id] || "none"), names[id]);
        b.type = "button";
        b.tabIndex = -1;
        b.setAttribute("aria-hidden", "true");
        b.addEventListener("click", function () { onPick(id === selZone ? null : id); });
        var line = document.createElementNS(SVGNS, "line");
        line.setAttribute("class", "lvl-" + (level[id] || "none"));
        lines.appendChild(line);
        overlay.appendChild(b);
        labels.push({ id: id, anchor: anchors[id], el: b, line: line, left: null, y: null, ax: 0, ay: 0, on: false });
      });
    }
    var wpos = new THREE.Vector3();
    function placeLabels() {
      var w = host.clientWidth || 1, h = host.clientHeight || 1;
      labels.forEach(function (l) {
        l.anchor.getWorldPosition(wpos);
        wpos.project(camera);
        l.on = !focus && wpos.z < 1 && Math.abs(wpos.x) < 1.05 && Math.abs(wpos.y) < 1.05;
        l.ax = (wpos.x + 1) / 2 * w;
        l.ay = (1 - wpos.y) / 2 * h;
        if (l.left === null) l.left = l.ax < w / 2;
        else if (l.left && l.ax > w / 2 + 30) l.left = false;
        else if (!l.left && l.ax < w / 2 - 30) l.left = true;
      });
      [true, false].forEach(function (side) {
        var col = labels.filter(function (l) { return l.on && l.left === side; }).sort(function (a, b) { return a.ay - b.ay; });
        var prev = -100;
        col.forEach(function (l, i) {
          var goal = Math.max(8, Math.max(prev + 30, Math.min(l.ay - 40, h - 34 - (col.length - 1 - i) * 30)));
          prev = goal;
          l.y = l.y === null ? goal : l.y + (goal - l.y) * 0.25;
        });
      });
      labels.forEach(function (l) {
        l.el.hidden = !l.on;
        l.line.style.display = l.on ? "" : "none";
        if (!l.on) return;
        l.el.style.top = l.y + "px";
        l.el.style.left = l.left ? "10px" : "auto";
        l.el.style.right = l.left ? "auto" : "10px";
        var lw = l.el.offsetWidth;
        l.line.setAttribute("x1", l.left ? 10 + lw : w - 10 - lw);
        l.line.setAttribute("y1", l.y + 12);
        l.line.setAttribute("x2", l.ax);
        l.line.setAttribute("y2", l.ay);
        l.el.classList.toggle("on", l.id === selZone);
      });
    }

    /* ---------- boucle d'affichage ---------- */
    var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var visible = true, raf = 0, dead = false;
    if (typeof IntersectionObserver !== "undefined") {
      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; wake(); }).observe(host);
    }
    function loop() {
      raf = 0;
      if (dead || !visible || document.hidden) return;
      raf = requestAnimationFrame(loop);
      if (!dragging && !still && !selZone && selPart === null) heli.rotation.y += 0.002;
      parts.forEach(function (p) {
        var out = p.idx === selPart || (selZone && p.zone === selZone);
        p.obj.position.lerp(out ? p.out : p.home, 0.12);
      });
      camera.position.lerp(camGoal, 0.08);
      lookAt.lerp(targetGoal, 0.08);
      camera.lookAt(lookAt);
      renderer.render(scene, camera);
      if (namesOn) placeLabels();
    }
    function wake() { if (!dead && !raf && visible && !document.hidden) raf = requestAnimationFrame(loop); }
    document.addEventListener("visibilitychange", wake);
    function dispose() {
      dead = true;
      if (raf > 0) cancelAnimationFrame(raf);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("resize", resize);
      if (ro) ro.disconnect();
      if (bar) bar.hidden = true;
      if (info) info.hidden = true;
      renderer.dispose();
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    }
    window.addEventListener("pagehide", dispose);
    wake();

    return {
      focus: function (id) { if (id !== selZone) zoneFocus(id); },
      showNames: function (on) { namesOn = !!on; overlay.hidden = !namesOn; },
      ready: ready,
      dispose: dispose
    };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
