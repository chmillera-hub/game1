// Cinematic post chain shared by all shots.
import * as THREE from 'three';
import {
  EffectComposer, RenderPass, EffectPass, Effect, BloomEffect, GodRaysEffect, DepthOfFieldEffect,
  ToneMappingEffect, ToneMappingMode, VignetteEffect, SMAAEffect, KernelSize, BlendFunction,
} from 'postprocessing';

const gradeFrag = /* glsl */`
uniform float contrast;
uniform float saturation;
uniform vec3 lift;
uniform vec3 gammaV;
uniform vec3 gain;
uniform vec3 shadowTint;
uniform vec3 highlightTint;
uniform float split;
uniform float blackPoint;
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec3 c = max(inputColor.rgb, 0.0);
  c = pow(c, vec3(1.0 / 2.2));
  c = (c - 0.5) * contrast + 0.5;
  c = gain * (c + lift * (1.0 - c));
  c = pow(max(c, 0.0), 1.0 / gammaV);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  vec3 tone = mix(shadowTint, highlightTint, smoothstep(0.15, 0.85, l));
  c = mix(c, c * tone * 2.0, split);
  l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, saturation);
  c = max(c - blackPoint, 0.0) / (1.0 - blackPoint);
  c = pow(max(c, 0.0), vec3(2.2));
  outputColor = vec4(c, inputColor.a);
}`;

export class GradeEffect extends Effect {
  constructor(o = {}) {
    const u = (v) => new THREE.Uniform(v);
    const col = (v, d) => new THREE.Vector3(...(v || d));
    super('GradeEffect', gradeFrag, {
      blendFunction: BlendFunction.NORMAL,
      uniforms: new Map([
        ['contrast', u(o.contrast ?? 1.05)],
        ['saturation', u(o.saturation ?? 0.9)],
        ['lift', u(col(o.lift, [0.02, 0.012, 0.0]))],
        ['gammaV', u(col(o.gamma, [1.0, 1.0, 1.0]))],
        ['gain', u(col(o.gain, [1.0, 0.98, 0.94]))],
        ['shadowTint', u(col(o.shadowTint, [0.47, 0.49, 0.53]))],
        ['highlightTint', u(col(o.highlightTint, [0.53, 0.5, 0.46]))],
        ['split', u(o.split ?? 0.35)],
        ['blackPoint', u(o.blackPoint ?? 0.0)],
      ]),
    });
  }
}

// Reference look: warm sepia/golden, soft contrast, gentle bloom and vignette.
export const LOOKS = {
  warm: { contrast: 1.06, saturation: 0.86, lift: [0.025, 0.015, 0.0], gamma: [1.0, 0.98, 0.95], gain: [1.02, 0.98, 0.9], shadowTint: [0.5, 0.47, 0.44], highlightTint: [0.56, 0.5, 0.42], split: 0.35 },
  golden: { contrast: 1.08, saturation: 0.8, lift: [0.03, 0.02, 0.006], gamma: [1.02, 0.99, 0.94], gain: [1.02, 0.97, 0.89], shadowTint: [0.5, 0.47, 0.44], highlightTint: [0.56, 0.51, 0.44], split: 0.32 },
  candle: { contrast: 1.12, saturation: 0.95, lift: [0.012, 0.006, 0.0], gamma: [1.0, 0.97, 0.92], gain: [1.05, 0.96, 0.85], shadowTint: [0.5, 0.45, 0.4], highlightTint: [0.6, 0.5, 0.38], split: 0.4 },
  night: { contrast: 1.1, saturation: 0.8, lift: [0.0, 0.01, 0.025], gamma: [0.97, 0.99, 1.04], gain: [0.92, 0.97, 1.05], shadowTint: [0.44, 0.48, 0.56], highlightTint: [0.56, 0.52, 0.46], split: 0.35 },
  space: { contrast: 1.08, saturation: 0.95, lift: [0.0, 0.0, 0.01], gamma: [1, 1, 1], gain: [1.02, 1.0, 0.97], shadowTint: [0.48, 0.49, 0.53], highlightTint: [0.55, 0.51, 0.45], split: 0.25 },
  heaven: { contrast: 1.0, saturation: 0.82, lift: [0.04, 0.03, 0.015], gamma: [1.02, 1.0, 0.96], gain: [1.03, 1.0, 0.93], shadowTint: [0.5, 0.48, 0.45], highlightTint: [0.56, 0.51, 0.43], split: 0.35 },
};

export function makeComposer(renderer, scene, camera, o = {}) {
  const msaa = o.msaa ?? window.QUALITY.msaa;
  const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, multisampling: msaa });
  composer.addPass(new RenderPass(scene, camera));
  const handles = {};
  if (o.dof) {
    const dof = new DepthOfFieldEffect(camera, {
      worldFocusDistance: o.dof.distance ?? 5, worldFocusRange: o.dof.range ?? 3,
      bokehScale: o.dof.bokeh ?? 2.0, resolutionScale: o.dof.resolution ?? 0.5,
    });
    handles.dof = dof;
    composer.addPass(new EffectPass(camera, dof));
  }
  const effects = [];
  if (o.godrays && o.godrays.source) {
    const gr = new GodRaysEffect(camera, o.godrays.source, {
      resolutionScale: o.godrays.resolution ?? 0.5, density: o.godrays.density ?? 0.94, decay: o.godrays.decay ?? 0.92,
      weight: o.godrays.weight ?? 0.35, exposure: o.godrays.exposure ?? 0.55, samples: o.godrays.samples ?? 60,
      clampMax: o.godrays.clampMax ?? 1.0, blur: true, kernelSize: KernelSize.SMALL,
    });
    handles.godrays = gr;
    effects.push(gr);
  }
  const bloom = new BloomEffect({
    intensity: o.bloom?.intensity ?? 0.9, luminanceThreshold: o.bloom?.threshold ?? 0.75,
    luminanceSmoothing: o.bloom?.smoothing ?? 0.35, mipmapBlur: true, radius: o.bloom?.radius ?? 0.75, levels: o.bloom?.levels ?? 6,
  });
  handles.bloom = bloom;
  effects.push(bloom);
  effects.push(new ToneMappingEffect({ mode: o.toneMapping ?? ToneMappingMode.ACES_FILMIC }));
  const grade = new GradeEffect({ ...(LOOKS[o.look || 'warm']), ...(o.grade || {}) });
  handles.grade = grade;
  effects.push(grade);
  const vig = new VignetteEffect({ offset: o.vignette?.offset ?? 0.32, darkness: o.vignette?.darkness ?? 0.55 });
  handles.vignette = vig;
  effects.push(vig);
  composer.addPass(new EffectPass(camera, ...effects));
  if (msaa === 0) composer.addPass(new EffectPass(camera, new SMAAEffect()));
  renderer.toneMappingExposure = o.exposure ?? 1.0;
  return { composer, handles };
}
