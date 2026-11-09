// TEMP A/B bench lab (same page): t < 1000 -> NEW backroom lab at t; 3000+ -> ORIGINAL backroom set, same lab at t-3000;
// 1000+ -> facetest; 5000 -> empty scene; 6000+v*100 -> NEW wide view with parts hidden (v: 0 room, 1 floor, 2 shafts,
// 3 dome, 4 corner+cage, 5 all transparents-ish: shafts+pools+fx)
import * as THREE from 'three';
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
  const empty = new THREE.Scene(); empty.background = new THREE.Color(0x101018);
  const dome = a.set.scene.children.find((o) => o.isMesh && o.geometry.type === 'SphereGeometry' && o.geometry.parameters.radius === 70);
  return { a, b, c, empty, dome, scene: a.scene, look: a.look };
}
export async function update(t, app, S) {
  let st;
  S.dome.visible = true;
  if (t < 1000) { st = S.a; await BR.update(t, app, st); }
  else if (t < 2000) { st = S.b; await FT.update(t - 1000, app, st); }
  else if (t < 5000) { st = S.c; await BR.update(t - 3000, app, st); }
  else if (t < 6000) { S.scene = S.empty; S.look = S.a.look; return; }
  else {
    const v = Math.floor((t - 6000) / 100), r = (t - 6000) % 100, tt = r < 50 ? 0.6 + r * 0.01 : 3.0 + (r - 50) * 0.01;
    st = S.a; await BR.update(tt, app, st);
    const P = st.set.props;
    if (v === 0) P.room.visible = false;
    if (v === 1) P.floor.visible = false;
    if (v === 2) st.set.update(tt, { shafts: 0, dust: 0 });
    if (v === 3) S.dome.visible = false;
    if (v === 4) { P.corner.visible = false; P.cage.visible = false; }
    if (v === 5) { P.room.visible = false; P.floor.visible = false; }
    if (v === 6) { P.key.castShadow = P.key.castShadow; st.set.scene.traverse((o) => { if (o.isMesh && o.material && o.material.transparent) o.visible = false; }); }
  }
  S.scene = st.scene; S.look = st.look; st.scene.add(app.camera);
}
