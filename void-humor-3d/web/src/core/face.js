// FACE RIG — 3D eyes with real eyelids, swept brows, and a painted "face decal" (mouth, blush, tears) that
// conforms to the head surface. One Face per character head. See docs/FACE.md for the full API.
//
// Head-local space: origin = head centre, +Z = forward (out of the face), +Y = up, +X = the CHARACTER'S LEFT
// (screen-right when the character faces camera). Face surface coords: u = longitude from +Z toward +X
// (radians), v = latitude (radians, + up).
import * as THREE from 'three';
import { CTX, EYE_LIGHT } from './context.js';
import { SweepTube } from './limbs.js';
import { clamp, lerp, noise1, schedule, smooth, hash1 } from './util.js';

// ---------------------------------------------------------------------------------------------------------
// Eyeball shader
const EYE_VS = /* glsl */`
varying vec3 vObjN; varying vec3 vWorldN; varying vec3 vWorldPos;
void main(){
  vObjN = normal;
  vWorldN = normalize(mat3(modelMatrix) * normal);
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  gl_Position = projectionMatrix * viewMatrix * wp;
}`;
const EYE_FS = /* glsl */`
uniform vec3 uSclera, uIris, uIris2, uPupilC, uLimbal, uKeyDir, uKeyColor, uAmbient;
uniform float uIrisR, uPupilR, uGlowMode, uGlow, uWet;
varying vec3 vObjN; varying vec3 vWorldN; varying vec3 vWorldPos;
void main(){
  vec3 n = normalize(vObjN);
  float a = acos(clamp(n.z, -1.0, 1.0));
  float ang = atan(n.y, n.x);
  float fw = max(fwidth(a), 1e-4) * 1.2;
  vec3 col = uSclera * mix(1.0, 0.82, smoothstep(0.7, 1.6, a));
  float rr = clamp(a / uIrisR, 0.0, 1.0);
  float streak = 0.5 + 0.5 * sin(ang * 21.0 + sin(ang * 5.0) * 2.5);
  vec3 ic = mix(uIris2, uIris, smoothstep(0.2, 0.95, rr));
  ic *= 0.82 + 0.3 * streak * (1.0 - rr * 0.6);
  ic = mix(ic, uLimbal, smoothstep(0.8, 1.0, rr));
  float inIris = 1.0 - smoothstep(uIrisR - fw, uIrisR + fw, a);
  col = mix(col, ic, inIris);
  float inPupil = 1.0 - smoothstep(uPupilR - fw, uPupilR + fw, a);
  col = mix(col, uPupilC, inPupil);
  vec3 N = normalize(vWorldN);
  vec3 L = normalize(uKeyDir);
  float lam = max(dot(N, L), 0.0);
  vec3 lit = col * (uAmbient + uKeyColor * (0.3 + 0.7 * lam));
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 H = normalize(L + V);
  lit += uKeyColor * pow(max(dot(N, H), 0.0), 140.0) * (0.9 + uWet);
  lit = mix(lit, col * uGlow, uGlowMode);
  gl_FragColor = vec4(lit, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

function eyeMaterial(o) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uSclera: { value: new THREE.Color(o.sclera ?? 0xf4efe8) },
      uIris: { value: new THREE.Color(o.iris ?? 0x6a4428) },
      uIris2: { value: new THREE.Color(o.iris2 ?? o.irisInner ?? 0xc89a5a) },
      uPupilC: { value: new THREE.Color(o.pupilColor ?? 0x080506) },
      uLimbal: { value: new THREE.Color(o.limbal ?? 0x1c120b) },
      uIrisR: { value: o.irisR ?? 0.62 },
      uPupilR: { value: o.pupilR ?? 0.26 },
      uGlowMode: { value: o.glow ? 1 : 0 },
      uGlow: { value: o.glow ?? 0 },
      uWet: { value: 0 },
      uKeyDir: EYE_LIGHT.uKeyDir, uKeyColor: EYE_LIGHT.uKeyColor, uAmbient: EYE_LIGHT.uAmbient,
    },
    vertexShader: EYE_VS, fragmentShader: EYE_FS,
  });
}

// ---------------------------------------------------------------------------------------------------------
/**
 * Eye — eyeball (+Z forward) with upper/lower lid shells, lash lines and catchlights.
 * opts: radius, side ('L' = character's left, at +X), iris, iris2, irisR, pupilR, sclera, limbal, pupilColor,
 *       glow (number: emissive multiplier for glowing eyes, e.g. the Void), lidMaterial, lashColor, lash (0..2),
 *       lowerLash (0..1), scale [sx,sy,sz] (oval eyes), catchlight (0..1)
 */
export class Eye {
  constructor(o = {}) {
    this.o = o;
    const r = this.r = o.radius ?? 0.05;
    this.side = o.side ?? 'L';
    this.sx = this.side === 'L' ? 1 : -1;
    this.group = new THREE.Group();          // positioned/oriented by Face (rest pose)
    this.inner = new THREE.Group();          // non-uniform scale for oval eyes
    this.group.add(this.inner);
    if (o.scale) this.inner.scale.set(...o.scale);
    this.mat = eyeMaterial(o);
    this.ball = new THREE.Mesh(new THREE.SphereGeometry(r, 40, 28), this.mat);
    this.inner.add(this.ball);
    const lidMat = o.lidMaterial || new THREE.MeshStandardMaterial({ color: 0xd9a27e, roughness: 0.6 });
    const ru = r * (o.lidGapU ?? 1.045), rl = r * (o.lidGapL ?? 1.035);
    // upper lid: top hemisphere; lower lid: bottom hemisphere. pivot.rotation.x = -edgeElevation
    this.upRoll = new THREE.Group(); this.inner.add(this.upRoll);
    this.up = new THREE.Mesh(new THREE.SphereGeometry(ru, 36, 14, 0, Math.PI * 2, 0, Math.PI / 2), lidMat);
    this.upRoll.add(this.up);
    this.loRoll = new THREE.Group(); this.inner.add(this.loRoll);
    this.lo = new THREE.Mesh(new THREE.SphereGeometry(rl, 36, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), lidMat);
    this.loRoll.add(this.lo);
    const lashCol = new THREE.Color(o.lashColor ?? 0x24150e);
    const lash = o.lash ?? 1;
    if (lash > 0) {
      const lg = new THREE.TorusGeometry(ru, r * 0.05 * lash, 6, 32, Math.PI * 1.08);
      lg.rotateZ(-Math.PI * 0.04);
      const lm = new THREE.Mesh(lg, new THREE.MeshStandardMaterial({ color: lashCol, roughness: 0.7 }));
      lm.rotation.x = Math.PI / 2; // lie on the lid edge, covering the front half
      this.up.add(lm);
      // a little outer-corner flick
      const fl = new THREE.Mesh(new THREE.ConeGeometry(r * 0.06 * lash, r * 0.32 * lash, 6), lm.material);
      fl.position.set(this.sx * ru * 0.95, 0, ru * 0.25); fl.rotation.set(0, 0, -this.sx * 1.2);
      this.up.add(fl);
    }
    const ll = o.lowerLash ?? 0.35;
    if (ll > 0) {
      const lg2 = new THREE.TorusGeometry(rl, r * 0.03 * ll + 1e-4, 5, 28, Math.PI * 0.9);
      lg2.rotateZ(Math.PI * 0.05);
      const lm2 = new THREE.Mesh(lg2, new THREE.MeshStandardMaterial({ color: lashCol, roughness: 0.8, transparent: true, opacity: 0.6 }));
      lm2.rotation.x = Math.PI / 2;
      this.lo.add(lm2);
    }
    // catchlights (billboards placed toward the camera each frame)
    const cm = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95, depthWrite: false, toneMapped: false });
    this.catch1 = new THREE.Mesh(new THREE.CircleGeometry(r * 0.15, 16), cm);
    this.catch2 = new THREE.Mesh(new THREE.CircleGeometry(r * 0.065, 12), cm);
    this.catchK = o.catchlight ?? 1;
    this.inner.add(this.catch1, this.catch2);
  }

  /** yaw/pitch: eyeball rotation (rad). up/low: lid edge elevations (rad). tiltU/tiltL: lid roll (rad). */
  set({ yaw = 0, pitch = 0, up = 0.5, low = -0.6, tiltU = 0, tiltL = 0, pupil = 1, wet = 0 }) {
    this.ball.rotation.set(-pitch, yaw, 0, 'YXZ');
    this.up.rotation.x = -up;
    this.lo.rotation.x = -low;
    this.upRoll.rotation.z = tiltU;
    this.loRoll.rotation.z = tiltL;
    this.mat.uniforms.uPupilR.value = (this.o.pupilR ?? 0.26) * pupil;
    this.mat.uniforms.uWet.value = wet;
    // catchlights: on the cornea toward camera, offset up & toward the key light side
    const cam = CTX.camera;
    if (cam && this.catchK > 0) {
      this.inner.updateWorldMatrix(true, false);
      const inv = new THREE.Matrix4().copy(this.inner.matrixWorld).invert();
      const cl = cam.position.clone().applyMatrix4(inv).normalize();
      const upv = new THREE.Vector3(0, 1, 0), side = new THREE.Vector3().crossVectors(upv, cl).normalize();
      const d1 = cl.clone().addScaledVector(upv, 0.42).addScaledVector(side, -0.3).normalize();
      const d2 = cl.clone().addScaledVector(upv, -0.28).addScaledVector(side, 0.32).normalize();
      // hide when the lid covers that point (edge elevation test)
      const elev1 = Math.asin(clamp(d1.y)), elev2 = Math.asin(clamp(d2.y));
      this.catch1.visible = elev1 < up - 0.05 && elev1 > low + 0.05;
      this.catch2.visible = elev2 < up - 0.05 && elev2 > low + 0.05;
      this.catch1.position.copy(d1).multiplyScalar(this.r * 1.012);
      this.catch2.position.copy(d2).multiplyScalar(this.r * 1.012);
      this.catch1.lookAt(cam.position); this.catch2.lookAt(cam.position);
      this.catch1.material.opacity = 0.95 * this.catchK;
    }
  }
}

// ---------------------------------------------------------------------------------------------------------
// Surfaces
export function ellipsoidSurface(radii = [0.12, 0.13, 0.12], center = [0, 0, 0]) {
  const [rx, ry, rz] = radii;
  return (u, v) => {
    const cv = Math.cos(v);
    const p = new THREE.Vector3(rx * Math.sin(u) * cv + center[0], ry * Math.sin(v) + center[1], rz * Math.cos(u) * cv + center[2]);
    const q = p.clone().sub(new THREE.Vector3(...center));
    const n = new THREE.Vector3(q.x / (rx * rx), q.y / (ry * ry), q.z / (rz * rz)).normalize();
    return { p, n };
  };
}

// ---------------------------------------------------------------------------------------------------------
// Expression presets (flat numeric params). X('scared', {mOpen: 0.3}) -> full param object.
export const FACE_DEFAULTS = {
  lidU: 1, lidL: 0, lidAngry: 0, lidSad: 0, lidAsym: 0, pupil: 1, blink: 0, wet: 0, squint: 0,
  browIn: 0, browOut: 0, browMid: 0, browSq: 0, browAsym: 0,
  mOpen: 0, mWide: 0, mRound: 0, mSmile: 0, mAsym: 0, mTeethU: 0.85, mTeethL: 0.45, mClench: 0, mPress: 0,
  mTongue: 0.5, mPout: 0, mTremble: 0, mShift: 0,
  blush: 0, tearL: 0, tearR: 0,
  gazeYaw: 0, gazePitch: 0, saccade: 1, talk: 1, autoBlink: 1,
};

export const EXPR = {
  neutral: {},
  soft: { mSmile: 0.3, lidL: 0.12, browIn: 0.06 },
  happy: { mSmile: 0.8, lidL: 0.42, browIn: 0.15, browOut: 0.15, blush: 0.15 },
  grin: { mSmile: 0.95, mOpen: 0.22, mTeethU: 1, mTeethL: 0.2, lidL: 0.5, browIn: 0.2, browOut: 0.2 },
  laugh: { mSmile: 1, mOpen: 0.8, mTeethU: 1, mTeethL: 0.3, mTongue: 0.7, lidL: 0.8, lidU: 0.5, browIn: 0.4, browOut: 0.25, blush: 0.25 },
  giggle: { mSmile: 0.9, mOpen: 0.25, mTeethU: 0.9, lidL: 0.65, lidU: 0.65, browIn: 0.3, browOut: 0.1 },
  tender: { mSmile: 0.35, lidU: 0.86, lidL: 0.25, lidSad: 0.15, browIn: 0.35, browOut: -0.05 },
  sad: { mSmile: -0.55, mPout: 0.3, browIn: 0.75, browOut: -0.3, browSq: 0.15, lidSad: 0.6, lidU: 0.72 },
  sadSmile: { mSmile: 0.28, browIn: 0.62, browOut: -0.2, lidSad: 0.5, lidU: 0.78, lidL: 0.3 },
  scared: { lidU: 1.28, browIn: 0.85, browOut: 0.35, browSq: 0.35, lidSad: 0.3, mSmile: -0.4, mOpen: 0.14, mWide: 0.5, mTeethL: 0.6, pupil: 0.72 },
  terror: { lidU: 1.42, browIn: 1, browOut: 0.6, browSq: 0.45, lidSad: 0.25, mOpen: 0.55, mWide: 0.55, mSmile: -0.55, mTeethL: 0.8, mTeethU: 0.6, pupil: 0.55, mTremble: 0.5 },
  surprised: { lidU: 1.35, browIn: 0.7, browOut: 0.85, mOpen: 0.42, mRound: 0.45 },
  wtf: { lidU: 1.3, browIn: 0.35, browOut: 0.95, browAsym: 0.45, mOpen: 0.32, mWide: 0.25, mSmile: -0.35, mAsym: -0.2 },
  angry: { lidAngry: 0.7, lidU: 0.82, browIn: -0.85, browSq: 0.85, browOut: 0.3, mSmile: -0.45, mPress: 0.4 },
  scowl: { lidAngry: 0.9, lidU: 0.58, lidL: 0.35, browIn: -1, browSq: 1, browOut: 0.1, mSmile: -0.65, mPress: 0.65, mAsym: -0.15, mPout: 0.2 },
  awkward: { mClench: 1, mWide: 0.9, mSmile: 0.15, mAsym: 0.22, browIn: 0.75, browOut: 0.55, browAsym: 0.15, lidU: 1.15, lidSad: 0.2 },
  smug: { lidU: 0.62, lidL: 0.32, mSmile: 0.4, mAsym: 0.55, browAsym: 0.35, browSq: 0.15 },
  sideeye: { lidU: 0.58, lidL: 0.3, browIn: -0.25, browSq: 0.35, browAsym: -0.2, mPress: 0.35, mAsym: -0.25, mSmile: -0.15 },
  skeptical: { lidU: 0.7, lidL: 0.28, browAsym: 0.65, mPress: 0.4, mAsym: -0.3 },
  annoyed: { lidU: 0.55, lidL: 0.1, browIn: -0.25, browSq: 0.35, mPress: 0.5, mSmile: -0.3 },
  disgust: { browSq: 0.6, browIn: -0.4, lidL: 0.6, mSmile: -0.5, mAsym: 0.5, mOpen: 0.08, mWide: 0.4 },
  wonder: { lidU: 1.2, browIn: 0.6, browOut: 0.42, mOpen: 0.26, mRound: 0.32, pupil: 1.35, wet: 0.6 },
  hopeful: { lidU: 1.08, browIn: 0.5, browOut: 0.2, mSmile: 0.25, mOpen: 0.05, wet: 0.3 },
  worried: { browIn: 0.7, browOut: -0.1, browSq: 0.3, lidSad: 0.4, mSmile: -0.25, mPress: 0.25, lidU: 1.0 },
  guarded: { lidU: 0.78, lidL: 0.2, browIn: -0.1, browSq: 0.4, mPress: 0.55, mSmile: -0.2 },
  relieved: { mSmile: 0.4, lidU: 0.7, lidL: 0.25, browIn: 0.3, browOut: 0.1, mOpen: 0.05 },
  innocent: { lidU: 1.1, browIn: 0.45, browOut: 0.45, mSmile: 0.18, mPress: 0.3, mRound: 0.15 },
  hungry: { lidU: 0.6, lidL: 0.25, browSq: 0.3, mSmile: 0.7, mOpen: 0.18, mTongue: 1, mAsym: 0.3 },
};

export function X(name, over = {}) {
  const base = { ...FACE_DEFAULTS };
  const names = Array.isArray(name) ? name : [[name, 1]];
  if (typeof name === 'string') Object.assign(base, EXPR[name] || {});
  else for (const [nm, w] of names) for (const [key, val] of Object.entries(EXPR[nm] || {})) base[key] += (val - FACE_DEFAULTS[key]) * w;
  return Object.assign(base, over);
}

// ---------------------------------------------------------------------------------------------------------
/**
 * Face — the controller. Construct once per character; call update(t, params, {gaze, speech}) every frame.
 * cfg:
 *   head: THREE.Object3D (head-local space as described at the top)
 *   surface: (u,v)=>{p,n}   (default ellipsoid from cfg.radii/cfg.center)
 *   eyes: { u, v, radius, sink, splay, ...Eye opts }      (u,v = the LEFT eye; mirrored)
 *   brows: { color, material, thickness, lift, inner:[u,v], mid:[u,v], outer:[u,v], flatten } | null
 *   mouth: { v, halfW, line, interior, teeth, tongue, lipTint, lineW, drawInterior?(g, w, h, t) } (metres)
 *   decal: { uMin, uMax, vMin, vMax, size:[w,h], lift, material? }
 *   jaw: [uniform objects] (e.g. head material.userData.uJaw) driven by mouth opening, jawScale
 *   seed: int (blink/saccade schedule)
 */
export class Face {
  constructor(cfg) {
    this.cfg = cfg;
    this.head = cfg.head;
    this.surface = cfg.surface || ellipsoidSurface(cfg.radii, cfg.center);
    this.seed = cfg.seed ?? 1;
    // eyes
    const E = cfg.eyes;
    this.eyes = ['L', 'R'].map((side) => {
      const sx = side === 'L' ? 1 : -1;
      const eye = new Eye({ ...E, side });
      const { p, n } = this.surface(sx * E.u, E.v);
      const c = p.clone().addScaledVector(n, -E.radius * (E.sink ?? 0.55));
      eye.group.position.copy(c);
      eye.group.rotation.set(0, sx * (E.splay ?? 0.06), 0);
      this.head.add(eye.group);
      return eye;
    });
    // brows
    this.brows = null;
    if (cfg.brows) {
      const B = cfg.brows;
      const mat = B.material || new THREE.MeshStandardMaterial({ color: new THREE.Color(B.color ?? 0x3a2416), roughness: 0.8 });
      this.brows = ['L', 'R'].map((side) => {
        const tube = new SweepTube({ material: mat, segments: 14, radial: 8, capRings: 3 });
        this.head.add(tube.mesh);
        return { side, tube };
      });
    }
    // face decal
    this.decal = null;
    if (cfg.mouth) this._buildDecal();
    this.blinks = schedule(this.seed * 7 + 3, -5, 2000, 2.2, 5.6);
    this.sacc = schedule(this.seed * 13 + 5, -5, 2000, 0.35, 1.7);
    this._lastKey = '';
    this.state = { ...FACE_DEFAULTS };
  }

  _buildDecal() {
    const D = this.cfg.decal || {};
    const M = this.cfg.mouth;
    const uMin = D.uMin ?? -0.75, uMax = D.uMax ?? 0.75;
    const vMin = D.vMin ?? (M.v - 0.42), vMax = D.vMax ?? (this.cfg.eyes.v - 0.08);
    const [W, H] = D.size || [512, 384];
    const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H;
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    const nu = 28, nv = 20;
    const pos = [], uv = [], idx = [];
    const lift = D.lift ?? 0.0015;
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) {
      const u = lerp(uMin, uMax, i / nu), v = lerp(vMin, vMax, j / nv);
      const { p, n } = this.surface(u, v);
      p.addScaledVector(n, lift);
      pos.push(p.x, p.y, p.z); uv.push(i / nu, j / nv);
    }
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) {
      const a = j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx); g.computeVertexNormals();
    const mat = D.material || new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.55, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    if (D.material) D.material.map = tex;
    if (D.onMaterial) D.onMaterial(mat);
    const mesh = new THREE.Mesh(g, mat);
    mesh.renderOrder = 2;
    this.head.add(mesh);
    // canvas transform: draw in metres around the mouth centre, +y up
    const mid = this.surface(0, M.v);
    const rxEff = Math.abs(this.surface(0.1, M.v).p.x - this.surface(-0.1, M.v).p.x) / 0.2; // metres per radian of u at mouth
    const ryEff = Math.abs(this.surface(0, M.v + 0.05).p.y - this.surface(0, M.v - 0.05).p.y) / 0.1;
    this.decal = { canvas, ctx: canvas.getContext('2d'), tex, mesh, W, H, uMin, uMax, vMin, vMax, rxEff, ryEff, mid };
    // where the eyes are in decal metres (for tears / blush)
    const eu = this.cfg.eyes.u, ev = this.cfg.eyes.v;
    this.decal.eyeX = eu * rxEff; this.decal.eyeY = (ev - M.v) * ryEff;
  }

  // metres (relative to mouth centre, +y up) -> canvas px
  _xf(g) {
    const d = this.decal, M = this.cfg.mouth;
    const sx = d.W / ((d.uMax - d.uMin) * d.rxEff), sy = d.H / ((d.vMax - d.vMin) * d.ryEff);
    const ox = (0 - d.uMin) / (d.uMax - d.uMin) * d.W;
    const oy = (1 - (M.v - d.vMin) / (d.vMax - d.vMin)) * d.H;
    // canvas texture is flipped (uv.y up): image row 0 = top = vMax. flipY default true -> row 0 maps to v=1 (vMax). ok.
    g.setTransform(sx, 0, 0, -sy, ox, oy);
  }

  _drawDecal(p, t) {
    const d = this.decal, g = d.ctx, M = this.cfg.mouth;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, d.W, d.H);
    this._xf(g);
    const hw0 = M.halfW ?? 0.03;
    // ---- blush
    if (p.blush > 0.01) {
      for (const sx of [-1, 1]) {
        const cx = sx * (M.blushX ?? hw0 * 1.9), cy = M.blushY ?? hw0 * 1.1;
        const gr = g.createRadialGradient(cx, cy, 0, cx, cy, hw0 * 1.1);
        const bc = M.blushColor || '255,120,120';
        gr.addColorStop(0, `rgba(${bc},${0.45 * p.blush})`); gr.addColorStop(1, `rgba(${bc},0)`);
        g.fillStyle = gr; g.beginPath(); g.ellipse(cx, cy, hw0 * 1.2, hw0 * 0.8, 0, 0, Math.PI * 2); g.fill();
      }
    }
    // ---- tears (wet streaks from the lower lid)
    for (const [sx, amt] of [[1, p.tearL], [-1, p.tearR]]) {
      if (amt <= 0.01) continue;
      const x0 = sx * d.eyeX * 0.92, y0 = d.eyeY - (this.cfg.eyes.radius * 0.8);
      const len = amt * (y0 + hw0 * 1.5);
      g.lineCap = 'round';
      g.strokeStyle = `rgba(200,230,255,${0.55 * Math.min(1, amt * 2)})`; g.lineWidth = hw0 * 0.12;
      g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(x0 + sx * hw0 * 0.15, y0 - len * 0.5, x0 + sx * hw0 * 0.1, y0 - len); g.stroke();
      g.strokeStyle = `rgba(255,255,255,${0.7 * Math.min(1, amt * 2)})`; g.lineWidth = hw0 * 0.035;
      g.beginPath(); g.moveTo(x0 - hw0 * 0.02, y0); g.quadraticCurveTo(x0 + sx * hw0 * 0.13, y0 - len * 0.5, x0 + sx * hw0 * 0.08, y0 - len); g.stroke();
      g.fillStyle = `rgba(215,238,255,${0.8 * Math.min(1, amt * 2)})`;
      g.beginPath(); g.ellipse(x0 + sx * hw0 * 0.1, y0 - len, hw0 * 0.11, hw0 * 0.15, 0, 0, Math.PI * 2); g.fill();
    }
    // ---- mouth
    const open = clamp(p.mOpen, 0, 1.3) * (1 - clamp(p.close ?? 0));
    const round = clamp(p.mRound), wide = clamp(p.mWide, -1, 1), clench = clamp(p.mClench), press = clamp(p.mPress);
    const w = hw0 * (1 + 0.3 * wide) * (1 - 0.45 * round) * (1 + 0.22 * clench) * (1 - 0.18 * press);
    const smile = clamp(p.mSmile, -1, 1), asym = clamp(p.mAsym, -1, 1);
    const shift = (p.mShift || 0) * hw0 * 0.4;
    const yR = (smile * 0.62 - asym * 0.3) * hw0;   // character's right corner (screen-left, -x)
    const yL = (smile * 0.62 + asym * 0.3) * hw0;   // character's left corner (+x)
    let h = hw0 * 1.75 * open + round * hw0 * 0.7 * Math.min(1, open * 4);
    if (clench > 0.01) h = Math.max(h, hw0 * 0.42 * clench);
    const lineCol = M.line || '#5a2a22', lineW = (M.lineW ?? hw0 * 0.14) * (1 + press * 0.6);
    const cornerMid = (yL + yR) / 2;
    const xr = -w + shift, xl = w + shift;
    if (h < hw0 * 0.04) {
      // closed: a curved line (lens), corners tucked when smiling
      const cy = -smile * hw0 * 0.06;
      g.lineCap = 'round'; g.lineJoin = 'round';
      g.strokeStyle = lineCol; g.lineWidth = lineW;
      g.beginPath(); g.moveTo(xr, yR);
      g.bezierCurveTo(xr + w * 0.55, cy - (cornerMid) * 0.35 + (smile < 0 ? -smile * hw0 * 0.15 : 0), xl - w * 0.55, cy - cornerMid * 0.35 + (smile < 0 ? -smile * hw0 * 0.15 : 0), xl, yL);
      g.stroke();
      if (press > 0.05 || p.mPout > 0.05) {
        g.strokeStyle = `rgba(${M.lipTintRGB || '200,110,100'},${0.35 * Math.max(press, p.mPout)})`; g.lineWidth = hw0 * 0.18;
        g.beginPath(); g.moveTo(xr * 0.6, cornerMid - hw0 * 0.14); g.quadraticCurveTo(shift, -hw0 * (0.24 + 0.08 * p.mPout), xl * 0.6, cornerMid - hw0 * 0.14); g.stroke();
      }
    } else {
      const yTop = cornerMid * 0.35 + h * 0.3 + (smile < 0 ? -smile * hw0 * 0.1 : 0);
      const yBot = cornerMid * 0.2 - h * 0.7 - (smile > 0 ? smile * h * 0.35 : 0);
      const cxs = 0.45 + 0.45 * round;
      const path = () => {
        g.beginPath(); g.moveTo(xr, yR);
        g.bezierCurveTo(xr + w * (1 - cxs) + w * 0.1 * round, yTop, xl - w * (1 - cxs) - w * 0.1 * round, yTop, xl, yL);
        g.bezierCurveTo(xl - w * (1 - cxs - 0.1), yBot, xr + w * (1 - cxs - 0.1), yBot, xr, yR);
        g.closePath();
      };
      g.save(); path(); g.clip();
      if (M.drawInterior) M.drawInterior(g, { xr, xl, yTop, yBot, w, h, t });
      else {
        const gr = g.createLinearGradient(0, yTop, 0, yBot);
        gr.addColorStop(0, M.interior || '#2b0c12'); gr.addColorStop(1, M.interior2 || '#5a1b25');
        g.fillStyle = gr; g.fillRect(xr - 1, yBot - 1, w * 2 + 2, yTop - yBot + 2);
        // tongue
        if (p.mTongue > 0.02 && !clench) {
          g.fillStyle = M.tongue || '#d0606a';
          g.beginPath(); g.ellipse(shift, yBot + h * 0.12, w * 0.6, h * 0.38 * p.mTongue + hw0 * 0.05, 0, 0, Math.PI * 2); g.fill();
        }
      }
      const teeth = M.teeth || '#fbf7ef';
      if (clench > 0.01) {
        g.fillStyle = teeth; g.fillRect(xr - 1, yBot - 1, w * 2 + 2, yTop - yBot + 2);
        const midY = (yTop + yBot) / 2;
        g.strokeStyle = 'rgba(90,60,60,0.55)'; g.lineWidth = hw0 * 0.04;
        g.beginPath(); g.moveTo(xr, midY + (yR - cornerMid) * 0.3); g.quadraticCurveTo(shift, midY - smile * hw0 * 0.05, xl, midY + (yL - cornerMid) * 0.3); g.stroke();
        g.strokeStyle = 'rgba(120,100,100,0.25)'; g.lineWidth = hw0 * 0.02;
        for (let i = -3; i <= 3; i++) { const x = shift + i * w * 0.24; g.beginPath(); g.moveTo(x, yTop); g.lineTo(x, yBot); g.stroke(); }
      } else {
        const tu = clamp(p.mTeethU) * Math.min(1, h / (hw0 * 0.25));
        if (tu > 0.02) {
          g.fillStyle = teeth;
          const th = hw0 * 0.3 * tu;
          g.beginPath(); g.moveTo(xr, yTop + hw0); g.lineTo(xl, yTop + hw0);
          g.lineTo(xl, yTop - th * 0.6); g.quadraticCurveTo(shift, yTop - th * 1.15, xr, yTop - th * 0.6); g.closePath(); g.fill();
        }
        const tl = clamp(p.mTeethL) * Math.min(1, h / (hw0 * 0.45));
        if (tl > 0.02) {
          g.fillStyle = teeth;
          const th = hw0 * 0.2 * tl;
          g.beginPath(); g.moveTo(xr, yBot - hw0); g.lineTo(xl, yBot - hw0);
          g.lineTo(xl * 0.8, yBot + th * 0.7); g.quadraticCurveTo(shift, yBot + th * 1.2, xr * 0.8, yBot + th * 0.7); g.closePath(); g.fill();
        }
      }
      g.restore();
      // outline + lips
      g.lineJoin = 'round'; g.lineCap = 'round';
      g.strokeStyle = lineCol; g.lineWidth = lineW * 0.9; path(); g.stroke();
      // lower lip: soft fuller tint under the opening
      g.strokeStyle = `rgba(${M.lipTintRGB || '200,110,100'},0.28)`; g.lineWidth = hw0 * 0.16;
      g.beginPath(); g.moveTo(xr * 0.7 + shift * 0.3, yBot + (yR - yBot) * 0.3 - hw0 * 0.08);
      g.quadraticCurveTo(shift, yBot - hw0 * 0.14, xl * 0.7 + shift * 0.3, yBot + (yL - yBot) * 0.3 - hw0 * 0.08); g.stroke();
    }
    // corner dimples on smiles
    if (smile > 0.35) {
      const a = (smile - 0.35) / 0.65;
      g.strokeStyle = `rgba(90,40,30,${0.35 * a})`; g.lineWidth = hw0 * 0.06; g.lineCap = 'round';
      for (const [x, y, s] of [[xr, yR, -1], [xl, yL, 1]]) {
        g.beginPath(); g.moveTo(x + s * hw0 * 0.06, y + hw0 * 0.1); g.quadraticCurveTo(x + s * hw0 * 0.16, y, x + s * hw0 * 0.06, y - hw0 * 0.14); g.stroke();
      }
    }
    if (M.drawExtra) M.drawExtra(g, p, t);
    d.tex.needsUpdate = true;
  }

  /**
   * update(t, params, opts)
   *  params: flat face params (see FACE_DEFAULTS / X()). Per-side overrides: browInL/R, browOutL/R, lidUL/R, lidLL/R.
   *  opts.gaze: THREE.Vector3 (world) to look at, or null for straight ahead (+ gazeYaw/gazePitch offsets)
   *  opts.speech: { open, wide, round, close } lip-sync sample or null
   *  opts.blinkAt: [times] extra explicit blinks
   */
  update(t, params = {}, opts = {}) {
    const p = { ...FACE_DEFAULTS, ...params };
    // ---- speech blend
    const sp = opts.speech;
    if (sp && p.talk > 0) {
      const k = p.talk;
      const so = sp.open * k;
      p.mOpen = Math.max(p.mOpen * (1 - 0.5 * k), so * 0.9 + p.mOpen * 0.3 * k);
      p.mRound = lerp(p.mRound, sp.round, 0.75 * k);
      p.mWide = lerp(p.mWide, Math.max(p.mWide, sp.wide * 0.8), 0.6 * k);
      p.close = (sp.close || 0) * k;
      if (p.mClench > 0.3) p.mClench = Math.max(0, p.mClench - so * 0.8); // talk through gritted teeth
    }
    if (p.mTremble > 0) {
      p.mOpen = Math.max(0, p.mOpen + p.mTremble * 0.06 * noise1(t * 11, this.seed));
      p.mSmile += p.mTremble * 0.12 * noise1(t * 9, this.seed + 3);
    }
    // ---- blink
    let blink = p.blink;
    if (p.autoBlink > 0) {
      for (const bt of this.blinks) {
        if (bt > t) break;
        const dt = t - bt;
        if (dt < 0.22) blink = Math.max(blink, p.autoBlink * (dt < 0.06 ? dt / 0.06 : dt < 0.09 ? 1 : 1 - (dt - 0.09) / 0.13));
      }
    }
    for (const bt of opts.blinkAt || []) {
      const dt = t - bt;
      if (dt >= 0 && dt < 0.24) blink = Math.max(blink, dt < 0.07 ? dt / 0.07 : dt < 0.1 ? 1 : 1 - (dt - 0.1) / 0.14);
    }
    blink = clamp(blink);
    // ---- saccades (small stepwise gaze offsets, eased over ~40 ms)
    let sy = 0, spch = 0;
    if (p.saccade > 0) {
      let prev = -1e9, cur = -1e9, idx = 0;
      for (let i = 0; i < this.sacc.length; i++) { if (this.sacc[i] > t) break; prev = cur; cur = this.sacc[i]; idx = i; }
      const tgt = (i) => [(hash1(i * 31 + this.seed) - 0.5) * 0.07, (hash1(i * 17 + this.seed * 3) - 0.5) * 0.045];
      const a = tgt(idx - 1), b = tgt(idx);
      const u = smooth((t - cur) / 0.045);
      sy = lerp(a[0], b[0], u) * p.saccade; spch = lerp(a[1], b[1], u) * p.saccade;
    }
    // ---- eyes
    const E = this.cfg.eyes;
    this.head.updateWorldMatrix(true, false);
    for (const eye of this.eyes) {
      const sx = eye.sx;
      let yaw = p.gazeYaw, pitch = p.gazePitch;
      if (opts.gaze) {
        eye.group.updateWorldMatrix(true, false);
        const inv = new THREE.Matrix4().copy(eye.group.matrixWorld).invert();
        const dl = opts.gaze.clone().applyMatrix4(inv);
        yaw += Math.atan2(dl.x, Math.max(1e-4, dl.z));
        pitch += Math.atan2(dl.y, Math.hypot(dl.x, dl.z));
      }
      yaw = clamp(yaw + sy, -(E.maxYaw ?? 0.6), E.maxYaw ?? 0.6);
      pitch = clamp(pitch + spch, -(E.maxPitch ?? 0.45), E.maxPitch ?? 0.45);
      const side = sx > 0 ? 'L' : 'R';
      const lidU = (p['lidU' + side] ?? p.lidU) - (sx > 0 ? Math.max(0, p.lidAsym) : Math.max(0, -p.lidAsym)) * 0.5;
      const lidL = (p['lidL' + side] ?? p.lidL) + p.squint * 0.5;
      let low = lerp(E.lowRelaxed ?? -0.62, E.lowRaised ?? -0.08, clamp(lidL)) + pitch * 0.25;
      const openElev = E.upOpen ?? 0.5;
      let up = lidU <= 1 ? lerp(low + 0.04, openElev, clamp(lidU)) : lerp(openElev, E.upWide ?? 0.98, clamp((lidU - 1) / 0.42));
      up += pitch * 0.55;
      up = lerp(up, low + 0.03, blink);
      low = lerp(low, low + 0.06, blink);
      up = Math.max(up, low + 0.02);
      const tiltU = sx * (p.lidAngry - p.lidSad) * 0.36;
      const tiltL = sx * (p.lidAngry * 0.1 - p.lidSad * 0.05);
      eye.set({ yaw, pitch, up, low, tiltU, tiltL, pupil: p.pupil, wet: p.wet });
    }
    // ---- brows
    if (this.brows) {
      const B = this.cfg.brows;
      const th = B.thickness ?? 0.012, lift = B.lift ?? 0.004;
      for (const br of this.brows) {
        const sx = br.side === 'L' ? 1 : -1, sd = br.side;
        const asym = p.browAsym * sx;
        const inn = (p['browIn' + sd] ?? p.browIn) + asym * 0.5, out = (p['browOut' + sd] ?? p.browOut) + asym * 0.7;
        const mid = p.browMid, sq = clamp(p.browSq);
        const R = B.range ?? 0.1;
        const pIn = [B.inner[0] - sq * 0.05, B.inner[1] + inn * R - sq * 0.035];
        const pMid = [B.mid[0], B.mid[1] + (inn * 0.45 + out * 0.55) * R * 0.95 + mid * R * 0.5];
        const pOut = [B.outer[0], B.outer[1] + out * R * 0.8];
        const pA = [lerp(pIn[0], pMid[0], 0.5), lerp(pIn[1], pMid[1], 0.5) + (inn > 0.4 ? -0.01 : 0.004)];
        const uv = [pIn, pA, pMid, pOut];
        const pts = [], ups = [];
        for (const [u, v] of uv) { const { p: sp2, n } = this.surface(sx * u, v); pts.push(sp2.addScaledVector(n, lift + th * 0.25)); ups.push(n); }
        br.tube.update(pts, B.profile ? B.profile.map((f) => f * th) : [th * 0.75, th, th * 0.85, th * 0.45],
          { up: (s) => ups[Math.min(3, Math.round(s * 3))], flatten: B.flatten ?? 0.55 });
      }
    }
    // ---- face decal / mouth
    if (this.decal) {
      const key = ['mOpen', 'mWide', 'mRound', 'mSmile', 'mAsym', 'mTeethU', 'mTeethL', 'mClench', 'mPress', 'mTongue', 'mPout', 'blush', 'tearL', 'tearR', 'close', 'mShift']
        .map((kk) => (p[kk] || 0).toFixed(3)).join(',') + (this.cfg.mouth.animated ? t.toFixed(3) : '');
      if (key !== this._lastKey) { this._drawDecal(p, t); this._lastKey = key; }
    }
    // ---- jaw
    if (this.cfg.jaw) {
      const j = clamp(p.mOpen * (1 - clamp(p.close || 0))) * (this.cfg.jawScale ?? 1);
      for (const u of this.cfg.jaw) u.value = j;
    }
    this.state = p;
    return p;
  }
}
