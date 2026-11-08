// Set registry (lazy). app.set('EDGE') -> { scene, update, anchors, props, look } (built once).
export const SETS = {
  EDGE: async () => (await import('./edge.js')).create(),
  BACKROOM: async () => (await import('./backroom.js')).create(),
  COSMOS: async () => (await import('./cosmos.js')).create(),
};
