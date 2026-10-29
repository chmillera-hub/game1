// Architecture kits: Solomon's Colonnade (temple courts), Jerusalem skyline, upper room.
import * as THREE from 'three';
import { pbr } from './assets.js';
import { rng, noise3 } from './util.js';

function columnShaftGeometry(h = 8, r0 = 0.47, r1 = 0.41, flutes = 24) {
  const g = new THREE.CylinderGeometry(r1, r0, h, flutes * 4, 12, true);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const th = Math.atan2(z, x);
    const ent = 1 + 0.025 * Math.sin(((y / h) + 0.5) * Math.PI); // entasis
    const k = 1 - 0.035 * Math.pow(0.5 + 0.5 * Math.cos(th * flutes), 2.2);
    p.setXYZ(i, x * k * ent, y + h / 2, z * k * ent);
  }
  // UVs: wrap around once, tile vertically
  const uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 2.0, uv.getY(i) * 5.0);
  g.computeVertexNormals();
  return g;
}
function lathe(points, seg = 48) { return new THREE.LatheGeometry(points.map(([x, y]) => new THREE.Vector2(x, y)), seg); }
function columnBaseGeometry() {
  return lathe([[0, 0], [0.62, 0], [0.62, 0.2], [0.6, 0.22], [0.6, 0.24], [0.66, 0.3], [0.62, 0.38], [0.55, 0.42], [0.53, 0.48], [0.56, 0.52], [0.52, 0.58], [0.48, 0.6], [0, 0.6]]);
}
function columnCapitalGeometry() {
  // necking, bell with leaf-like lobes, abacus
  const g = lathe([[0, 0], [0.43, 0], [0.46, 0.04], [0.43, 0.08], [0.45, 0.2], [0.52, 0.45], [0.62, 0.66], [0.7, 0.75], [0.72, 0.8], [0, 0.8]], 64);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (y > 0.12 && y < 0.76) {
      const th = Math.atan2(z, x);
      const lobe = 0.035 * Math.pow(Math.abs(Math.cos(th * 4)), 3) * Math.sin(((y - 0.12) / 0.64) * Math.PI) + 0.012 * Math.cos(th * 16) * ((y - 0.12) / 0.64);
      const s = 1 + lobe / Math.max(0.3, Math.hypot(x, z));
      p.setXYZ(i, x * s, y, z * s);
    }
  }
  g.computeVertexNormals();
  return g;
}

// Colonnade along Z. Inner row at x = 0 faces the open court (x > 0); second row at x = -6; back wall at x = -11.
export async function buildColonnade(scene, { zFrom = -84, zTo = 24, spacing = 4, colH = 8.2, sanctuary = true, court = true } = {}) {
  const out = {};
  const stone = await pbr('old_sandstone_02', { repeat: [1, 1], color: 0xfff6e8, roughness: 0.85, normalScale: 0.6 });
  const stoneCol = await pbr('old_sandstone_02', { repeat: [1, 1], color: 0xfff3e2, roughness: 0.8, normalScale: 0.45 });
  const floorMat = await pbr('marble_tiles', { repeat: [40, 40], color: 0xf0e4d0, roughness: 0.75, normalScale: 0.7 });
  const wallMat = await pbr('large_sandstone_blocks', { repeat: [14, 2], color: 0xf2e2c8, roughness: 0.9 });
  const woodMat = await pbr('rough_wood', { repeat: [8, 1], color: 0x8a6a4c, roughness: 0.85 });
  const beamWood = await pbr('rough_wood', { repeat: [1, 6], color: 0x7a5a3e, roughness: 0.85 });

  const L = zTo - zFrom;
  const rows = [0, -6];
  const zs = [];
  for (let z = zFrom; z <= zTo; z += spacing) zs.push(z);
  out.columnZ = zs;
  const n = zs.length * rows.length;
  const shaft = new THREE.InstancedMesh(columnShaftGeometry(colH - 1.4), stoneCol, n);
  const base = new THREE.InstancedMesh(columnBaseGeometry(), stone, n);
  const cap = new THREE.InstancedMesh(columnCapitalGeometry(), stone, n);
  const abacus = new THREE.InstancedMesh(new THREE.BoxGeometry(1.5, 0.22, 1.5), stone, n);
  const plinth = new THREE.InstancedMesh(new THREE.BoxGeometry(1.3, 0.22, 1.3), stone, n);
  const m4 = new THREE.Matrix4();
  let k = 0;
  for (const x of rows) for (const z of zs) {
    base.setMatrixAt(k, m4.makeTranslation(x, 0.2, z));
    plinth.setMatrixAt(k, m4.makeTranslation(x, 0.11, z));
    shaft.setMatrixAt(k, m4.makeTranslation(x, 0.8, z));
    cap.setMatrixAt(k, m4.makeTranslation(x, colH - 0.6, z));
    abacus.setMatrixAt(k, m4.makeTranslation(x, colH + 0.31, z));
    k++;
  }
  for (const im of [shaft, base, cap, abacus, plinth]) { im.castShadow = true; im.receiveShadow = true; im.instanceMatrix.needsUpdate = true; scene.add(im); }
  out.rows = rows;

  // Entablature beams over each row, ceiling, roof edge.
  const top = colH + 0.42;
  for (const x of rows) {
    const arch = new THREE.Mesh(new THREE.BoxGeometry(1.25, 1.1, L + 4), stone);
    arch.position.set(x, top + 0.55, (zFrom + zTo) / 2); arch.castShadow = arch.receiveShadow = true; scene.add(arch);
  }
  const cornice = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.35, L + 4), stone);
  cornice.position.set(0.25, top + 1.28, (zFrom + zTo) / 2); cornice.castShadow = cornice.receiveShadow = true; scene.add(cornice);
  const ceiling = new THREE.Mesh(new THREE.BoxGeometry(13, 0.3, L + 4), woodMat);
  ceiling.position.set(-5.5, top + 1.25, (zFrom + zTo) / 2); ceiling.castShadow = true; ceiling.receiveShadow = true; scene.add(ceiling);
  const nb = Math.floor(L / 2);
  const beams = new THREE.InstancedMesh(new THREE.BoxGeometry(12.2, 0.42, 0.34), beamWood, nb);
  for (let i = 0; i < nb; i++) beams.setMatrixAt(i, m4.makeTranslation(-5.5, top + 0.92, zFrom + i * 2 + 1));
  beams.castShadow = true; beams.receiveShadow = true; scene.add(beams);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(14, 0.6, L + 4), stone);
  roof.position.set(-5.2, top + 1.7, (zFrom + zTo) / 2); roof.castShadow = true; scene.add(roof);

  // Back wall with ashlar blocks.
  const wall = new THREE.Mesh(new THREE.BoxGeometry(1.2, top + 2.2, L + 4), wallMat);
  wall.position.set(-11.6, (top + 2.2) / 2, (zFrom + zTo) / 2); wall.receiveShadow = true; wall.castShadow = true; scene.add(wall);

  // Floor (colonnade + court).
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(240, 240), floorMat);
  floor.rotation.x = -Math.PI / 2; floor.position.set(60, 0, -30); floor.receiveShadow = true; scene.add(floor);
  // Raised step along the court edge.
  const step = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.0, L + 4), stone);
  step.position.set(0.9, 0.0, (zFrom + zTo) / 2); scene.add(step);

  if (sanctuary) {
    // Distant sanctuary: tall white limestone facade with a dark portal and gilded trim, seen through haze.
    const facadeMat = await pbr('white_sandstone_blocks_02', { repeat: [6, 8], color: 0xfff8ee, roughness: 0.7 });
    const gold = new THREE.MeshStandardMaterial({ color: 0xd8a848, metalness: 1, roughness: 0.32 });
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(24, 44, 50), facadeMat); body.position.set(0, 22, 0); g.add(body);
    const wingL = new THREE.Mesh(new THREE.BoxGeometry(14, 30, 60), facadeMat); wingL.position.set(6, 15, 0); g.add(wingL);
    const portal = new THREE.Mesh(new THREE.BoxGeometry(0.5, 22, 9), new THREE.MeshStandardMaterial({ color: 0x1a120a, roughness: 1 }));
    portal.position.set(-12.1, 15, 0); g.add(portal);
    const trim = new THREE.Mesh(new THREE.BoxGeometry(0.6, 1.0, 50.5), gold); trim.position.set(-12.2, 43.6, 0); g.add(trim);
    const trim2 = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 9.8), gold); trim2.position.set(-12.3, 26.5, 0); g.add(trim2);
    for (let i = -4; i <= 4; i++) { // gilded spikes along the roof line
      const sp = new THREE.Mesh(new THREE.ConeGeometry(0.25, 1.6, 6), gold); sp.position.set(-12, 45, i * 5.5); g.add(sp);
    }
    g.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = true; } });
    // Placed across the court away from the low sun so backlit views stay clean.
    g.position.set(62, 0, 46);
    g.rotation.y = -0.5;
    scene.add(g);
    out.sanctuary = g;
  }
  out.top = top;
  return out;
}

// ---------- Jerusalem skyline on a hill (for establishing shots) ----------
export async function buildJerusalem(scene, { x = 0, z = -380, scale = 1, seed = 5 } = {}) {
  const r = rng(seed);
  const wallMat = await pbr('white_sandstone_blocks_02', { repeat: [6, 1], color: 0xf0dcc0, roughness: 0.9 }).catch(() => null)
    || await pbr('large_sandstone_blocks', { repeat: [4, 1], color: 0xf0dcc0 });
  const houseMat = await pbr('clay_plaster', { repeat: [1, 1], color: 0xe8d4b8, roughness: 0.95 });
  const g = new THREE.Group();
  // city wall with towers along a ridge
  const wall = new THREE.Mesh(new THREE.BoxGeometry(260, 14, 4), wallMat); wall.position.set(0, 7, 40); g.add(wall);
  for (let i = -6; i <= 6; i++) { const t = new THREE.Mesh(new THREE.BoxGeometry(9, 22, 9), wallMat); t.position.set(i * 21, 11, 40); g.add(t); }
  // houses: many boxes on the slope
  const hg = new THREE.BoxGeometry(1, 1, 1);
  const N = 420;
  const houses = new THREE.InstancedMesh(hg, houseMat, N);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
  for (let i = 0; i < N; i++) {
    const hx = r.range(-120, 120), hz = r.range(-60, 36);
    const ground = 6 + 10 * Math.exp(-((hx / 90) ** 2)) - hz * 0.15;
    const w = r.range(5, 11), h = r.range(5, 12), d = r.range(5, 11);
    p.set(hx, ground + h / 2, hz); s.set(w, h, d); q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), r.range(-0.15, 0.15));
    houses.setMatrixAt(i, m4.compose(p, q, s));
  }
  g.add(houses);
  // temple platform and sanctuary
  const plat = new THREE.Mesh(new THREE.BoxGeometry(110, 26, 80), wallMat); plat.position.set(-40, 13, -10); g.add(plat);
  const sanct = new THREE.Mesh(new THREE.BoxGeometry(22, 34, 38), new THREE.MeshStandardMaterial({ color: 0xfff4e4, roughness: 0.6 })); sanct.position.set(-40, 26 + 17, -14); g.add(sanct);
  const gold = new THREE.MeshStandardMaterial({ color: 0xe0b050, metalness: 1, roughness: 0.3, emissive: 0x3a2508 });
  const roofTrim = new THREE.Mesh(new THREE.BoxGeometry(22.5, 1.2, 38.5), gold); roofTrim.position.set(-40, 60.5, -14); g.add(roofTrim);
  const porch = new THREE.Mesh(new THREE.BoxGeometry(40, 30, 6), new THREE.MeshStandardMaterial({ color: 0xfff4e4, roughness: 0.6 })); porch.position.set(-40, 41, 6); g.add(porch);
  const portal = new THREE.Mesh(new THREE.BoxGeometry(8, 18, 0.5), new THREE.MeshStandardMaterial({ color: 0x2a1a0c, roughness: 1 })); portal.position.set(-40, 37, 9.1); g.add(portal);
  // colonnades on the platform edge (as thin dark/light stripes)
  for (let i = 0; i < 26; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 9, 8), wallMat); c.position.set(-93 + i * 4.2, 30.5, 28); g.add(c); }
  const stoaRoof = new THREE.Mesh(new THREE.BoxGeometry(110, 1.5, 6), wallMat); stoaRoof.position.set(-40, 35.5, 28); g.add(stoaRoof);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  g.position.set(x, 0, z); g.scale.setScalar(scale);
  scene.add(g);
  return g;
}

// ---------- upper room (plaster walls, beams, low table) ----------
export async function buildUpperRoom(scene) {
  const out = {};
  const wallMat = await pbr('clay_plaster', { repeat: [3, 2], color: 0xd8c2a4, roughness: 0.95 });
  const floorMat = await pbr('clay_floor_001', { repeat: [4, 4], color: 0xc8b090, roughness: 0.9 });
  const beamMat = await pbr('rough_wood', { repeat: [1, 4], color: 0x5a4030, roughness: 0.85 });
  const W = 9, D = 7, H = 3.4;
  const room = new THREE.Group();
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(W, D), floorMat); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; room.add(floor);
  const mkWall = (w, h, x, z, ry) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat); m.position.set(x, h / 2, z); m.rotation.y = ry; m.receiveShadow = true; room.add(m); return m; };
  mkWall(W, H, 0, -D / 2, 0);
  mkWall(D, H, -W / 2, 0, Math.PI / 2);
  mkWall(D, H, W / 2, 0, -Math.PI / 2);
  mkWall(W, H, 0, D / 2, Math.PI);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, D), beamMat); ceil.rotation.x = Math.PI / 2; ceil.position.y = H; room.add(ceil);
  for (let i = 0; i < 6; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(W, 0.22, 0.2), beamMat); b.position.set(0, H - 0.11, -D / 2 + 0.7 + i * 1.12); b.castShadow = true; room.add(b); }
  // small window high on the back wall (moonlight)
  const win = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.9), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.25, 0.32, 0.5) }));
  win.position.set(2.4, 2.3, -D / 2 + 0.01); room.add(win);
  out.window = win;
  // niches with lamps along the walls are placed by the shot
  scene.add(room);
  out.room = room; out.size = { W, D, H };
  return out;
}
