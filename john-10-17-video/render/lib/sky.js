// Photographed HDRI skies on a dome, matching image-based lighting, and a global
// height fog with sun-facing haze that every material picks up.
import * as THREE from 'three';
import { loadHDR } from './assets.js';

// ---------- global fog (patched into three's shader chunks) ----------
export const FOG = {
  uFogDensity: { value: 0.01 },
  uFogHeightFalloff: { value: 0.03 },
  uFogBase: { value: 0 },
  uSunDir: { value: new THREE.Vector3(0, 1, 0) },
  uSunHaze: { value: new THREE.Color(0, 0, 0) },
  uSunHazePow: { value: 8 },
};
THREE.ShaderChunk.fog_pars_vertex = `
#ifdef USE_FOG
  varying float vFogDepth;
  varying vec3 vFogWorldPos;
#endif`;
THREE.ShaderChunk.fog_vertex = `
#ifdef USE_FOG
  vFogDepth = - mvPosition.z;
  vec4 fogWP = vec4( transformed, 1.0 );
  #ifdef USE_INSTANCING
    fogWP = instanceMatrix * fogWP;
  #endif
  vFogWorldPos = ( modelMatrix * fogWP ).xyz;
#endif`;
THREE.ShaderChunk.fog_pars_fragment = `
#ifdef USE_FOG
  uniform vec3 fogColor;
  varying float vFogDepth;
  varying vec3 vFogWorldPos;
  uniform float uFogDensity;
  uniform float uFogHeightFalloff;
  uniform float uFogBase;
  uniform float uSunHazePow;
  uniform vec3 uSunDir;
  uniform vec3 uSunHaze;
  #ifdef FOG_EXP2
    uniform float fogDensity;
  #else
    uniform float fogNear;
    uniform float fogFar;
  #endif
#endif`;
THREE.ShaderChunk.fog_fragment = `
#ifdef USE_FOG
  vec3 fogRay = vFogWorldPos - cameraPosition;
  float fogDist = length( fogRay );
  float hf = max( uFogHeightFalloff, 1e-4 );
  float h0 = cameraPosition.y - uFogBase;
  float h1 = vFogWorldPos.y - uFogBase;
  float dh = h1 - h0;
  float avgDen = abs( dh ) > 1e-3 ? ( exp( -hf * h0 ) - exp( -hf * h1 ) ) / ( hf * dh ) : exp( -hf * h0 );
  float fogFactor = 1.0 - exp( -uFogDensity * fogDist * max( avgDen, 0.0 ) );
  vec3 fogV = fogRay / max( fogDist, 1e-4 );
  vec3 fogC = fogColor + uSunHaze * pow( max( dot( fogV, uSunDir ), 0.0 ), uSunHazePow );
  gl_FragColor.rgb = mix( gl_FragColor.rgb, fogC, clamp( fogFactor, 0.0, 1.0 ) );
#endif`;
export function addFogUniforms(shader) { Object.assign(shader.uniforms, FOG); }
THREE.Material.prototype.onBeforeCompile = function (shader) { addFogUniforms(shader); };

export function setFog(scene, { color = 0xc8a882, density = 0.01, falloff = 0.03, base = 0, sunDir = null, sunHaze = 0x000000, sunHazePow = 8 } = {}) {
  scene.fog = new THREE.FogExp2(new THREE.Color(color), 0.0);
  FOG.uFogDensity.value = density;
  FOG.uFogHeightFalloff.value = falloff;
  FOG.uFogBase.value = base;
  if (sunDir) FOG.uSunDir.value.copy(sunDir).normalize();
  FOG.uSunHaze.value.set(sunHaze);
  FOG.uSunHazePow.value = sunHazePow;
}

// ---------- sun direction inside an HDRI ----------
const sunCache = new Map();
export function hdrSunDir(tex) {
  if (sunCache.has(tex)) return sunCache.get(tex);
  const { data, width, height } = tex.image;
  const half = data instanceof Uint16Array;
  const f = half ? THREE.DataUtils.fromHalfFloat : (x) => x;
  let best = -1, bi = 0;
  for (let y = 0; y < height / 2; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const l = 0.2126 * f(data[i]) + 0.7152 * f(data[i + 1]) + 0.0722 * f(data[i + 2]);
      if (l > best) { best = l; bi = y * width + x; }
    }
  }
  const px = bi % width, py = Math.floor(bi / width);
  const u = (px + 0.5) / width, v = 1 - (py + 0.5) / height;
  const phi = (u - 0.5) * 2 * Math.PI, th = (v - 0.5) * Math.PI;
  const d = new THREE.Vector3(Math.cos(phi) * Math.cos(th), Math.sin(th), Math.sin(phi) * Math.cos(th));
  sunCache.set(tex, d);
  return d;
}

// Yaw that places the HDRI's sun at the requested world azimuth (radians, atan2(x, z) convention).
export function yawForSun(tex, azimuth) {
  const d = hdrSunDir(tex);
  return azimuth - Math.atan2(d.x, d.z);
}

// ---------- sky dome ----------
const skyVert = `
varying vec3 vDir;
void main() {
  vDir = (modelMatrix * vec4(position, 0.0)).xyz;
  vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  gl_Position = p.xyww;
}`;
const skyFrag = `
uniform sampler2D map;
uniform mat3 rot;
uniform float exposure, saturation, hazeAmount, hazeTop, hazeBottom, sunDisk, sunGlow, sunGlowPow, sunSize, starAmount, gradeMix, clampMax;
uniform vec3 tint, hazeColor, sunDir, sunColor, zenithTint;
uniform float time;
varying vec3 vDir;
#define PI 3.141592653589793
vec2 equirectUv(vec3 d) {
  float u = atan(d.z, d.x) * (0.5 / PI) + 0.5;
  float v = asin(clamp(d.y, -1.0, 1.0)) * (1.0 / PI) + 0.5;
  return vec2(u, v);
}
float hash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
void main() {
  vec3 d = normalize(vDir);
  vec3 c = min(texture2D(map, equirectUv(rot * d)).rgb, vec3(clampMax));
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, saturation) * tint * exposure;
  c *= mix(vec3(1.0), zenithTint, smoothstep(0.1, 0.9, d.y));
  float hz = 1.0 - smoothstep(hazeBottom, hazeTop, d.y);
  c = mix(c, hazeColor, hz * hazeAmount);
  float cs = dot(d, normalize(sunDir));
  c += sunColor * (sunGlow * pow(max(cs, 0.0), sunGlowPow) + sunDisk * smoothstep(cos(sunSize * 1.15), cos(sunSize), cs));
  if (starAmount > 0.0) {
    vec3 q = d * 900.0;
    vec3 cell = floor(q);
    float h = hash(cell);
    float tw = 0.65 + 0.35 * sin(time * 2.0 + h * 50.0);
    float s = step(0.9965, h) * smoothstep(0.0, 0.25, d.y) * tw;
    c += vec3(0.85, 0.9, 1.0) * s * starAmount * (0.4 + 2.0 * fract(h * 91.7));
  }
  gl_FragColor = vec4(c, 1.0);
}`;

export async function makeSky(scene, {
  hdri, res = '4k', yaw = 0, sunAzimuth = null, exposure = 1, saturation = 1, tint = 0xffffff, zenithTint = 0xffffff,
  haze = 0xd8b890, hazeAmount = 0.0, hazeTop = 0.18, hazeBottom = -0.05,
  sunGlow = 0, sunGlowPow = 24, sunDisk = 0, sunSize = 0.012, sunColor = 0xffe2b0, sunDir = null,
  envIntensity = 1, envFrom = null, stars = 0, radius = 2000, clampMax = 8,
} = {}) {
  const tex = await loadHDR(hdri, res);
  if (sunAzimuth !== null) yaw = yawForSun(tex, sunAzimuth);
  const rot = new THREE.Matrix3().setFromMatrix4(new THREE.Matrix4().makeRotationFromEuler(new THREE.Euler(0, -yaw, 0)));
  const hdrSun = hdrSunDir(tex).clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
  const uniforms = {
    map: { value: tex }, rot: { value: rot }, exposure: { value: exposure }, saturation: { value: saturation },
    tint: { value: new THREE.Color(tint) }, zenithTint: { value: new THREE.Color(zenithTint) },
    hazeColor: { value: new THREE.Color(haze) }, hazeAmount: { value: hazeAmount }, hazeTop: { value: hazeTop }, hazeBottom: { value: hazeBottom },
    sunDir: { value: (sunDir || hdrSun).clone() }, sunColor: { value: new THREE.Color(sunColor) },
    sunGlow: { value: sunGlow }, sunGlowPow: { value: sunGlowPow }, sunDisk: { value: sunDisk }, sunSize: { value: sunSize },
    starAmount: { value: stars }, time: { value: 0 }, gradeMix: { value: 0 }, clampMax: { value: clampMax },
  };
  const mat = new THREE.ShaderMaterial({ uniforms, vertexShader: skyVert, fragmentShader: skyFrag, side: THREE.BackSide, depthWrite: false, depthTest: true, fog: false });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(radius, 64, 32), mat);
  dome.renderOrder = -10;
  dome.frustumCulled = false;
  dome.onBeforeRender = (r, s, cam) => dome.position.copy(cam.position);
  scene.add(dome);

  // Image-based lighting from the 1k version, rotated to match the dome.
  const renderer = window.__renderer;
  const envTex = await loadHDR(envFrom || hdri, '1k');
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromEquirectangular(envTex).texture;
  pmrem.dispose();
  scene.environment = env;
  scene.environmentRotation = new THREE.Euler(0, yaw, 0);
  scene.environmentIntensity = envIntensity;
  return { dome, uniforms, sunDir: hdrSun, yaw, tex };
}

// Plain gradient sky for interiors / space (no HDRI needed).
export function gradientEnv(scene, { top = 0x1a1410, bottom = 0x080604, intensity = 0.5 } = {}) {
  const renderer = window.__renderer;
  const s = new THREE.Scene();
  const g = new THREE.SphereGeometry(10, 32, 16);
  const m = new THREE.ShaderMaterial({
    side: THREE.BackSide, uniforms: { top: { value: new THREE.Color(top) }, bottom: { value: new THREE.Color(bottom) } },
    vertexShader: 'varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'uniform vec3 top, bottom; varying vec3 p; void main(){ gl_FragColor = vec4(mix(bottom, top, smoothstep(-0.4, 0.8, normalize(p).y)), 1.0); }',
  });
  s.add(new THREE.Mesh(g, m));
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromScene(s, 0.04).texture;
  pmrem.dispose();
  scene.environment = env;
  scene.environmentIntensity = intensity;
  return env;
}
