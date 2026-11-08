// Materials for the luminous "inside the mind" look.
//   skin(color, opts)      stylized human skin (soft, warm rim, subtle subsurface glow)
//   cloth(color, opts)     fabric (rough, optional velvet sheen)
//   hair(color, opts)      hair masses (soft sheen + rim)
//   being(color, opts)     effervescent inner-being material (self-glow + rim + slow fizz)
//   flat(color)            unlit colour (for tiny details: lash lines, pupils...)
//   enhance(mat, opts)     add rim / fizz / glow / jaw-drop deformation to any MeshStandard/Physical material
// Every material shares GLOBAL.uTime (seconds) -> set once per frame by main.js.
import * as THREE from 'three';

export const GLOBAL = { uTime: { value: 0 } };

const NOISE_GLSL = /* glsl */`
float vh_hash(vec3 p){ p = fract(p*0.3183099+.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vh_noise(vec3 x){ vec3 i=floor(x); vec3 f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(vh_hash(i+vec3(0,0,0)),vh_hash(i+vec3(1,0,0)),f.x),mix(vh_hash(i+vec3(0,1,0)),vh_hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(vh_hash(i+vec3(0,0,1)),vh_hash(i+vec3(1,0,1)),f.x),mix(vh_hash(i+vec3(0,1,1)),vh_hash(i+vec3(1,1,1)),f.x),f.y),f.z); }
float vh_fbm(vec3 p){ float s=0.0, a=0.5; for(int i=0;i<3;i++){ s+=a*vh_noise(p); p*=2.03; a*=0.5; } return s/0.875; }
`;

/**
 * enhance(material, opts) — inject extra shading into a MeshStandardMaterial / MeshPhysicalMaterial.
 * opts:
 *   rim: strength (0..3, HDR >1 blooms)      rimColor: THREE.Color|hex   rimPower: 1..6 (default 3)
 *   glow: self-illumination fraction of base colour (0..1)               glowColor (default = base colour)
 *   fizz: strength of slow animated surface shimmer (0..1)              fizzColor, fizzScale (default 6), fizzSpeed (0.25)
 *   wrap: fake subsurface/wrap lighting amount (0..1): brightens the terminator with wrapColor
 *   jaw: { y, drop, back }  -> uniforms for a jaw-drop deformation of a head mesh (vertices below y move down/back by
 *        uJaw * drop). Set mat.userData.uJaw.value per frame. (Only use on a head geometry.)
 * Returns the material (with .userData.uniforms for live tweaking: uRim, uGlow, uFizz, uJaw...).
 */
export function enhance(mat, opts = {}) {
  const u = {
    uTime: GLOBAL.uTime,
    uRim: { value: opts.rim ?? 0 },
    uRimColor: { value: new THREE.Color(opts.rimColor ?? 0xffffff) },
    uRimPower: { value: opts.rimPower ?? 3.0 },
    uGlow: { value: opts.glow ?? 0 },
    uGlowColor: { value: new THREE.Color(opts.glowColor ?? mat.color ?? 0xffffff) },
    uFizz: { value: opts.fizz ?? 0 },
    uFizzColor: { value: new THREE.Color(opts.fizzColor ?? 0xffffff) },
    uFizzScale: { value: opts.fizzScale ?? 6.0 },
    uFizzSpeed: { value: opts.fizzSpeed ?? 0.25 },
    uWrap: { value: opts.wrap ?? 0 },
    uWrapColor: { value: new THREE.Color(opts.wrapColor ?? 0xff8866) },
    uJaw: { value: 0 },
    uJawY: { value: opts.jaw?.y ?? 0 },
    uJawDrop: { value: opts.jaw?.drop ?? 0 },
    uJawBack: { value: opts.jaw?.back ?? 0 },
    uJawSoft: { value: opts.jaw?.soft ?? 0.05 },
    uOpacityMul: { value: 1 },
  };
  mat.userData.uniforms = u;
  mat.userData.uJaw = u.uJaw;
  const useJaw = !!opts.jaw;
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>\nvarying vec3 vObjPos;\nuniform float uJaw, uJawY, uJawDrop, uJawBack, uJawSoft;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        ${useJaw ? `float jw = uJaw * (1.0 - smoothstep(uJawY - uJawSoft, uJawY + uJawSoft, transformed.y));
        transformed.y -= jw * uJawDrop; transformed.z -= jw * uJawBack;` : ''}
        vObjPos = transformed;`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>\nvarying vec3 vObjPos;
        uniform float uTime, uRim, uRimPower, uGlow, uFizz, uFizzScale, uFizzSpeed, uWrap, uOpacityMul;
        uniform vec3 uRimColor, uGlowColor, uFizzColor, uWrapColor;\n${NOISE_GLSL}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        {
          vec3 vdir = normalize(vViewPosition);
          float fres = 1.0 - clamp(dot(normalize(normal), vdir), 0.0, 1.0);
          totalEmissiveRadiance += uRimColor * uRim * pow(fres, uRimPower);
          totalEmissiveRadiance += uGlowColor * uGlow * diffuseColor.rgb;
          if (uFizz > 0.0) {
            float n = vh_fbm(vObjPos * uFizzScale + vec3(0.0, uTime * uFizzSpeed, uTime * uFizzSpeed * 0.6));
            float sp = smoothstep(0.55, 0.9, n);
            totalEmissiveRadiance += uFizzColor * uFizz * (0.35 * n + sp) * (0.5 + 0.5 * fres);
          }
          totalEmissiveRadiance += uWrapColor * uWrap * pow(fres, 1.5) * 0.35;
        }`)
      .replace('#include <dithering_fragment>', `#include <dithering_fragment>\n gl_FragColor.a *= uOpacityMul;`);
  };
  mat.customProgramCacheKey = () => 'enh' + (useJaw ? 'J' : '') + mat.type;
  return mat;
}

export function skin(color, opts = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(color), roughness: opts.roughness ?? 0.52, metalness: 0,
    sheen: opts.sheen ?? 0.25, sheenColor: new THREE.Color(opts.sheenColor ?? 0xffd2b0), sheenRoughness: 0.6,
    clearcoat: opts.clearcoat ?? 0.0, clearcoatRoughness: 0.5,
  });
  return enhance(m, { rim: opts.rim ?? 0.35, rimColor: opts.rimColor ?? 0xffc9a0, rimPower: 3.0,
    glow: opts.glow ?? 0.06, wrap: opts.wrap ?? 0.5, wrapColor: opts.wrapColor ?? 0xff6a50, jaw: opts.jaw });
}

export function cloth(color, opts = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(color), roughness: opts.roughness ?? 0.85, metalness: 0,
    sheen: opts.sheen ?? 0.5, sheenColor: new THREE.Color(opts.sheenColor ?? color), sheenRoughness: opts.sheenRoughness ?? 0.5,
    side: opts.side ?? THREE.FrontSide,
  });
  return enhance(m, { rim: opts.rim ?? 0.2, rimColor: opts.rimColor ?? 0xffffff, rimPower: 3.5, glow: opts.glow ?? 0.03,
    fizz: opts.fizz ?? 0, fizzColor: opts.fizzColor, fizzScale: opts.fizzScale });
}

export function hair(color, opts = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(color), roughness: opts.roughness ?? 0.45, metalness: 0,
    sheen: 0.8, sheenColor: new THREE.Color(opts.sheenColor ?? 0xc89a70), sheenRoughness: 0.35,
  });
  return enhance(m, { rim: opts.rim ?? 0.35, rimColor: opts.rimColor ?? 0xffd8a8, rimPower: 2.5, glow: opts.glow ?? 0.02 });
}

export function being(color, opts = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(color), roughness: opts.roughness ?? 0.4, metalness: 0,
    sheen: opts.sheen ?? 0.6, sheenColor: new THREE.Color(opts.sheenColor ?? 0xffffff), sheenRoughness: 0.4,
    transparent: !!opts.transparent, opacity: opts.opacity ?? 1,
  });
  return enhance(m, { rim: opts.rim ?? 1.2, rimColor: opts.rimColor ?? color, rimPower: opts.rimPower ?? 2.2,
    glow: opts.glow ?? 0.35, glowColor: opts.glowColor ?? color, fizz: opts.fizz ?? 0.12,
    fizzColor: opts.fizzColor ?? 0xffffff, fizzScale: opts.fizzScale ?? 7, fizzSpeed: opts.fizzSpeed ?? 0.3,
    wrap: opts.wrap ?? 0.3, wrapColor: opts.wrapColor ?? color, jaw: opts.jaw });
}

export function flat(color, opts = {}) {
  return new THREE.MeshBasicMaterial({ color: new THREE.Color(color), transparent: !!opts.transparent,
    opacity: opts.opacity ?? 1, side: opts.side ?? THREE.FrontSide, depthWrite: opts.depthWrite ?? true,
    toneMapped: opts.toneMapped ?? true });
}

// Additive soft glow sprite texture (radial gradient), cached
let _glowTex = null;
export function glowTexture() {
  if (_glowTex) return _glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.55)');
  gr.addColorStop(0.6, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  _glowTex = new THREE.CanvasTexture(c); _glowTex.colorSpace = THREE.SRGBColorSpace;
  return _glowTex;
}

export function glowSprite(color, size = 1, opacity = 1) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: new THREE.Color(color),
    transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false }));
  s.scale.setScalar(size);
  return s;
}

// Soft contact shadow (dark radial decal on the ground). Put at y=0.002 under a character.
let _shadowTex = null;
export function contactShadow(w = 1, d = 0.6, opacity = 0.45) {
  if (!_shadowTex) {
    const c = document.createElement('canvas'); c.width = c.height = 128;
    const g = c.getContext('2d');
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.5)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    _shadowTex = new THREE.CanvasTexture(c);
  }
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map: _shadowTex, transparent: true,
    opacity, depthWrite: false, color: 0x1a1030 }));
  m.rotation.x = -Math.PI / 2; m.position.y = 0.004; m.renderOrder = 1;
  return m;
}
