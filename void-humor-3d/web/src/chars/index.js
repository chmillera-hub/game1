// Character registry (lazy). app.char('JESUS') -> instance (built once, shared by scenes).
export const CHARS = {
  JESUS: async () => (await import('./jesus.js')).create(),
  USER: async () => (await import('./user.js')).create(),
  VOID: async () => (await import('./void.js')).create(),
  FEAR: async () => (await import('./fear.js')).create(),
  MAGICIAN: async () => (await import('./magician.js')).create(),
};
