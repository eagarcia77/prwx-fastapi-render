/* PR-WX v3.6.0 — AURORA 3D Command Center */
(function () {
  const VERSION = "3.6.0";
  const $ = (id) => document.getElementById(id);
  const cfg = window.PRWX_CONFIG || {};
  const paths = cfg.paths || {};
  let renderer, scene, camera, animationId;
  let autoRotate = true;
  let dustGroup, stormGroup, nodeGroup, worldGroup;

  function apiBase() {
    const input = $("apiBase");
    return ((input && input.value) || cfg.defaultApiBase || window.location.origin).replace(/\/$/, "");
  }

  async function getJSON(path) {
    const res = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  }

  function esc(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }

  function project(lon, lat, alt = 0) {
    const x = ((Number(lon) + 72) / 14 - 0.5) * 10.5;
    const z = -(((Number(lat) - 10) / 14 - 0.5) * 7.2);
    const y = Number(alt) || 0;
    return { x, y, z };
  }

  function colorForRisk(value) {
    const n = Number(value);
    if (n >= 65) return 0xfb7185;
    if (n >= 45) return 0xfacc15;
    return 0x34d399;
  }

  function lineFromPoints(points, color, altitude = 0.45, opacity = 0.95) {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    points.forEach((p, idx) => {
      const v = project(p[0], p[1], altitude + idx * 0.04);
      vertices.push(v.x, v.y, v.z);
    });
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
    return new THREE.Line(geometry, material);
  }

  function makeTextSprite(text, color = "#e0f2fe") {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 128;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "bold 42px Arial";
    ctx.fillStyle = "rgba(2,6,23,.72)";
    ctx.roundRect?.(8, 28, 496, 72, 22);
    if (ctx.roundRect) ctx.fill();
    ctx.fillStyle = color;
    ctx.fillText(text, 26, 78);
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(1.45, 0.38, 1);
    return sprite;
  }

  function addWorld(payload) {
    worldGroup = new THREE.Group();
    const oceanGeometry = new THREE.CircleGeometry(5.9, 96);
    const oceanMaterial = new THREE.MeshPhongMaterial({ color: 0x0f766e, transparent: true, opacity: 0.32, side: THREE.DoubleSide });
    const ocean = new THREE.Mesh(oceanGeometry, oceanMaterial);
    ocean.rotation.x = -Math.PI / 2;
    ocean.position.y = -0.035;
    worldGroup.add(ocean);

    const grid = new THREE.GridHelper(12, 24, 0x38bdf8, 0x155e75);
    grid.material.transparent = true;
    grid.material.opacity = 0.22;
    worldGroup.add(grid);

    const domeGeo = new THREE.SphereGeometry(2.05, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const domeMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.12, wireframe: true });
    const dome = new THREE.Mesh(domeGeo, domeMat);
    const pr = payload.reference_point || { lon: -66.5901, lat: 18.2208 };
    const pp = project(pr.lon, pr.lat, 0.08);
    dome.position.set(pp.x, pp.y, pp.z);
    worldGroup.add(dome);

    const prCore = new THREE.Mesh(new THREE.SphereGeometry(0.13, 24, 24), new THREE.MeshStandardMaterial({ color: 0xfed141, emissive: 0x85714d, emissiveIntensity: 0.7 }));
    prCore.position.set(pp.x, 0.23, pp.z);
    worldGroup.add(prCore);
    const label = makeTextSprite("Puerto Rico", "#fef9c3");
    label.position.set(pp.x, 0.7, pp.z);
    worldGroup.add(label);

    scene.add(worldGroup);
  }

  function addMunicipalNodes(nodes) {
    nodeGroup = new THREE.Group();
    (nodes || []).forEach((node) => {
      const p = project(node.lon, node.lat, 0);
      const h = Math.max(0.35, Number(node.risk || 40) / 38);
      const color = colorForRisk(node.risk);
      const tower = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.105, h, 18), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.42, transparent: true, opacity: 0.88 }));
      tower.position.set(p.x, h / 2, p.z);
      nodeGroup.add(tower);
      const top = new THREE.Mesh(new THREE.SphereGeometry(0.13, 20, 20), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.9 }));
      top.position.set(p.x, h + 0.12, p.z);
      nodeGroup.add(top);
    });
    scene.add(nodeGroup);
  }

  function addDustStreams(streams) {
    dustGroup = new THREE.Group();
    (streams || []).forEach((stream) => {
      const altitude = Number(stream.altitude_km || 3.0) / 3.8;
      const line = lineFromPoints(stream.points || [], 0xfacc15, altitude, 0.72);
      dustGroup.add(line);
      (stream.points || []).forEach((p, idx) => {
        const pos = project(p[0], p[1], altitude + 0.08 * Math.sin(idx));
        const particle = new THREE.Mesh(new THREE.SphereGeometry(0.06 + Number(stream.intensity || 0.4) * 0.07, 12, 12), new THREE.MeshBasicMaterial({ color: 0xfacc15, transparent: true, opacity: 0.55 }));
        particle.position.set(pos.x, pos.y, pos.z);
        particle.userData = { seed: idx * 0.7, speed: 0.004 + Number(stream.intensity || 0.4) * 0.006 };
        dustGroup.add(particle);
      });
    });
    scene.add(dustGroup);
  }

  function addStormStreams(streams) {
    stormGroup = new THREE.Group();
    (streams || []).forEach((stream) => {
      const line = lineFromPoints(stream.points || [], 0x38bdf8, 0.72, 0.9);
      stormGroup.add(line);
      const last = (stream.points || [])[Math.max(0, (stream.points || []).length - 1)];
      if (last) {
        const pos = project(last[0], last[1], 0.95);
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.035, 12, 40), new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.9 }));
        ring.rotation.x = Math.PI / 2;
        ring.position.set(pos.x, pos.y, pos.z);
        ring.userData = { spin: true };
        stormGroup.add(ring);
      }
    });
    scene.add(stormGroup);
  }

  function renderFallback(message) {
    const target = $("aurora3dViewport");
    if (!target) return;
    target.innerHTML = `<div class="aurora3dFallback"><div class="aurora3dFallbackBox"><h3>AURORA 3D Command Center</h3><p>${esc(message || "Vista 3D en modo compatible.")}</p><div class="aurora3dCssWorld"></div><p>El navegador no cargó WebGL/Three.js, pero se conserva una vista 3D CSS accesible.</p></div></div>`;
  }

  function updatePanel(payload) {
    const panel = $("aurora3dPanel");
    if (!panel) return;
    const model = payload.model || {};
    panel.innerHTML = `
      <h3>${esc(model.model_name || "AURORA 3D")}</h3>
      <p>${esc(payload.summary_es || "Escena 3D experimental.")}</p>
      <div class="aurora3dMetrics">
        <div class="aurora3dMetric"><span>Nodos municipales</span><strong>${(payload.municipal_nodes || []).length}</strong></div>
        <div class="aurora3dMetric"><span>Flujos Sahara</span><strong>${(payload.dust_streams || []).length}</strong></div>
        <div class="aurora3dMetric"><span>Trayectorias</span><strong>${(payload.tropical_streams || []).length}</strong></div>
        <div class="aurora3dMetric"><span>Modo</span><strong>3D</strong></div>
      </div>
      <div class="aurora3dLegend">
        <div><span class="aurora3dDot dust"></span> Polvo del Sahara / aerosoles</div>
        <div><span class="aurora3dDot storm"></span> Trayectoria tropical</div>
        <div><span class="aurora3dDot town"></span> Torres municipales IA</div>
        <div><span class="aurora3dDot risk"></span> Domo de riesgo AURORA</div>
      </div>
      <p class="note">${esc(payload.disclaimer || "Validar con fuentes oficiales.")}</p>
    `;
  }

  function initThree(payload) {
    const target = $("aurora3dViewport");
    if (!target || !window.THREE) {
      renderFallback("Three.js no cargó o WebGL no está disponible.");
      return;
    }
    target.innerHTML = `<div class="aurora3dGridOverlay"></div><div class="aurora3dScan"></div><div class="aurora3dHUD"><div class="aurora3dHUDTop"><span class="aurora3dBadge">AURORA 3D activo</span><span class="aurora3dBadge">Sahara · Caribe · PR</span></div></div>`;
    const width = target.clientWidth || 1000;
    const height = target.clientHeight || 650;
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020617, 0.055);
    camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    const cam = payload.scene?.camera?.position || [0, 8.5, 13.5];
    camera.position.set(cam[0], cam[1], cam[2]);
    camera.lookAt(0, 0, 0);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    target.appendChild(renderer.domElement);

    const amb = new THREE.AmbientLight(0x9bdcff, 0.7);
    scene.add(amb);
    const light = new THREE.DirectionalLight(0xffffff, 1.0);
    light.position.set(4, 8, 6);
    scene.add(light);
    const cyan = new THREE.PointLight(0x22d3ee, 1.4, 16);
    cyan.position.set(0, 4, 3);
    scene.add(cyan);

    addWorld(payload);
    addMunicipalNodes(payload.municipal_nodes || []);
    addDustStreams(payload.dust_streams || []);
    addStormStreams(payload.tropical_streams || []);

    window.addEventListener("resize", () => {
      if (!renderer || !camera || !target) return;
      const w = target.clientWidth || 1000;
      const h = target.clientHeight || 650;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
  }

  function animate() {
    animationId = requestAnimationFrame(animate);
    const t = performance.now() * 0.001;
    if (autoRotate && worldGroup) worldGroup.rotation.y = Math.sin(t * 0.18) * 0.08;
    if (dustGroup) {
      dustGroup.children.forEach((obj) => {
        if (obj.userData && obj.userData.speed) {
          obj.position.x += Math.sin(t + obj.userData.seed) * obj.userData.speed;
          obj.position.y += Math.cos(t * 1.4 + obj.userData.seed) * obj.userData.speed * 0.9;
        }
      });
    }
    if (stormGroup) {
      stormGroup.children.forEach((obj) => { if (obj.userData?.spin) obj.rotation.z += 0.02; });
    }
    if (nodeGroup) nodeGroup.children.forEach((obj, i) => { if (obj.geometry?.type === "SphereGeometry") obj.scale.setScalar(1 + Math.sin(t * 2 + i) * 0.08); });
    if (renderer && scene && camera) renderer.render(scene, camera);
  }

  async function loadScene() {
    try {
      const payload = await getJSON(paths.aurora3DScene || "/aurora-caribe/3d/scene");
      updatePanel(payload);
      if (animationId) cancelAnimationFrame(animationId);
      initThree(payload);
      animate();
    } catch (err) {
      renderFallback(`No se pudo cargar la escena 3D: ${err.message}`);
    }
  }

  function bind() {
    const refresh = $("aurora3dRefreshBtn");
    if (refresh) refresh.addEventListener("click", loadScene);
    const rotate = $("aurora3dRotateBtn");
    if (rotate) rotate.addEventListener("click", () => { autoRotate = !autoRotate; rotate.textContent = autoRotate ? "Pausar rotación" : "Rotar escena"; });
    const reset = $("aurora3dResetBtn");
    if (reset) reset.addEventListener("click", () => { if (camera) { camera.position.set(0, 8.5, 13.5); camera.lookAt(0, 0, 0); } });
  }

  document.addEventListener("DOMContentLoaded", () => { bind(); setTimeout(loadScene, 650); });
  window.PRWX_AURORA_3D = { version: VERSION, refresh: loadScene };
})();
