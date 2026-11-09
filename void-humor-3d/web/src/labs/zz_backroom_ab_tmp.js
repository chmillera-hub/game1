// TEMP A/B bench lab (same page): t < 1000 -> NEW backroom lab at t; 3000+ -> ORIGINAL backroom set, same lab at t-3000;
// 1000+ -> facetest
import * as BR from './backroom.js';
import * as FT from './facetest.js';
import { create as createOrig } from './zz_backroom_origset_tmp.js';
export async function setup(app) {
  const a = await BR.setup(app);
  const orig = await createOrig();
  const real = app.set; app.set = async () => orig;
  const c = await BR.setup(app);
  app.set = real;
  const b = await FT.setup(app);
  return { a, b, c, scene: a.scene, look: a.look };
}
export async function update(t, app, S) {
  let st;
  if (t < 1000) { st = S.a; await BR.update(t, app, st); }
  else if (t < 2000) { st = S.b; await FT.update(t - 1000, app, st); }
  else { st = S.c; await BR.update(t - 3000, app, st); }
  S.scene = st.scene; S.look = st.look; st.scene.add(app.camera);
}
