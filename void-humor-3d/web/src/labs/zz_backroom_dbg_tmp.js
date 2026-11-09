// TEMP: count draw calls / triangles per frame for the backroom lab views (deleted after use)
import * as BR from './backroom.js';
import { CTX } from '../core/context.js';
export async function setup(app) {
  const st = await BR.setup(app);
  CTX.renderer.info.autoReset = false;
  return st;
}
let last = null;
export async function update(t, app, S) {
  const info = CTX.renderer.info;
  if (last !== null) console.log(`t=${last} calls ${info.render.calls} tris ${info.render.triangles}`);
  info.reset();
  last = t;
  await BR.update(t, app, S);
}
