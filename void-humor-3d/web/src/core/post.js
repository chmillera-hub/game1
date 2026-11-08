// Post: MSAA HDR render -> bloom -> ACES output -> grade (vignette, warmth, lift, saturation, fade).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

const GradeShader = {
  uniforms: {
    tDiffuse: { value: null },
    uVignette: { value: 0.28 },     // 0..1
    uSat: { value: 1.06 },
    uWarm: { value: 0.0 },          // -1 cool .. +1 warm
    uLift: { value: new THREE.Color(0.0, 0.0, 0.0) },
    uGain: { value: new THREE.Color(1, 1, 1) },
    uFade: { value: 0 },            // 0..1 to uFadeColor
    uFadeColor: { value: new THREE.Color(0, 0, 0) },
    uRes: { value: new THREE.Vector2(720, 1280) },
    uDither: { value: 1.0 },
  },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse; uniform float uVignette, uSat, uWarm, uFade, uDither; uniform vec3 uLift, uGain, uFadeColor; uniform vec2 uRes;
    varying vec2 vUv;
    float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
    void main(){
      vec4 c = texture2D(tDiffuse, vUv);
      vec3 col = c.rgb;
      float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col = mix(vec3(l), col, uSat);
      col *= mix(vec3(1.0), vec3(1.06, 1.0, 0.92), max(uWarm, 0.0));
      col *= mix(vec3(1.0), vec3(0.92, 0.98, 1.08), max(-uWarm, 0.0));
      col = uLift + col * (uGain - uLift);
      vec2 q = vUv - 0.5; q.x *= uRes.x / uRes.y * 1.25;
      float v = smoothstep(0.85, 0.25, length(q));
      col *= mix(1.0, v, uVignette);
      col = mix(col, uFadeColor, uFade);
      // tiny ordered dither (breaks banding on dark gradients; amplitude below 1 code value)
      col += (h12(gl_FragCoord.xy) - 0.5) / 255.0 * uDither;
      gl_FragColor = vec4(col, 1.0);
    }`,
};

export function makePost(renderer, scene, camera, W, H) {
  const rt = new THREE.WebGLRenderTarget(W, H, { samples: 4, type: THREE.HalfFloatType });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);
  const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.5, 0.55, 0.82);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const grade = new ShaderPass(GradeShader);
  grade.uniforms.uRes.value.set(W, H);
  composer.addPass(grade);
  return {
    composer, renderPass, bloom, grade,
    setScene(s, c) { renderPass.scene = s; renderPass.camera = c; },
    /** look: { bloom, bloomRadius, bloomThreshold, vignette, sat, warm, lift:[r,g,b], gain:[r,g,b], fade, fadeColor, exposure } */
    setLook(look = {}) {
      bloom.strength = look.bloom ?? 0.5; bloom.radius = look.bloomRadius ?? 0.55; bloom.threshold = look.bloomThreshold ?? 0.82;
      const u = grade.uniforms;
      u.uVignette.value = look.vignette ?? 0.28; u.uSat.value = look.sat ?? 1.06; u.uWarm.value = look.warm ?? 0;
      u.uLift.value.setRGB(...(look.lift || [0, 0, 0])); u.uGain.value.setRGB(...(look.gain || [1, 1, 1]));
      u.uFade.value = look.fade ?? 0; u.uFadeColor.value.set(look.fadeColor ?? 0x000000);
      renderer.toneMappingExposure = look.exposure ?? 1.0;
    },
  };
}
