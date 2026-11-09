/* AHMIS – vue 3D d'un hélicoptère sur la fiche aéronef.
 *
 * Modèle générique construit avec three.js (static/ahmis/vendor/three.min.js).
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
    var level = {};
    buttons.forEach(function (b) { level[b.dataset.zone] = b.dataset.level in COLORS ? b.dataset.level : "none"; });

    var view = null;
    function select(id) {
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.zone === id)); });
      panels.forEach(function (p) { p.hidden = p.dataset.zoneInfo !== (id || ""); });
      if (view) view.focus(id);
    }
    var current = null;
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        current = current === b.dataset.zone ? null : b.dataset.zone;
        select(current);
      });
    });

    view = build(host, level, function (id) { current = id; select(id); });
    if (!view) {
      host.hidden = true;
      card.querySelector(".heli-hint").hidden = true;
      card.querySelector(".heli-nogl").hidden = false;
    }
  }

  /** Construit la scène. Renvoie {focus(id)} ou null si WebGL est indisponible. */
  function build(host, level, onPick) {
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
    }
    function wake() { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(loop); }
    document.addEventListener("visibilitychange", wake);
    window.addEventListener("pagehide", function () {
      if (raf) cancelAnimationFrame(raf);
      raf = -1;
      renderer.dispose();
    });
    wake();

    return { focus: focus };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
