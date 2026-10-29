// Earth from space (city lights at night, sunrise over the limb) and the cosmos
// ("before the creation of the world"). Earth imagery: NASA Blue/Black Marble (public domain).
import * as THREE from 'three';
import { loadTexture } from '../lib/assets.js';
import { rng, v3, smooth, easeInOut } from '../lib/util.js';

const earthVert = `
varying vec2 vUv; varying vec3 vN; varying vec3 vP;
void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position,1.0); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const earthFrag = `
uniform sampler2D dayMap, nightMap, specMap; uniform vec3 sunDir; uniform float nightGain;
varying vec2 vUv; varying vec3 vN; varying vec3 vP;
void main(){
  vec3 n = normalize(vN); float ndl = dot(n, sunDir);
  float dayAmt = smoothstep(-0.1, 0.22, ndl);
  vec3 day = texture2D(dayMap, vUv).rgb; vec3 night = texture2D(nightMap, vUv).rgb; float spec = texture2D(specMap, vUv).r;
  vec3 V = normalize(cameraPosition - vP); vec3 H = normalize(sunDir + V);
  float sp = pow(max(dot(n, H), 0.0), 70.0) * spec * dayAmt;
  vec3 col = day * max(ndl, 0.0) * 1.7 + sp * vec3(1.0, 0.85, 0.6) * 1.4;
  col += pow(night, vec3(1.4)) * vec3(1.0, 0.72, 0.42) * nightGain * (1.0 - dayAmt);
  col *= mix(vec3(1.0), vec3(1.25, 0.78, 0.55), smoothstep(0.35, 0.0, abs(ndl)) * dayAmt);
  gl_FragColor = vec4(col, 1.0);
}`;
const cloudFrag = `
uniform sampler2D cloudMap; uniform vec3 sunDir; uniform float time;
varying vec2 vUv; varying vec3 vN; varying vec3 vP;
void main(){ vec3 n = normalize(vN); float ndl = dot(n, sunDir);
  float a = texture2D(cloudMap, vUv + vec2(time * 0.0015, 0.0)).r;
  float lit = smoothstep(-0.12, 0.3, ndl);
  vec3 c = vec3(1.0, 0.97, 0.92) * (0.05 + 1.4 * max(ndl, 0.0)) * mix(vec3(1.0), vec3(1.3, 0.75, 0.5), smoothstep(0.3, 0.0, abs(ndl)) * lit);
  gl_FragColor = vec4(c, a * (0.25 + 0.75 * lit) * 0.9); }`;
const atmoFrag = `
uniform vec3 sunDir; varying vec3 vN; varying vec3 vP;
void main(){ vec3 n = normalize(vN); vec3 V = normalize(cameraPosition - vP);
  float fres = pow(1.0 - max(dot(n, V), 0.0), 2.4);
  float s = dot(n, sunDir); float lit = smoothstep(-0.35, 0.35, s);
  vec3 c = mix(vec3(1.0, 0.55, 0.25), vec3(0.35, 0.62, 1.0), smoothstep(-0.05, 0.5, s));
  gl_FragColor = vec4(c * fres * lit * 2.2, 1.0); }`;

function starField(scene, { count = 9000, radius = 900, seed = 3, size = 1.6 } = {}) {
  const r = rng(seed);
  const pos = new Float32Array(count * 3), col = new Float32Array(count * 3), sz = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const u = r() * 2 - 1, a = r() * Math.PI * 2, s = Math.sqrt(1 - u * u);
    pos.set([Math.cos(a) * s * radius, u * radius, Math.sin(a) * s * radius], i * 3);
    const t = r(); col.set(t < 0.15 ? [1.0, 0.8, 0.6] : t < 0.3 ? [0.75, 0.85, 1.0] : [1, 0.97, 0.92], i * 3);
    sz[i] = Math.pow(r(), 6) * 4 + 0.6;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.setAttribute('sz', new THREE.BufferAttribute(sz, 1));
  const m = new THREE.ShaderMaterial({
    uniforms: { size: { value: size }, time: { value: 0 } },
    vertexShader: `attribute float sz; attribute vec3 color; varying vec3 vC; uniform float size, time;
      void main(){ vC = color * (0.8 + 0.2 * sin(time * 2.0 + position.x)); vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_PointSize = size * sz; gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying vec3 vC; void main(){ float d = length(gl_PointCoord - 0.5); gl_FragColor = vec4(vC * smoothstep(0.5, 0.0, d) * 1.6, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
  });
  const p = new THREE.Points(g, m); p.userData.uniforms = m.uniforms; p.frustumCulled = false; scene.add(p); return p;
}

const nebulaFrag = `
uniform float time; varying vec3 vDir;
float hash(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float vn(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z); }
float fbm(vec3 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++){ s += a * vn(p); p = p * 2.03 + 1.7; a *= 0.5; } return s; }
void main(){
  vec3 d = normalize(vDir);
  vec3 q = d * 2.2 + vec3(0.0, 0.0, time * 0.01);
  float n1 = fbm(q + fbm(q * 1.7) * 0.9);
  float n2 = fbm(q * 2.6 + 4.0);
  float band = exp(-pow((d.y + 0.15 * sin(d.x * 3.0)) * 2.6, 2.0));
  float dens = smoothstep(0.42, 0.85, n1) * (0.35 + 0.9 * band);
  vec3 c = mix(vec3(0.08, 0.04, 0.16), vec3(0.62, 0.3, 0.42), smoothstep(0.45, 0.75, n1));
  c = mix(c, vec3(1.0, 0.72, 0.38), smoothstep(0.62, 0.9, n2) * band);
  vec3 col = c * dens * 1.4 + vec3(0.01, 0.008, 0.02);
  float dark = smoothstep(0.55, 0.8, fbm(q * 3.1 + 9.0));
  col *= 1.0 - 0.6 * dark * band;
  gl_FragColor = vec4(col, 1.0);
}`;

export async function build({ params }) {
  const variant = params.variant || 'earth_night';
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);
  const cam = new THREE.PerspectiveCamera(params.fov ?? 36, 720 / 1280, 0.1, 5000);
  const updaters = [];
  let camPath, lookPath, exposure = 1.0, bloom = { intensity: 1.1, threshold: 0.65 };
  const stars = starField(scene, {});
  updaters.push((t) => { stars.userData.uniforms.time.value = t; });

  if (variant === 'earth_night' || variant === 'earth_sunrise') {
    const day = await loadTexture('/assets/earth/day_5400.jpg', { srgb: true });
    const night = await loadTexture('/assets/earth/night_3600.jpg', { srgb: true });
    const spec = await loadTexture('/assets/earth/spec_2048.jpg');
    const clouds = await loadTexture('/assets/earth/clouds_2048_nasa.jpg');
    for (const t of [day, night, spec, clouds]) { t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.ClampToEdgeWrapping; t.anisotropy = 8; }
    const Rr = 10;
    // Rotate the globe so Israel (31.8N, 35.2E) faces +Z toward the camera rig.
    const lon = THREE.MathUtils.degToRad(35.2), lat = THREE.MathUtils.degToRad(31.8);
    const israel = v3(Math.cos(Math.PI + lon) * -1 * Math.cos(lat), Math.sin(lat), Math.sin(Math.PI + lon) * Math.cos(lat));
    const earth = new THREE.Group(); scene.add(earth);
    const q = new THREE.Quaternion().setFromUnitVectors(israel.clone().normalize(), v3(0, 0, 1));
    earth.quaternion.copy(q);
    const sunDir = variant === 'earth_night' ? v3(-0.25, 0.55, -1).normalize() : v3(0.1, 0.36, -1).normalize();
    const U = { dayMap: { value: day }, nightMap: { value: night }, specMap: { value: spec }, cloudMap: { value: clouds }, sunDir: { value: sunDir }, time: { value: 0 }, nightGain: { value: variant === 'earth_night' ? 3.2 : 2.2 } };
    const globe = new THREE.Mesh(new THREE.SphereGeometry(Rr, 128, 96), new THREE.ShaderMaterial({ uniforms: U, vertexShader: earthVert, fragmentShader: earthFrag }));
    earth.add(globe);
    const cl = new THREE.Mesh(new THREE.SphereGeometry(Rr * 1.008, 96, 72), new THREE.ShaderMaterial({ uniforms: U, vertexShader: earthVert, fragmentShader: cloudFrag, transparent: true, depthWrite: false }));
    earth.add(cl);
    const atmo = new THREE.Mesh(new THREE.SphereGeometry(Rr * 1.035, 96, 72), new THREE.ShaderMaterial({ uniforms: U, vertexShader: earthVert, fragmentShader: atmoFrag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.FrontSide }));
    earth.add(atmo);
    const halo = new THREE.Mesh(new THREE.SphereGeometry(Rr * 1.07, 96, 72), new THREE.ShaderMaterial({
      uniforms: U, vertexShader: earthVert, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.BackSide,
      fragmentShader: `uniform vec3 sunDir; varying vec3 vN; varying vec3 vP; void main(){ vec3 n = normalize(vN); vec3 V = normalize(cameraPosition - vP);
        float f = pow(max(0.0, 1.0 + dot(n, V)) , 0.0) * pow(1.0 - abs(dot(n, V)), 6.0); float lit = smoothstep(-0.4, 0.4, dot(n, sunDir));
        gl_FragColor = vec4(mix(vec3(1.0,0.5,0.2), vec3(0.4,0.65,1.0), lit) * f * (0.2 + lit) * 1.6, 1.0); }`,
    }));
    earth.add(halo);
    updaters.push((t) => { U.time.value = t; earth.rotation.y = 0; earth.quaternion.copy(q); earth.rotateOnWorldAxis(v3(0, 1, 0), 0.006 * t); });
    if (variant === 'earth_night') {
      camPath = (p) => v3(0.6 - 0.8 * p, 8.5 + 0.6 * p, 22 - 1.5 * p);
      lookPath = (p) => v3(0, 3.5 + 0.4 * p, 0);
      exposure = 1.1;
    } else {
      // the sun rises over the limb; its light sweeps across the globe
      const sun = new THREE.Mesh(new THREE.SphereGeometry(6, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(30, 24, 16) }));
      scene.add(sun);
      const s0 = v3(0.1, 0.3, -1).normalize(), s1 = v3(0.1, 0.62, -1).normalize();
      updaters.push((t, p) => { const k = easeInOut(p); sunDir.copy(s0).lerp(s1, k).normalize(); sun.position.copy(sunDir).multiplyScalar(900); });
      camPath = (p) => v3(0.4 - 0.5 * p, 7.6 + 0.5 * p, 21 - 1.2 * p);
      lookPath = (p) => v3(0, 6.5 + 0.6 * p, 0);
      exposure = 1.0;
      bloom = { intensity: 1.3, threshold: 0.8 };
    }
  } else if (variant === 'cosmos') {
    const neb = new THREE.Mesh(new THREE.SphereGeometry(1500, 64, 32), new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } }, side: THREE.BackSide, depthWrite: false,
      vertexShader: 'varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: nebulaFrag,
    }));
    scene.add(neb);
    // nearby star particles streaming past
    const near = starField(scene, { count: 2500, radius: 60, seed: 9, size: 5 });
    near.geometry.attributes.position.array.forEach((_, i, a) => { if (i % 3 === 2) a[i] = a[i] * 3 - 60; });
    // the light of glory
    const glow = new THREE.Mesh(new THREE.SphereGeometry(2, 32, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(9, 7.5, 5) }));
    glow.position.set(0, 2, -260); scene.add(glow);
    const rays = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 }, amt: { value: 0 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: `uniform float time, amt; varying vec2 vUv; void main(){ vec2 p = vUv - 0.5; float r = length(p); float a = atan(p.y, p.x);
        float rays = pow(0.5 + 0.5 * sin(a * 14.0 + time * 0.3) * sin(a * 5.0 - time * 0.2), 3.0);
        float c = exp(-r * 9.0) * 1.5 + rays * exp(-r * 5.0) * 0.9; gl_FragColor = vec4(vec3(1.0, 0.85, 0.6) * c * amt, 1.0); }`,
    }));
    rays.scale.set(200, 200, 1); rays.position.copy(glow.position); scene.add(rays);
    updaters.push((t, p) => {
      neb.material.uniforms.time.value = t; near.userData.uniforms.time.value = t;
      rays.material.uniforms.time.value = t; rays.material.uniforms.amt.value = 0.25 + 1.6 * smooth(0.25, 1.0, p);
      glow.scale.setScalar(1 + 2.5 * smooth(0.3, 1.0, p));
      rays.lookAt(cam.position);
    });
    camPath = (p) => v3(0, 0, 40 - 70 * p);
    lookPath = (p) => v3(0, 2, -260);
    exposure = 1.0;
  }

  return {
    scene, camera: cam,
    post: { look: 'space', dof: null, exposure, bloom, vignette: { darkness: 0.6 } },
    update(t, p) { cam.position.copy(camPath(p)); cam.lookAt(lookPath(p)); updaters.forEach((u) => u(t, p)); },
  };
}
