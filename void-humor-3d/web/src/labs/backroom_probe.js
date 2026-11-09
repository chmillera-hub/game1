// TEMP: same-page interleaved floor-material probe. mode 0 std, 1 phong, 2 lambert, 3 std w/o shadow receive, 9 facetest.
import * as THREE from 'three';
import * as BR from './backroom.js';
import * as FT from './facetest.js';
export async function setup(app) {
  const br = await BR.setup(app), floor = br.set.props.room.children[0];
  return { br, ft: await FT.setup(app), scene: null, floor, mats: [floor.material,
    new THREE.MeshPhongMaterial({ map: floor.material.map, shininess: 20, specular: 0x2a2224 }),
    new THREE.MeshLambertMaterial({ map: floor.material.map })] };
}
export async function update(t, app, S) {
  const mode = Math.floor(t / 100), tt = t % 100;
  if (mode !== 9) { S.floor.material = S.mats[mode === 3 ? 0 : mode]; S.floor.receiveShadow = mode !== 3; }
  const sub = mode === 9 ? S.ft : S.br;
  await (mode === 9 ? FT.update(tt, app, sub) : BR.update(tt, app, sub));
  S.scene = sub.scene; S.look = sub.look;
}
