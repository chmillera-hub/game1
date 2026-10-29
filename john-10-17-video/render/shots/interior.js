// Candlelit interiors: the upper room (John 17), lamps lighting one another, the Psalms
// scroll (Psalm 82, quoted in John 10:34) and the stone water jars of Cana (John 2).
import * as THREE from 'three';
import { setFog, gradientEnv } from '../lib/sky.js';
import { buildUpperRoom } from '../lib/architecture.js';
import { oilLamp, flame, dustField, stoneJar, lightBeam } from '../lib/props.js';
import { jesusFigure, crowdFigure, makeFigure } from '../lib/figure.js';
import { model, pbr, loadTexture } from '../lib/assets.js';
import { rng, v3, smooth, easeInOut, canvasTex, noise3 } from '../lib/util.js';

// Consonantal Masoretic text (no verse numbers, as written in a scroll).
const PS81_END = 'ולא שמע עמי לקולי וישראל לא אבה לי ואשלחהו בשרירות לבם ילכו במועצותיהם לו עמי שמע לי ישראל בדרכי יהלכו כמעט אויביהם אכניע ועל צריהם אשיב ידי משנאי יהוה יכחשו לו ויהי עתם לעולם ויאכילהו מחלב חטה ומצור דבש אשביעך';
const PS82 = [
  'מזמור לאסף אלהים נצב בעדת אל בקרב אלהים ישפט',
  'עד מתי תשפטו עול ופני רשעים תשאו סלה',
  'שפטו דל ויתום עני ורש הצדיקו',
  'פלטו דל ואביון מיד רשעים הצילו',
  'לא ידעו ולא יבינו בחשכה יתהלכו ימוטו כל מוסדי ארץ',
  'אני אמרתי אלהים אתם ובני עליון כלכם',
  'אכן כאדם תמותון וכאחד השרים תפלו',
  'קומה אלהים שפטה הארץ כי אתה תנחל בכל הגוים',
];
const PS83_START = 'שיר מזמור לאסף אלהים אל דמי לך אל תחרש ואל תשקט אל כי הנה אויביך יהמיון ומשנאיך נשאו ראש על עמך יערימו סוד ויתיעצו על צפוניך אמרו לכו ונכחידם מגוי ולא יזכר שם ישראל עוד';

async function scrollTexture() {
  const ff = new FontFace('FrankRuhl', 'url(/assets/fonts/FrankRuhlLibre%5Bwght%5D.ttf)', { weight: '300 900' });
  await ff.load(); document.fonts.add(ff);
  const W = 3072, H = 1280;
  let info = null;
  const tex = canvasTex(W, H, (g) => {
    // parchment
    const img = g.createImageData(W, H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const n = 0.5 + 0.3 * noise3(x / 220, y / 220, 1) + 0.15 * noise3(x / 40, y / 40, 2) + 0.05 * noise3(x / 6, y / 6, 3);
      const i = (y * W + x) * 4;
      img.data[i] = 205 + 40 * n; img.data[i + 1] = 178 + 38 * n; img.data[i + 2] = 128 + 30 * n; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    // faint ruling and ink
    g.direction = 'rtl'; g.textAlign = 'right'; g.textBaseline = 'alphabetic';
    const colW = 820, gap = 160, top = 170, lh = 58;
    const cols = [W - 150, W - 150 - colW - gap, W - 150 - 2 * (colW + gap)];
    const wrap = (text, maxW) => {
      const words = text.split(' '), lines = []; let cur = '';
      for (const w of words) { const t = cur ? cur + ' ' + w : w; if (g.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; }
      if (cur) lines.push(cur); return lines;
    };
    g.font = '600 44px FrankRuhl';
    const blocks = [wrap(PS81_END, colW), [], wrap(PS83_START, colW)];
    // Psalm 82 in the middle column, each verse flowing on; remember where verse 6 sits.
    let mid = [], hi = [];
    for (let v = 0; v < PS82.length; v++) { const L = wrap(PS82[v], colW); if (v === 5) hi = [mid.length, mid.length + L.length]; mid.push(...L); }
    blocks[1] = mid;
    blocks.forEach((lines, c) => {
      lines.forEach((ln, k) => {
        const y = top + k * lh;
        g.fillStyle = 'rgba(40,24,10,0.10)'; g.fillRect(cols[c] - colW, y + 10, colW, 1.5);
        g.fillStyle = c === 1 && k >= hi[0] && k < hi[1] ? 'rgba(18,10,4,0.98)' : 'rgba(26,16,8,0.92)';
        g.fillText(ln, cols[c], y);
      });
    });
    // age stains
    for (let i = 0; i < 26; i++) { const x = Math.random() * W, y = Math.random() * H, r = 60 + Math.random() * 220; const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(120,80,40,0.10)'); gr.addColorStop(1, 'rgba(120,80,40,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); }
    info = { hi, top, lh, cols, colW };
  });
  tex.userData = info;
  return tex;
}

function scrollMesh(tex, { width = 1.5, height = 0.62 } = {}) {
  const g = new THREE.Group();
  const seg = 80;
  const geo = new THREE.PlaneGeometry(width, height, seg, 8);
  const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i); p.setZ(i, 0.02 * Math.cos((x / width) * Math.PI) - 0.004 * Math.sin(x * 9)); }
  geo.computeVertexNormals();
  const parch = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.82, side: THREE.DoubleSide });
  const sheet = new THREE.Mesh(geo, parch); sheet.rotation.x = -Math.PI / 2; sheet.receiveShadow = true; g.add(sheet);
  const rollMat = new THREE.MeshStandardMaterial({ color: 0xcdb48a, roughness: 0.8 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x5a3a22, roughness: 0.55 });
  for (const sx of [-1, 1]) {
    const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, height * 0.98, 32), rollMat);
    roll.rotation.x = Math.PI / 2; roll.position.set(sx * (width / 2 + 0.06), 0.075, 0); roll.castShadow = roll.receiveShadow = true; g.add(roll);
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, height + 0.4, 12), wood);
    rod.rotation.x = Math.PI / 2; rod.position.set(sx * (width / 2 + 0.06), 0.075, 0); rod.castShadow = true; g.add(rod);
    for (const sz of [-1, 1]) {
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.018, 28), wood);
      disc.rotation.x = Math.PI / 2; disc.position.set(sx * (width / 2 + 0.06), 0.075, sz * (height / 2 + 0.02)); disc.castShadow = true; g.add(disc);
      const knob = new THREE.Mesh(new THREE.SphereGeometry(0.028, 12, 8), wood); knob.position.set(sx * (width / 2 + 0.06), 0.075, sz * (height / 2 + 0.2)); g.add(knob);
    }
  }
  return g;
}

export async function build({ params }) {
  const variant = params.variant || 'upper_room';
  const scene = new THREE.Scene();
  const R = rng(params.seed ?? 5);
  gradientEnv(scene, { top: 0x2a2018, bottom: 0x0c0806, intensity: 0.35 });
  scene.background = new THREE.Color(0x050302);
  setFog(scene, { color: 0x0e0905, density: 0.02, falloff: 0.0001 });
  const room = await buildUpperRoom(scene);
  const updaters = [];
  const cam = new THREE.PerspectiveCamera(params.fov ?? 34, 720 / 1280, 0.02, 200);
  let camPath, lookPath, focus = null, exposure = 1.0, look = 'candle';
  const woodMat = await pbr('wood_table_worn', { repeat: [1.5, 1], color: 0x9a7a5a, roughness: 0.75 });

  const table = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.08, 1.0), woodMat);
  table.castShadow = table.receiveShadow = true;
  const addTable = (y = 0.42, x = 0, z = -0.6) => {
    table.position.set(x, y, z); scene.add(table);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.08, y - 0.04, 0.08), woodMat); leg.position.set(x + sx * 1.15, (y - 0.04) / 2, z + sz * 0.4); leg.castShadow = true; scene.add(leg); }
  };
  const lampAt = async (x, y, z, { seed = 1, shadow = false, intensity = 1.1, dist = 5, yaw = 0 } = {}) => {
    const l = await oilLamp({ seed, lightIntensity: intensity, lightDistance: dist, shadow });
    l.position.set(x, y, z); l.rotation.y = yaw; scene.add(l); updaters.push((t) => l.userData.update(t)); return l;
  };

  if (variant === 'upper_room') {
    addTable(0.42, 0, -0.9);
    const buns = await model('hamburger_buns'); buns.position.set(-0.35, 0.46, -0.85); buns.scale.setScalar(1.2); scene.add(buns);
    const gob = await model('brass_goblets'); gob.position.set(0.3, 0.46, -0.95); gob.scale.setScalar(0.9); scene.add(gob);
    const plate = await model('carved_wooden_plate'); plate.position.set(-0.75, 0.46, -0.8); plate.scale.setScalar(0.8); scene.add(plate);
    const bowl = await model('wooden_bowl_01'); bowl.position.set(0.8, 0.46, -0.75); bowl.scale.setScalar(0.8); scene.add(bowl);
    const pot = await model('planter_pot_clay'); pot.position.set(-2.4, 0, -2.5); pot.scale.setScalar(1.4); scene.add(pot);
    await lampAt(-0.05, 0.46, -0.65, { seed: 1, shadow: true, intensity: 1.6, dist: 7 });
    await lampAt(0.95, 0.46, -1.05, { seed: 2, intensity: 0.9 });
    await lampAt(-1.05, 0.46, -1.0, { seed: 3, intensity: 0.9 });
    await lampAt(-3.2, 1.5, -3.4, { seed: 4, intensity: 0.6 });
    await lampAt(3.0, 1.5, -3.4, { seed: 5, intensity: 0.6 });
    const moon = new THREE.SpotLight(0x8aa0d0, 6, 12, 0.5, 0.7, 1.2); moon.position.set(2.4, 2.4, -3.6); moon.target.position.set(0.4, 0.8, -1.6); scene.add(moon, moon.target);
    const j = jesusFigure({ arms: { l: { pitch: 1.05, roll: 0.5, elbow: 0.55, wristPitch: -0.5 }, r: { pitch: 1.05, roll: 0.5, elbow: 0.55, wristPitch: -0.5 } }, headPitch: -0.5 });
    j.position.set(0.15, 0, -1.95); j.lookAt(0.15, 0, 3); scene.add(j);
    updaters.push((t) => j.userData.idle(t, 0.3));
    const seats = [[-1.55, -1.2], [-1.6, -0.35], [1.6, -1.15], [1.65, -0.3], [-0.9, 0.05], [0.9, 0.08], [-2.2, -0.8], [2.2, -0.7]];
    seats.forEach(([x, z], i) => {
      const f = makeFigure({ seed: 900 + i, pose: 'sit', robe: [0x6a5440, 0x7d6650, 0x5a4a3c, 0x846c52][i % 4], mantle: [0x4a3828, null, 0x3a3630, 0x5a4232][i % 4], head: i % 3 ? 'hair' : 'headcloth', headgear: 0xb8a888,
        arms: { l: { pitch: 0.7, elbow: 1.3 }, r: { pitch: 0.7, elbow: 1.3 } }, headPitch: -0.1 });
      f.position.set(x, 0, z); f.lookAt(0.15, 0, -1.95); scene.add(f); updaters.push((t) => f.userData.idle(t, 0.5));
    });
    camPath = (p) => v3(-3.15 + 0.35 * p, 1.08 + 0.05 * p, -1.25 - 0.2 * p);
    exposure = 1.3;
    lookPath = () => v3(0.25, 1.3, -1.85);
    focus = { distance: 2.8, range: 1.6, bokeh: 2.2 };
    scene.add(dustField({ count: 700, box: [[-2, 0.3, -3], [2, 2.6, 1]], size: 0.012, opacity: 0.35, color: 0xffd8a0 }));
  } else if (variant === 'lamp_lighting') {
    addTable(0.8, 0, -1.2);
    const lamps = [];
    for (let i = 0; i < 9; i++) {
      const l = await oilLamp({ seed: 20 + i, lightIntensity: i < 3 ? 0.9 : 0, lightDistance: 3.5, flameSize: 0.045 });
      l.position.set(-0.85 + i * 0.22 + R.range(-0.02, 0.02), 0.84, -0.85 - i * 0.05); l.rotation.y = 0.15 + R.range(-0.2, 0.2);
      scene.add(l); lamps.push(l);
    }
    // a hand-held lamp (lit) passes its flame along the row: each lamp ignites in turn
    updaters.push((t, p) => lamps.forEach((l, i) => {
      const on = smooth(0.08 + i * 0.1, 0.13 + i * 0.1, p);
      const fl = l.userData.flame; fl.userData.update(t);
      fl.children[0].scale.set(0.045 * on, 0.09 * on, 1);
      if (fl.userData.light) fl.userData.light.intensity *= on;
    }));
    camPath = (p) => v3(-0.95 + 0.9 * p, 0.95, -0.3 - 0.05 * p);
    lookPath = (p) => v3(-0.55 + 0.9 * p, 0.88, -0.95);
    focus = { distance: 0.75, range: 0.35, bokeh: 3.0 };
    exposure = 1.25;
    scene.add(dustField({ count: 500, box: [[-1.5, 0.8, -1.6], [1.5, 1.8, -0.2]], size: 0.006, opacity: 0.3, color: 0xffd0a0 }));
  } else if (variant === 'scroll_a' || variant === 'scroll_b') {
    addTable(0.85, 0, -1.0);
    const tex = await scrollTexture();
    const sc = scrollMesh(tex); sc.position.set(0, 0.9, -1.0); sc.rotation.y = 0; scene.add(sc);
    await lampAt(0.95, 0.89, -0.75, { seed: 7, shadow: true, intensity: 1.8, dist: 6 });
    await lampAt(-1.05, 0.89, -1.25, { seed: 8, intensity: 0.7 });
    const key = new THREE.SpotLight(0xffc890, variant === 'scroll_b' ? 7 : 4, 6, 0.32, 0.8, 1.5);
    key.position.set(-0.6, 2.6, -0.3); key.target.position.set(0, 0.9, -1.0); scene.add(key, key.target);
    const d = tex.userData; // highlight position of Psalm 82:6 in the middle column (uv -> local)
    const hx = (d.cols[1] - d.colW / 2) / 3072 - 0.5, hz = ((d.top + (d.hi[0] + 0.5) * d.lh) / 1280) - 0.5;
    const target = v3(hx * 1.5, 0.92, -1.0 + hz * 0.62);
    if (variant === 'scroll_a') {
      camPath = (p) => v3(0.55 - 0.45 * p, 1.55 - 0.08 * p, -0.25 - 0.1 * p);
      lookPath = (p) => v3(0.25 - 0.25 * p, 0.9, -1.0);
      focus = { distance: 1.1, range: 0.6, bokeh: 2.2 };
    } else {
      const glow = lightBeam({ from: target.clone().add(v3(-0.5, 1.6, 0.4)), to: target.clone().add(v3(0.05, -0.1, -0.03)), width: 0.34, height: 0.12, intensity: 0.0, color: 0xffd8a0, fadeStart: 0.1, fadeEnd: 0.95, softness: 0.48, noise: 0.4 });
      scene.add(glow);
      updaters.push((t, p) => { glow.userData.uniforms.intensity.value = 0.25 * smooth(0.1, 0.6, p); glow.userData.uniforms.time.value = t; });
      camPath = (p) => target.clone().add(v3(0.12 - 0.1 * p, 0.42 - 0.06 * p, 0.32 - 0.05 * p));
      lookPath = () => target.clone();
      focus = { distance: 0.5, range: 0.2, bokeh: 3.0 };
    }
    exposure = 1.15;
    scene.add(dustField({ count: 600, box: [[-1.2, 0.9, -1.6], [1.2, 2.2, -0.2]], size: 0.007, opacity: 0.35, color: 0xffd8a0 }));
  } else if (variant === 'jars') {
    look = 'warm';
    const stone = await pbr('rock_boulder_dry', { repeat: [1.5, 1.5], color: 0xe8dcc8, roughness: 0.9 });
    const jars = [], wine = [];
    for (let i = 0; i < 6; i++) {
      const jr = stoneJar({ height: R.range(0.78, 0.9), seed: 40 + i, mat: stone });
      const x = -1.3 + i * 0.52 + R.range(-0.04, 0.04), z = -1.5 - (i % 2) * 0.12;
      jr.position.set(x, 0, z); scene.add(jr); jars.push(jr);
      jr.geometry.computeBoundingBox();
      const top = jr.geometry.boundingBox.max.y - 0.06;
      const m = new THREE.MeshPhysicalMaterial({ color: 0x5c6c70, roughness: 0.05, metalness: 0.0, envMapIntensity: 1.2, clearcoat: 1, clearcoatRoughness: 0.05 });
      const disc = new THREE.Mesh(new THREE.CircleGeometry(0.115, 32), m); disc.rotation.x = -Math.PI / 2; disc.position.set(x, top, z); scene.add(disc);
      wine.push({ m, i });
    }
    const sunBeam = new THREE.SpotLight(0xffd8a8, 30, 14, 0.45, 0.6, 1.2); sunBeam.position.set(-3, 4.2, 1.5); sunBeam.target.position.set(0, 0.6, -1.5);
    sunBeam.castShadow = true; sunBeam.shadow.mapSize.set(1024, 1024); sunBeam.shadow.bias = -0.0005; scene.add(sunBeam, sunBeam.target);
    const shaft = lightBeam({ from: v3(-3, 4.2, 1.5), to: v3(0.3, 0.0, -1.6), width: 1.2, height: 1.0, intensity: 0.12, color: 0xffd8a8, fadeStart: 0.1, fadeEnd: 0.9, softness: 0.45 });
    scene.add(shaft);
    scene.add(new THREE.HemisphereLight(0xffe0c0, 0x2a1c12, 0.25));
    const W = new THREE.Color(0x5c6c70), Wn = new THREE.Color(0x4a0a16);
    updaters.push((t, p) => { wine.forEach(({ m, i }) => { const k = smooth(0.15 + i * 0.1, 0.35 + i * 0.1, p); m.color.copy(W).lerp(Wn, k); }); shaft.userData.uniforms.time.value = t; });
    camPath = (p) => v3(-0.9 + 1.1 * p, 1.95 - 0.1 * p, 0.05);
    lookPath = (p) => v3(-0.5 + 0.8 * p, 0.62, -1.5);
    focus = { distance: 2.0, range: 1.2, bokeh: 2.2 };
    exposure = 1.0;
    scene.add(dustField({ count: 900, box: [[-2, 0.2, -2.5], [1.5, 3, 0.5]], size: 0.01, opacity: 0.45, color: 0xffe0b0 }));
  }

  return {
    scene, camera: cam,
    post: { look, dof: focus, exposure, bloom: { intensity: 1.0, threshold: 0.7 }, vignette: { darkness: 0.72, offset: 0.28 } },
    update(t, p) {
      cam.position.copy(camPath(p)); cam.lookAt(lookPath(p));
      scene.traverse((o) => { if (o.userData && o.userData.uniforms && o.userData.uniforms.time) o.userData.uniforms.time.value = t; });
      updaters.forEach((u) => u(t, p));
    },
  };
}
