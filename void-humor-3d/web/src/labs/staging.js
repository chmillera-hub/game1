// Lab: STAGING — director's scratch bench for docs/STAGING.md. Real VOID / JESUS / FEAR / MAGICIAN rigs + a capsule
// USER stand-in at the marks of web/src/scenes/marks.js, in rough stand-ins of the EDGE and BACKROOM sets
// (the real sets were still being built). One setup per integer second:
//   node tools/render.js stills --lab staging --t 0,1,2,3,4,5,6,7,8,9,10,11,12,13 --out out/staging
// Overlay: red = phone-UI top (90), yellow = title band (110-300), cyan = subtitle band (880-1060).
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT, CTX } from '../core/context.js';
import { Particles, CELL } from '../core/particles.js';
import { glowSprite } from '../core/materials.js';
import { clamp, lerp, smooth, DEG } from '../core/util.js';
import { VX, whisperPose } from '../chars/void.js';
import { EDGE, ROOM, LENS, px } from '../scenes/marks.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const TAU = Math.PI * 2;

// ---------------------------------------------------------------- USER stand-in (1.65 m, hoodie + bob + phone)
function userDummy() {
  const g = new THREE.Group();
  const hood = new THREE.MeshStandardMaterial({ color: 0x5a6f96, roughness: 0.85 });
  const pants = new THREE.MeshStandardMaterial({ color: 0x2c2c38, roughness: 0.9 });
  const skinM = new THREE.MeshStandardMaterial({ color: 0xe9b99a, roughness: 0.6 });
  const hairM = new THREE.MeshStandardMaterial({ color: 0x3b2418, roughness: 0.7 });
  const shoe = new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: 0.6 });
  const P = {};
  P.hips = new THREE.Group(); g.add(P.hips);
  P.torso = new THREE.Group(); P.hips.add(P.torso);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.36, 6, 16), hood); body.position.y = 0.3; P.torso.add(body);
  P.head = new THREE.Group(); P.head.position.y = 0.72; P.torso.add(P.head);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.135, 24, 18), skinM); P.head.add(head);
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 18, 0, TAU, 0, 1.7), hairM); hair.position.set(0, 0.02, -0.015); hair.rotation.x = -0.5; P.head.add(hair);
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.03, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff })); e.position.set(sx * 0.05, 0.01, 0.118); P.head.add(e);
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.016, 10, 8), new THREE.MeshBasicMaterial({ color: 0x241510 })); p.position.set(sx * 0.05, 0.01, 0.142); P.head.add(p);
  }
  P.legs = [];
  for (const sx of [-1, 1]) {
    const leg = new THREE.Group(); leg.position.set(sx * 0.1, 0, 0); P.hips.add(leg);
    const m = new THREE.Mesh(new THREE.CapsuleGeometry(0.075, 0.7, 4, 10), pants); m.position.y = -0.42; leg.add(m);
    const s = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.09, 0.26), shoe); s.position.set(0, -0.82, 0.05); leg.add(s);
    P.legs.push(leg);
  }
  P.arms = [];
  for (const sx of [-1, 1]) {
    const arm = new THREE.Group(); arm.position.set(sx * 0.24, 0.52, 0); P.torso.add(arm);
    const m = new THREE.Mesh(new THREE.CapsuleGeometry(0.06, 0.48, 4, 10), hood); m.position.y = -0.27; arm.add(m);
    P.arms.push(arm);
  }
  const phone = new THREE.Mesh(new THREE.BoxGeometry(0.075, 0.15, 0.012), new THREE.MeshBasicMaterial({ color: 0xdfeaff }));
  phone.position.set(0, -0.55, 0.06); P.arms[0].add(phone);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  const api = { g, P,
    pose(mode, pos, yaw) {
      g.position.set(...pos); g.rotation.set(0, yaw, 0);
      P.hips.position.set(0, 0.86, 0); P.hips.rotation.set(0, 0, 0); P.torso.rotation.set(0, 0, 0); P.head.rotation.set(0, 0, 0);
      P.legs.forEach((l) => l.rotation.set(0, 0, 0)); P.arms.forEach((a) => a.rotation.set(0, 0, 0));
      if (mode === 'run') {
        P.torso.rotation.x = 0.22; P.head.rotation.x = -0.25;
        P.legs[0].rotation.x = -0.7; P.legs[1].rotation.x = 0.55; P.arms[1].rotation.x = -1.0; P.arms[0].rotation.x = 0.9; P.arms[0].rotation.z = 0.5;
      } else if (mode === 'sit') {
        P.hips.position.set(0, 0.12, 0); P.torso.rotation.x = -0.32;
        P.legs.forEach((l) => { l.rotation.x = -1.42; }); P.legs[0].rotation.z = 0.1; P.legs[1].rotation.z = -0.1;
        P.arms[1].rotation.x = -2.3; P.arms[1].rotation.z = -0.35;   // raised hand (its right... the left arm of the dummy)
        P.arms[0].rotation.x = 0.7; P.arms[0].rotation.z = 0.2;      // phone hand back on the ground
        P.head.rotation.x = -0.1;
      } else if (mode === 'hug') {
        P.hips.position.set(0, 0.12, 0); P.torso.rotation.x = 0.25;
        P.legs.forEach((l) => { l.rotation.x = -0.6; });
        P.arms.forEach((a) => { a.rotation.x = -1.2; });
      }
      g.updateMatrixWorld(true);
    },
    head() { return P.head.getWorldPosition(new THREE.Vector3()); },
  };
  return api;
}

// ---------------------------------------------------------------- EDGE stand-in (sky + sun + hills + path)
function edgeStandIn() {
  const scene = new THREE.Group();
  const U = { uSun: { value: V3(0, 0.2, -1).normalize() }, uVoidDir: { value: V3(1, 0.4, 0).normalize() }, uVoid: { value: 0.6 } };
  const sky = new THREE.Mesh(new THREE.SphereGeometry(180, 48, 24), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: U,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uSun, uVoidDir; uniform float uVoid; varying vec3 vP;
      void main(){ vec3 d = normalize(vP); float h = d.y;
        vec3 zen = vec3(0.30,0.30,0.62), mid = vec3(0.98,0.70,0.62), low = vec3(1.0,0.84,0.62);
        vec3 c = mix(low, mid, smoothstep(0.0, 0.22, h)); c = mix(c, zen, smoothstep(0.22, 0.85, h));
        float sd = max(dot(d, uSun), 0.0);
        c += vec3(1.0,0.62,0.3) * pow(sd, 6.0) * 0.55 + vec3(1.0,0.85,0.6) * pow(sd, 60.0) * 1.2 + vec3(1.4,1.2,0.9) * smoothstep(0.9993, 0.9997, sd) * 2.0;
        float vd = max(dot(d, uVoidDir), 0.0); float pocket = smoothstep(0.86, 0.985, vd) * uVoid;
        c = mix(c, vec3(0.12,0.10,0.30), pocket * 0.85);
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }` }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(170, 64), new THREE.MeshStandardMaterial({ color: 0xc9d9b0, roughness: 0.95 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  // hills (sunken ellipsoids) + heightAt(x,z) so marks on slopes stand on the ground
  const HILLS = [];
  const hill = (x, z, r, h, col) => { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 20), new THREE.MeshStandardMaterial({ color: col, roughness: 0.95 })); m.scale.set(r, h, r); m.position.set(x, 0, z); m.receiveShadow = true; scene.add(m); HILLS.push([x, z, r, h]); return m; };
  hill(10.5, 14.5, 11, 1.7, 0xf6c2a0);                                        // peach crest (s01), path runs over it
  hill(EDGE.HILL_WORLD[0] - 1.2, EDGE.HILL_WORLD[2] - 0.6, 4.2, 2.75, 0xc8b0dc);   // lilac hill (s16b07)
  hill(-0.8, -13.0, 6, 0.6, 0xd9e8c0);                                        // gentle rise the user crests (s14)
  hill(14, -32, 16, 4, 0xb8a8d8); hill(-26, -38, 20, 5.5, 0xa9d8c0); hill(30, 4, 18, 4.5, 0xc4e0b4); hill(-20, 12, 12, 3.0, 0xf0b8b8);
  hill(8, -62, 30, 5, 0xd8b0c8); hill(-42, -10, 18, 4, 0xbcdcc4); hill(22, 34, 20, 5, 0xe8c0d0); hill(-6, 34, 16, 4.2, 0xb8c8e8); hill(-16, 26, 10, 2.6, 0xd6c4ec);
  const heightAt = (x, z) => { let y = 0; for (const [cx, cz, r, h] of HILLS) { const d2 = ((x - cx) ** 2 + (z - cz) ** 2) / (r * r); if (d2 < 1) y = Math.max(y, h * Math.sqrt(1 - d2)); } return y; };
  // path ribbon
  const pts = EDGE.PATH_WORLD.map((p) => V3(p[0], 0, p[2]));
  const curve = new THREE.CatmullRomCurve3(pts);
  const N = 400, pos = [], idx = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N, p = curve.getPointAt(u), tg = curve.getTangentAt(u), nrm = V3(-tg.z, 0, tg.x).normalize();
    const w = lerp(0.9, 0.6, u);
    const ya = heightAt(p.x + nrm.x * w, p.z + nrm.z * w) + 0.015, yb = heightAt(p.x - nrm.x * w, p.z - nrm.z * w) + 0.015;
    pos.push(p.x + nrm.x * w, ya, p.z + nrm.z * w, p.x - nrm.x * w, yb, p.z - nrm.z * w);
    if (i < N) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
  }
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); pg.setIndex(idx); pg.computeVertexNormals();
  const path = new THREE.Mesh(pg, new THREE.MeshStandardMaterial({ color: 0xfbeedd, roughness: 0.9, side: THREE.DoubleSide })); path.receiveShadow = true; scene.add(path);
  // crystal tree stand-in
  const tw = EDGE.TREE_WORLD;
  const tree = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({ color: 0xf0b0a0, emissive: 0x3a1a10, roughness: 0.4 }));
  tree.scale.set(1.0, 1.5, 1.0); tree.position.set(tw[0], 2.1, tw[2]); tree.castShadow = true; scene.add(tree);
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 1.2, 8), new THREE.MeshStandardMaterial({ color: 0x9a6a5a })); trunk.position.set(tw[0], 0.6, tw[2]); scene.add(trunk);
  // lights
  const hemi = new THREE.HemisphereLight(0xffe0cc, 0x7a6a8a, 1.15); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffcf9a, 2.6); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: 1, far: 60 }); key.shadow.bias = -0.0008;
  scene.add(key); scene.add(key.target);
  const fill = new THREE.DirectionalLight(0xb8a8ff, 0.5); fill.position.set(0, 4, 10); scene.add(fill);
  const galaxy = new Particles({ max: 8 }); scene.add(galaxy.mesh);
  return { scene, U, key, hemi, galaxy, heightAt,
    update(tod, voidPos, voidAmt) {
      const el = lerp(11, 1.5, tod) * Math.PI / 180;
      const sun = V3(0, Math.sin(el), -Math.cos(el));
      U.uSun.value.copy(sun);
      key.position.copy(sun).multiplyScalar(30); key.target.position.set(0, 0, 0);
      key.color.setHSL(lerp(0.085, 0.045, tod), 1, lerp(0.8, 0.68, tod)); key.intensity = lerp(2.6, 2.0, tod);
      EYE_LIGHT.uKeyDir.value.copy(sun);
      if (voidPos) U.uVoidDir.value.copy(voidPos).normalize();
      U.uVoid.value = voidAmt ?? 0.6;
    } };
}

// ---------------------------------------------------------------- BACKROOM stand-in
function roomStandIn() {
  const scene = new THREE.Group();
  const floor = new THREE.Mesh(new THREE.CircleGeometry(40, 48), new THREE.MeshStandardMaterial({ color: 0x2a2838, roughness: 0.8 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  // walls behind the janitor corner (two planes meeting at the corner)
  const cw = ROOM.W(ROOM.M.CORNER.p);
  const wallM = new THREE.MeshStandardMaterial({ color: 0x343245, roughness: 0.9 });
  const w1 = new THREE.Mesh(new THREE.PlaneGeometry(12, 7), wallM); const w2 = new THREE.Mesh(new THREE.PlaneGeometry(12, 7), wallM);
  const ax = ROOM.V(1, 0, 0).sub(ROOM.V(0, 0, 0)), az = ROOM.V(0, 0, 1).sub(ROOM.V(0, 0, 0));
  w1.position.set(cw[0] + ax.x * 0.9, 3.5, cw[2] + ax.z * 0.9); w1.lookAt(w1.position.clone().sub(ax)); scene.add(w1);
  w2.position.set(cw[0] + ax.x * 0.9 + az.x * -5.5, 3.5, cw[2] + ax.z * 0.9 + az.z * -5.5); w2.lookAt(w2.position.clone().add(az)); scene.add(w2);
  // janitor props
  const met = new THREE.MeshStandardMaterial({ color: 0x9aa4b0, metalness: 0.6, roughness: 0.4 });
  const yel = new THREE.MeshStandardMaterial({ color: 0xf2c820, roughness: 0.5 });
  const props = new THREE.Group(); scene.add(props);
  const lp = (x, z) => ROOM.W(ROOM.M.CORNER.p[0] + x, 0, ROOM.M.CORNER.p[2] + z);
  for (const [x, z] of [[-0.2, 0.3], [0.3, -0.4], [-0.6, -0.5]]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.14, 0.32, 18), met); const p = lp(x, z); b.position.set(p[0], 0.16, p[2]); props.add(b); }
  const sign = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.75, 4), yel); const sp = lp(-0.9, 0.6); sign.position.set(sp[0], 0.38, sp[2]); props.add(sign);
  for (const [x, z] of [[0.45, 0.2], [0.55, -0.1]]) { const br = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 1.4, 6), new THREE.MeshStandardMaterial({ color: 0xb08050 })); const p = lp(x, z); br.position.set(p[0], 0.7, p[2]); br.rotation.z = 0.2; props.add(br); }
  props.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  // cage
  const brass = new THREE.MeshStandardMaterial({ color: 0xc9a85a, metalness: 0.7, roughness: 0.35 });
  const cage = new THREE.Group(); const cc = ROOM.W(0, 0, 0); cage.position.set(cc[0], 0, cc[2]); scene.add(cage);
  const R = 0.42, H = 1.0;
  for (let i = 0; i < 16; i++) { const a = i / 16 * TAU; const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, H, 6), brass); bar.position.set(Math.cos(a) * R, H / 2, Math.sin(a) * R); cage.add(bar); }
  for (const y of [0.02, H * 0.55, H]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(R, 0.012, 6, 40), brass); ring.rotation.x = Math.PI / 2; ring.position.y = y; cage.add(ring); }
  const dome = new THREE.Mesh(new THREE.SphereGeometry(R, 20, 8, 0, TAU, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xc9a85a, metalness: 0.7, roughness: 0.35, wireframe: true })); dome.position.y = H; cage.add(dome);
  // far glow (screen of consciousness) + bulb
  const glow = glowSprite(0x9fc8ff, 26, 0.85); glow.position.set(0, 4, -32); scene.add(glow);
  const glow2 = glowSprite(0xd8ecff, 8, 0.9); glow2.position.set(0, 4, -31); scene.add(glow2);
  const hemi = new THREE.HemisphereLight(0x8896c8, 0x1a1626, 0.7); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xa8c4ff, 1.3); key.position.set(0, 6, -20); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 50 }); scene.add(key);
  const vlight = new THREE.PointLight(0x9a7cff, 6, 7, 1.5); scene.add(vlight);
  const bulb = new THREE.PointLight(0xffc890, 3.5, 9, 1.6); bulb.position.set(-1.5, 3.4, 2.5); scene.add(bulb);
  const bulbS = glowSprite(0xffd8a0, 0.5, 0.9); bulbS.position.copy(bulb.position); scene.add(bulbS);
  return { scene, key, vlight, cage };
}

// ---------------------------------------------------------------- HUD (safe-zone guides)
function hud() {
  const c = document.createElement('canvas'); c.width = 360; c.height = 640;
  const g = c.getContext('2d');
  const line = (y, col) => { g.strokeStyle = col; g.lineWidth = 2; g.beginPath(); g.moveTo(0, y / 2); g.lineTo(360, y / 2); g.stroke(); };
  line(90, 'rgba(255,60,60,0.9)'); line(110, 'rgba(255,230,60,0.8)'); line(300, 'rgba(255,230,60,0.8)');
  line(850, 'rgba(255,255,255,0.5)'); line(880, 'rgba(60,230,255,0.9)'); line(1060, 'rgba(60,230,255,0.9)');
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
  m.renderOrder = 999; m.position.z = -0.3;
  const lab = document.createElement('canvas'); lab.width = 512; lab.height = 48;
  const lt = new THREE.CanvasTexture(lab); lt.colorSpace = THREE.SRGBColorSpace;
  const lm = new THREE.Mesh(new THREE.PlaneGeometry(1, 48 / 512), new THREE.MeshBasicMaterial({ map: lt, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
  lm.renderOrder = 1000;
  let last = '';
  return { m, lm, fit(cam, text) {
    const h = 2 * 0.3 * Math.tan(cam.fov * Math.PI / 360); m.scale.set(h * 0.5625, h, 1);
    lm.scale.set(h * 0.5625 * 0.95, h * 0.5625 * 0.95, 1); lm.position.set(0, -h * 0.47, -0.3);
    if (text !== last) { last = text; const g2 = lab.getContext('2d'); g2.clearRect(0, 0, 512, 48); g2.fillStyle = 'rgba(0,0,0,0.55)'; g2.fillRect(0, 0, 512, 48); g2.fillStyle = '#fff'; g2.font = 'bold 26px sans-serif'; g2.fillText(text, 10, 33); lt.needsUpdate = true; }
  } };
}


// ---------------------------------------------------------------- camera fitter (no rendering): find pos/look so
// world points land on target pixels. pts: [[Vector3, px, py, weight]]. Coordinate descent on (pos, look),
// pos regularised toward the guess. Returns { pos:[..], look:[..], err } (world).
function fitCam(pts, fov, pos0, look0, reg = 0.02, posFree = [1, 1, 1], yMin = -99, yMax = 99) {
  const cam = new THREE.PerspectiveCamera(fov, 720 / 1280, 0.05, 400);
  const P = [...pos0, ...look0];
  const cost = (q) => {
    cam.position.set(q[0], q[1], q[2]); cam.up.set(0, 1, 0); cam.lookAt(q[3], q[4], q[5]); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    let e = 0;
    for (const [w, x, y, wt = 1] of pts) {
      const v = w.clone().project(cam);
      if (v.z > 1) { e += 1e7; continue; }
      const sx = (v.x * 0.5 + 0.5) * 720, sy = (1 - (v.y * 0.5 + 0.5)) * 1280;
      e += wt * ((sx - x) ** 2 + (sy - y) ** 2);
    }
    for (let i = 0; i < 3; i++) e += reg * 1e4 * (q[i] - pos0[i]) ** 2;
    if (q[1] < yMin) e += 1e7 * (yMin - q[1]) ** 2; if (q[1] > yMax) e += 1e7 * (q[1] - yMax) ** 2;
    return e;
  };
  let best = cost(P), step = 0.5;
  for (let it = 0; it < 400 && step > 0.002; it++) {
    let improved = false;
    for (let i = 0; i < 6; i++) {
      if (i < 3 && !posFree[i]) continue;
      for (const d of [step, -step]) { const q = P.slice(); q[i] += d; const c = cost(q); if (c < best) { best = c; P.splice(0, 6, ...q); improved = true; } }
    }
    if (!improved) step *= 0.6;
  }
  return { pos: P.slice(0, 3), look: P.slice(3, 6), err: Math.sqrt(best / Math.max(1, pts.length)) };
}
const fmt = (a) => '[' + a.map((v) => v.toFixed(2)).join(', ') + ']';

// ---------------------------------------------------------------- setup
export async function setup(app) {
  const scene = new THREE.Scene();
  const edge = edgeStandIn(); const room = null;               // EDGE stand-in kept only for its galaxy sprite; real sets below
  const edgeSet = await app.set('EDGE'), roomSet = await app.set('BACKROOM');
  ROOM.fit(roomSet);
  edge.heightAt = (x, z) => edgeSet.groundAt(x, z);
  edgeSet.scene.add(edge.galaxy.mesh);
  const vd = await app.char('VOID'), js = await app.char('JESUS'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
  scene.add(vd.root, js.root, fear.root, mag.root);
  const user = userDummy(); scene.add(user.g);
  scene.add(app.camera);
  const H = hud(); app.camera.add(H.m); app.camera.add(H.lm);
  return { scene, edge, room, edgeSet, roomSet, vd, js, fear, mag, user, H, look: {} };
}

const LOG = (S, name, pts) => {
  const cam = CTX.camera;
  console.log(`[${name}] ` + Object.entries(pts).map(([k, p]) => `${k}=${p ? px(cam, p).join(',') : '-'}`).join('  '));
};



// ---------------------------------------------------------------- setups
export async function update(t, app, S) {
  const id = Math.floor(t + 1e-6);
  const isRoom = id >= 11;
  S.scene = isRoom ? S.roomSet.scene : S.edgeSet.scene;
  S.scene.add(S.vd.root, S.js.root, S.fear.root, S.mag.root, S.user.g, app.camera);
  S.fear.root.visible = isRoom; S.mag.root.visible = isRoom; S.user.g.visible = !isRoom;
  S.vd.root.visible = true; S.js.root.visible = !isRoom;
  const E = EDGE, M = E.M, R = ROOM, RM = R.M;
  let shot, label = '', tod = 0, vpose = null, jpose = null, logs = {};
  const vYaw = (m) => E.Y(m.yaw);
  S.look = { bloom: 0.55, bloomRadius: 0.55, bloomThreshold: 0.8, vignette: 0.18, warm: 0.3, exposure: 1.05, sat: 1.08 };

  const G = (lx, lz, dy = 0) => { const w = E.W(lx, 0, lz); w[1] = S.edge.heightAt(w[0], w[2]) + dy; return w; };   // local mark on terrain
  const head = (c) => c.anchor('head');
  const FIT = (pts, fov, posL, lookL, reg = 0.02, yMin = 0.3, yMax = 99) => {
    const r = fitCam(pts, fov, E.W(posL), E.W(lookL), reg, [1, 1, 1], yMin, yMax);
    console.log(`   FIT err ${r.err.toFixed(1)}px  pos(local) ${fmt(E.L(r.pos))}  look(local) ${fmt(E.L(r.look))}  fov ${fov}`);
    return { pos: r.pos, look: r.look, fov, drift: 0 };
  };
  if (id === 0) { // s01 frame 0 — the chase coming downhill at us, title in the sky
    label = 's01b01 FRAME 0';
    S.user.pose('run', G(2.35, -6.4), E.Y(0.2));
    vpose = { pos: G(3.3, -12.4), yaw: E.Y(-0.05), walk: { amount: 1, phase: 0.3, style: 'waddle' }, face: VX('hopeful', { mOpen: 0.15, mRound: 0.6 }),
      armL: { preset: 'wave', from: 'rest', mix: 0.6 }, armR: { preset: 'hold', from: 'rest', mix: 0.3 }, extra: { hem: 0.5 }, gaze: S.user.head() };
    S.vd.update(t, vpose);
    shot = E.cam('FRAME0', { drift: 0 });
    tod = 0;
  } else if (id === 1) { // s01b03 low wide: user small, Void towering
    label = 's01b03 low wide 24mm';
    S.user.pose('run', G(2.4, -6.6), E.Y(0.15));
    vpose = { pos: G(2.9, -9.4), yaw: E.Y(-0.05), walk: { amount: 1, phase: 0.55, style: 'waddle' }, face: VX('hopeful'), armL: { preset: 'wave', from: 'rest', mix: 0.5 }, extra: { hem: 0.5 } };
    S.vd.update(t, vpose);
    shot = E.cam('CHASELOW', { drift: 0 });
  } else if (id === 2) { // s02b02 Jesus appears at the bend, sun behind (reverse: camera upstage looking sunward)
    label = 's02b02 bend: Jesus appears';
    jpose = { pos: E.W(M.J0.p), yaw: vYaw(M.J0), face: 'content', armL: { preset: 'behind' }, armR: { preset: 'behind' }, head: { pitch: -0.2 } };
    S.vd.root.visible = false; S.user.g.visible = false;
    shot = E.cam('BEND', { drift: 0 });
  } else if (id === 3) { // s02b03 side two-shot: Jesus LEFT, user bursts in from the RIGHT (mirrored vs script)
    label = 's02b03 side 2-shot (mirrored)';
    S.user.pose('run', E.W(-0.75, 0, 0.8), E.Y(-0.74));
    jpose = { pos: E.W(M.J1.p), yaw: vYaw(M.J1) + 0.5, face: 'surprised', armL: { preset: 'behind' }, armR: { preset: 'behind' } };
    S.vd.root.visible = false;
    S.js.update(t, jpose);
    shot = E.cam('ARRIVE', { drift: 0 });
  } else if (id === 4) { // MASTER (s09b04 / s11b04): user lower-left, Jesus middle, Void upper-right
    label = 'MASTER 3-shot (s09b04)';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    jpose = { pos: E.W(M.JM.p), yaw: vYaw(M.JM), face: 'awkward', armL: { preset: 'clasp' }, armR: { preset: 'clasp' } };
    vpose = { pos: E.W(M.V.p), yaw: vYaw(M.V), face: VX('scowl'), armL: { preset: 'crossed' }, armR: { preset: 'crossed' }, gaze: S.user.head() };
    S.js.update(t, jpose); S.vd.update(t, vpose);
    shot = E.cam('MASTER', { drift: 0 });
    tod = 0.4;
  } else if (id === 5) { // OTS from behind the user (s08b05)
    label = 'OTS behind user (s08b05)';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    jpose = { pos: E.W(M.JV.p), yaw: vYaw(M.JV), face: 'hopeful', armL: { preset: 'clasp_chest' }, armR: { preset: 'clasp_chest' }, gaze: S.user.head() };
    vpose = { pos: E.W(M.V.p), yaw: vYaw(M.V), face: VX('scowl'), armL: { preset: 'crossed' }, armR: { preset: 'crossed' }, gaze: S.user.head() };
    S.js.update(t, jpose); S.vd.update(t, vpose);
    shot = E.cam('OTS', { drift: 0 });
    tod = 0.33;
  } else if (id === 6) { // WHISPER two-shot: the Void bent down to Jesus's LEFT ear (s07b02); solve Jesus's mark JW
    label = 'WHISPER 2-shot (s07b02)';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    const W = { pos: E.W(M.V.p), yaw: vYaw(M.V) - 0.15, ...whisperPose(-1, 1.25, 1), face: VX('whisper', { gazeYaw: 0.55 }), speech: false };
    S.vd.update(t, W); vpose = W;
    const A = S.vd.anchor('whisper');
    let jp = E.W(M.JV.p);
    const jbase = { yaw: vYaw(M.JV), face: 'listening', head: { roll: -0.12, yaw: 0.25 }, gaze: S.user.head() };
    for (let i = 0; i < 3; i++) { S.js.update(t, { ...jbase, pos: jp }); const e = S.js.anchor('earL'); jp = [jp[0] + A.x - e.x, 0, jp[2] + A.z - e.z]; }
    S.js.update(t, { ...jbase, pos: jp });
    console.log('   whisper: Jesus mark JW local', fmt(E.L(jp)), ' height err (mouth-ear)', (A.y - S.js.anchor('earL').y).toFixed(3));
    jpose = { ...jbase, pos: E.W(M.JV.p), yaw: vYaw(M.JV), armL: { preset: 'around', target: S.vd.anchor('sideR').clone().add(V3(0, 0.4, 0)) } };
    S.js.update(t, jpose);
    shot = E.cam('WHISPER', { drift: 0 });
  } else if (id === 7) { // user 3/4 lost profile looking frame-right at the pair (s06b01 / s03b02)
    label = 'USER 3/4 -> pair (s06b01)';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    jpose = { pos: E.W(M.JV.p), yaw: vYaw(M.JV), face: 'warm', gaze: S.user.head() };
    vpose = { pos: E.W(M.V.p), yaw: vYaw(M.V), face: VX('giggle'), extra: { laugh: 0.2 }, gaze: S.user.head() };
    S.js.update(t, jpose); S.vd.update(t, vpose);
    { const uh = S.user.head(); const fu = V3(...E.W(0.64, 0, -0.77)).sub(V3(...E.W(0, 0, 0))), ru = V3(...E.W(0.77, 0, 0.64)).sub(V3(...E.W(0, 0, 0)));
      const C = uh.clone().addScaledVector(fu, -1.25).addScaledVector(ru, 0.6).add(V3(0, 0.05, 0));
      const je = S.js.anchor('eyes'); const dU = uh.clone().sub(C).normalize(), dJ = je.clone().sub(C).normalize();
      console.log('   7: angle user<->Jesus from camera', (dU.angleTo(dJ) / DEG).toFixed(1), 'deg');
      const aim = C.clone().add(dU.clone().multiplyScalar(0.45).add(dJ.clone().multiplyScalar(0.55)).normalize().multiplyScalar(3));
      const r7 = fitCam([[uh, 220, 450], [je, 540, 330], [S.vd.anchor('eyes'), 640, 240, 0.3]], LENS[35], C.toArray(), aim.toArray(), 0.03, [1, 1, 1], 0.7, 1.4);
      console.log(`   FIT err ${r7.err.toFixed(1)}px  pos(local) ${fmt(E.L(r7.pos))}  look(local) ${fmt(E.L(r7.look))}`);
      shot = { pos: r7.pos, look: r7.look, fov: LENS[35], drift: 0 }; }
    tod = 0.2;
  } else if (id === 8) { // s13b06 two-shot: Jesus kneeling RIGHT, user LEFT, seated Void's back behind him
    label = 's13b06 2-shot kneel';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    jpose = { pos: E.W(M.K.p), yaw: vYaw(M.K), body: { kneel: 1 }, face: 'hopeful', armL: { preset: [['knee_rest', 0.6], ['open', 0.4]] }, armR: { preset: 'heart' }, gaze: S.user.head() };
    vpose = { pos: E.W(M.VSIT.p), yaw: vYaw(M.VSIT), body: { sit: 1 }, face: VX('sad'), armL: { preset: 'crossed' }, armR: { preset: 'crossed' } };
    S.js.update(t, jpose); S.vd.update(t, vpose);
    shot = E.cam('KNEEL2', { drift: 0 });
    tod = 0.48;
  } else if (id === 9) { // s12b01 from behind Jesus: hand on the seated Void's RIGHT shoulder
    label = 's12b01 hand on shoulder (behind J)';
    S.user.pose('sit', E.W(M.U.p), vYaw(M.U));
    vpose = { pos: E.W(M.VSIT.p), yaw: vYaw(M.VSIT), body: { sit: 1 }, face: VX('sad'), armL: { preset: 'crossed' }, armR: { preset: 'crossed' } };
    S.vd.update(t, vpose);
    const sh = S.vd.anchor('shoulderR');
    jpose = { pos: E.W(M.JS.p), yaw: vYaw(M.JS), face: 'tender', armR: { preset: 'shoulder', target: sh.clone().add(V3(0, 0.03, 0)), palm: [0, -1, 0] }, gaze: S.vd.anchor('head') };
    logs.shoulderR = sh;
    shot = E.cam('BEHINDJ', { drift: 0 });
    tod = 0.45;
  } else if (id === 10) { // s16b07 walk-off extreme wide, user on the lilac hill upper-left
    label = 's16b07 walk-off extreme wide';
    const hw = [EDGE.HILL_WORLD[0], 0, EDGE.HILL_WORLD[2]]; hw[1] = S.edge.heightAt(hw[0], hw[2]);
    S.user.pose('hug', hw, 2.84);
    const wp = [-1.2, 0, -20]; wp[1] = S.edge.heightAt(wp[0], wp[2]);
    jpose = { pos: [wp[0] - 0.65, wp[1], wp[2]], yaw: Math.PI, walk: { amount: 1, phase: 0.2 }, glow: 1.5 };
    vpose = { pos: [wp[0] + 0.6, wp[1], wp[2] - 0.1], yaw: Math.PI, walk: { amount: 1, phase: 0.6 }, extra: { rim: 1.8, eyeGlow: 1.2 } };
    S.js.update(t, jpose); S.vd.update(t, vpose);
    const r = fitCam([[S.user.head(), 180, 340], [S.js.anchor('head'), 340, 560], [S.vd.anchor('head'), 420, 540]], LENS[35], [0.9, 1.75, 3.5], [-1.8, 2.7, -22], 0.05, [1, 1, 1], 1.2, 2.4);
    console.log(`   FIT err ${r.err.toFixed(1)}px  pos(world) ${fmt(r.pos)}  look(world) ${fmt(r.look)}`);
    shot = { pos: r.pos, look: r.look, fov: LENS[35], drift: 0 };
    tod = 0.95;
  } else if (id === 11) { // BACKROOM master wide (s17b02 end): cage left, Void beside, corner right-back
    label = 'ROOM master wide (s17b02)';
    S.fear.update(t, { pos: R.W(RM.FIN.p), yaw: R.Y(RM.FIN.yaw), face: 'cry', body: { cower: 0.4 }, extra: { cry: 0.7 } });
    vpose = { pos: R.W(RM.V.p), yaw: R.Y(RM.V.yaw), face: VX('tender'), gaze: S.fear, body: { lean: 0.12 }, head: { pitch: 0.25 } };
    S.mag.update(t, { pos: R.W(RM.LURK.p), yaw: R.Y(RM.LURK.yaw), body: { crouch: 0.75 }, face: 'lurk' });
    S.vd.update(t, vpose);
    const r = fitCam([[S.fear.anchor('eyes'), 200, 700], [S.vd.anchor('eyes'), 390, 330], [V3(...S.roomSet.anchors.cornerCenter.toArray()), 610, 560, 0.3]], LENS[35], [-0.6, 1.8, 7.5], [0.3, 0.9, -1.5], 0.01, [1, 1, 1], 1.0, 2.6);
    console.log(`   FIT err ${r.err.toFixed(1)}px  ROOM local pos ${fmt(R.L(r.pos))} look ${fmt(R.L(r.look))}`);
    shot = { pos: r.pos, look: r.look, fov: LENS[35], drift: 0 };
    logs.mag = S.mag.anchor('head'); logs.fear = S.fear.anchor('eyes'); logs.corner = S.roomSet.anchors.cornerCenter.clone();
  } else if (id === 12) { // s20b03 wide at the kick wind-up: Fear lower-left, Void face top, magician leaning out at right
    label = 'ROOM kick wide (s20b03)';
    S.fear.update(t, { pos: R.W(RM.FOUT.p), yaw: R.Y(RM.FOUT.yaw), face: 'wonder', head: { pitch: -0.5 } });
    S.mag.update(t, { pos: R.W(RM.PEEK.p), yaw: R.Y(RM.PEEK.yaw), body: { lean: 0.55, hunch: 0.2, peek: 1.0, crouch: 0.15 }, face: 'gloat', armR: { preset: 'dagger_ready' }, gaze: S.fear });
    const chest = S.mag.anchor('chest');
    vpose = { pos: R.W(RM.V.p), yaw: R.Y(RM.V.yaw), head: { yaw: 0.35 }, face: VX('peripheral'), gaze: S.fear, extra: { kick: 1.0, kickSide: 'L', kickTarget: chest },
      armR: { preset: 'tip', target: R.W(1.0, 1.3, 0.55), reach: 1, tip: true } };
    S.vd.update(t, vpose);
    logs.magChest = chest; logs.kickFoot = S.vd.anchor('kickFoot'); logs.fearEyes = S.fear.anchor('eyes');
    console.log(`   kick err ${chest.distanceTo(S.vd.anchor('kickFoot')).toFixed(2)}m`);
    shot = R.cam('KICK', { drift: 0 });

  } else if (id === 13) { // s18b06 layered from behind: magician foreground right, Void flank middle, Fear far left
    label = 'ROOM layered from behind (s18b06)';
    S.fear.update(t, { pos: R.W(RM.FDOOR.p), yaw: R.Y(RM.FDOOR.yaw), face: 'sniffle', head: { pitch: -0.45 } });
    vpose = { pos: R.W(RM.V.p), yaw: R.Y(RM.V.yaw), face: VX('tender'), gaze: S.fear, body: { lean: 0.12 }, head: { pitch: 0.25 } };
    S.mag.update(t, { pos: R.W(RM.PEEK.p), yaw: R.Y(RM.PEEK.yaw), body: { crouch: 0.3, peek: 0.5 }, face: 'gloat', armR: { preset: 'dagger_ready' }, armL: { preset: 'pouch' }, gaze: S.fear });
    S.vd.update(t, vpose);
    const r = fitCam([[S.mag.anchor('head'), 540, 370], [S.fear.anchor('eyes'), 190, 600], [S.vd.anchor('eyes'), 330, 220, 0.2]], LENS[35], [4.9, 1.6, 1.6], [1.5, 1.0, 0.3], 0.03, [1, 1, 1], 1.1, 2.2);
    console.log(`   FIT err ${r.err.toFixed(1)}px  ROOM local pos ${fmt(R.L(r.pos))} look ${fmt(R.L(r.look))}`);
    shot = { pos: r.pos, look: r.look, fov: LENS[35], drift: 0 };
    logs.magHead = S.mag.anchor('head'); logs.fear = S.fear.anchor('eyes');
  } else if (id === 14) { // s17b01 opening drift from the screen side: cage + Void small and far ahead
    label = 'ROOM opening (s17b01)';
    S.fear.update(t, { pos: R.W(RM.FIN.p), yaw: R.Y(RM.FIN.yaw), face: 'cry', body: { cower: 0.4 }, extra: { cry: 0.7, glow: 1.5 } });
    vpose = { pos: R.W(RM.V.p), yaw: R.Y(RM.V.yaw), face: VX('tender'), gaze: S.fear, body: { lean: 0.12 }, head: { pitch: 0.25 }, extra: { rim: 1.6 } };
    S.mag.root.visible = false;
    S.vd.update(t, vpose);
    const r = fitCam([[S.fear.anchor('eyes'), 330, 640], [S.vd.anchor('eyes'), 420, 500]], LENS[35], [-6.0, 1.7, 10.0], [1.0, 1.0, -0.5], 0.02, [1, 1, 1], 1.2, 2.2);
    console.log(`   FIT err ${r.err.toFixed(1)}px  ROOM local pos ${fmt(R.L(r.pos))} look ${fmt(R.L(r.look))}`);
    shot = { pos: r.pos, look: r.look, fov: LENS[35], drift: 0 };
    logs.fear = S.fear.anchor('eyes');
  }

  applyShot(app.camera, shot, t);
  // EDGE sky / sun
  if (!isRoom) {
    S.edgeSet.update(t, { tod, voidSky: vpose ? 0.55 : 0, voidPos: vpose && vpose.pos ? vpose.pos : [0, 0, 0], clear: [[...[E.W(M.U.p)].map((w) => [w[0], w[2], 0.9])[0]]] });
    S.look = { ...S.edgeSet.look };
    S.edge.galaxy.begin();
    if (id >= 4) { const g = id === 10 ? E.GALAXY.to : E.GALAXY.from; S.edge.galaxy.add(g, E.GALAXY.size, 0xd8c0ff, 0.9, t * 0.2, CELL.galaxy); }
    S.edge.galaxy.end();
  } else {
    const v = R.W(RM.V.p);
    S.roomSet.update(t, { latch: id === 11 ? 0 : 1, cageDoor: id === 11 ? 0 : 1, voidLight: { pos: [v[0], 2.4, v[2]] } });
    S.look = { ...S.roomSet.look };
  }
  if (S.js.root.visible && jpose) S.js.update(t, jpose);
  else S.js.root.visible = false;
  if (vpose) S.vd.update(t, vpose); else S.vd.root.visible = false;
  S.H.fit(app.camera, `${id}: ${label}`);
  const pts = { ...logs };
  if (S.user.g.visible) pts.userHead = S.user.head();
  if (S.js.root.visible) { pts.jEyes = S.js.anchor('eyes'); pts.jMouth = S.js.anchor('mouth'); }
  if (S.vd.root.visible) { pts.vEyes = S.vd.anchor('eyes'); pts.vTop = S.vd.anchor('hoodTop'); }
  LOG(S, `${id} ${label}`, pts);
  if (S.vd.root.visible && !isRoom) console.log(`   void local ${E.L(S.vd.root.position).map((v) => v.toFixed(2))}  cam local ${E.L(app.camera.position).map((v) => v.toFixed(2))}`);
  if (isRoom) console.log(`   cam local ${R.L(app.camera.position).map((v) => v.toFixed(2))}`);
}
