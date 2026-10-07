// ===== Full-body figures for wide shots =====
// (x,y) = point between the feet on the ground, h = full height in px.
function limb(ctx, pts, w, col) {
  ctx.strokeStyle = rgba(col); ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
}
function drawFigure(ctx, o) {
  o = Object.assign({ who: 'him', x: 0, y: 0, h: 300, pose: 'stand', phase: 0, dir: -1, look: 0, eyesClosed: 0, mouth: 0, christ: 0, horns: 0, red: 0, bag: false, mantle: 0, t: 0, kneel: 0, headDown: 0, arm: null, glowChest: 0, halo: 0, blink: 0 }, o);
  const { x, y, h, dir } = o;
  const L = LOOK[o.who];
  const her = o.who === 'her';
  const coat = her ? L.coat : mixc(L.coat, ROBE, o.christ);
  const pants = her ? [60, 55, 62] : mixc([40, 42, 50], shade(ROBE, 0.85), o.christ);
  const shoe = o.christ > 0.5 ? [90, 60, 40] : [25, 22, 22];
  ctx.save(); ctx.translate(x, y); ctx.scale(h / 300, h / 300);
  const ph = o.phase;
  let hipY = -150, bob = 0, legs;
  if (o.pose === 'walk') {
    bob = -Math.abs(Math.sin(ph)) * 5;
    const leg = s => {
      const a = Math.sin(ph + s) * 0.42, knee = Math.max(0, Math.sin(ph + s + 1.2)) * 0.7;
      const kx = Math.sin(a) * 75 * dir, ky = hipY + bob + Math.cos(a) * 75;
      const fx = kx + Math.sin(a - knee) * 75 * dir, fy = ky + Math.cos(a - knee) * 75;
      return [[0, hipY + bob], [kx, ky], [fx, Math.min(0, fy)]];
    };
    legs = [leg(Math.PI), leg(0)];
  } else if (o.pose === 'sit') {
    hipY = -85;
    legs = [[[0, hipY], [dir * 70, hipY - 4], [dir * 75, 0]], [[0, hipY], [dir * 62, hipY + 2], [dir * 66, 0]]];
  } else if (o.kneel > 0) {
    const k = o.kneel;
    hipY = lerp(-150, -82, k);
    legs = [[[0, hipY], [dir * lerp(4, 55, k), lerp(-75, -70, k)], [dir * lerp(6, 55, k), 0]], [[0, hipY], [dir * lerp(-4, -8, k), lerp(-75, -2, k)], [dir * lerp(-6, -78, k), lerp(0, -4, k)]]];
  } else {
    legs = [[[0, hipY], [-6, -75], [-8, 0]], [[0, hipY], [6, -75], [8, 0]]];
  }
  const back = legs[0], front = legs[1];
  limb(ctx, back, 30, shade(pants, 0.75)); limb(ctx, [back[2], [back[2][0] + dir * 16, back[2][1]]], 14, shoe);
  const sy = hipY - 105 + bob;
  const lean = (o.pose === 'walk' ? dir * 6 : (o.pose === 'sit' ? dir * 4 : 0)) + o.headDown * dir * 8;
  if (her && o.pose === 'sit') {
    ctx.fillStyle = rgba(shade(L.coat, 0.9));
    ctx.beginPath(); ctx.moveTo(lean - 44, sy - 4); ctx.bezierCurveTo(-75, sy + 60, -62, hipY + 20, -44, hipY + 30); ctx.lineTo(dir * 100, hipY + 22); ctx.bezierCurveTo(dir * 85, hipY - 20, 50, sy + 20, lean + 44, sy - 4); ctx.closePath(); ctx.fill();
  }
  { // long hair falling behind the shoulders
    const hx0 = lean + dir * (3 + o.headDown * 8), hy0 = sy - 34 + o.headDown * 6;
    if (her) { ctx.fillStyle = rgba(L.hair); ctx.beginPath(); ctx.moveTo(hx0 - 30, hy0); ctx.lineTo(hx0 + 30, hy0); ctx.lineTo(hx0 + 34 - dir * 6, sy + 55); ctx.lineTo(hx0 - 34 - dir * 6, sy + 55); ctx.fill(); }
    else if (o.christ > 0) { ctx.globalAlpha = o.christ; ctx.fillStyle = rgba(shade(L.hair, 1.2)); ctx.beginPath(); ctx.moveTo(hx0 - 28, hy0); ctx.lineTo(hx0 + 28, hy0); ctx.lineTo(hx0 + 30 - dir * 8, sy + 30); ctx.lineTo(hx0 - 30 - dir * 8, sy + 30); ctx.fill(); ctx.globalAlpha = 1; }
  }
  ctx.fillStyle = rgba(coat);
  const hemY = hipY + (her ? 10 : 35) + (her ? 0 : o.christ * 70);
  ctx.beginPath(); ctx.moveTo(lean - 36, sy); ctx.lineTo(lean + 36, sy); ctx.lineTo(32 + o.christ * 10, hemY); ctx.lineTo(-32 - o.christ * 10, hemY); ctx.closePath(); ctx.fill();
  if (o.christ > 0 && !her) { ctx.globalAlpha = o.christ; ctx.fillStyle = rgba(MANTLE); ctx.beginPath(); ctx.moveTo(lean + dir * 36, sy); ctx.lineTo(lean - dir * 22, sy + 4); ctx.lineTo(dir * 36, hemY); ctx.lineTo(dir * 44, hipY - 20); ctx.fill(); ctx.globalAlpha = 1; }
  if (her && o.mantle > 0) { ctx.globalAlpha = o.mantle; ctx.fillStyle = rgba(MANTLE); ctx.beginPath(); ctx.moveTo(lean - 48, sy - 6); ctx.lineTo(lean + 48, sy - 6); ctx.lineTo(58, hipY + 25); ctx.lineTo(-58, hipY + 25); ctx.fill(); ctx.globalAlpha = 1; }
  ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.beginPath(); ctx.moveTo(lean + 36 * -dir, sy); ctx.lineTo(lean, sy); ctx.lineTo(0, hemY); ctx.lineTo(32 * -dir, hemY); ctx.fill();
  limb(ctx, front, 30, pants); limb(ctx, [front[2], [front[2][0] + dir * 16, front[2][1]]], 14, shoe);
  if (o.christ > 0 && !her && o.kneel < 0.5) { ctx.globalAlpha = o.christ; ctx.fillStyle = rgba(shade(ROBE, 0.95)); ctx.beginPath(); ctx.moveTo(-36, hipY + 20); ctx.lineTo(36, hipY + 20); ctx.lineTo(44 + dir * 8 * Math.sin(ph), -8); ctx.lineTo(-44 + dir * 8 * Math.sin(ph), -8); ctx.fill(); ctx.globalAlpha = 1; }
  // arm
  const sh = [lean + dir * 4, sy + 10];
  let arm;
  if (o.arm) arm = o.arm(sh);
  else if (o.pose === 'walk') { const a = -Math.sin(ph) * 0.4; arm = [sh, [sh[0] + Math.sin(a) * 50 * dir, sh[1] + 50], [sh[0] + Math.sin(a + 0.3) * 90 * dir, sh[1] + 92]]; }
  else if (o.pose === 'sit' && her) arm = [sh, [sh[0] + dir * 20, sh[1] + 50], [sh[0] + dir * 50, sh[1] + 70]];
  else arm = [sh, [sh[0] + 4, sh[1] + 52], [sh[0] + 6, sh[1] + 100]];
  limb(ctx, arm, 22, shade(coat, 0.85));
  ctx.fillStyle = rgba(L.skin); ctx.beginPath(); ctx.arc(arm[2][0], arm[2][1], 9, 0, 7); ctx.fill();
  if (o.bag) { const [bx, by] = arm[2]; ctx.fillStyle = 'rgb(176,140,96)'; ctx.fillRect(bx - 14, by + 2, 30, 38); ctx.fillStyle = 'rgba(0,0,0,0.2)'; ctx.fillRect(bx - 14, by + 2, 30, 6); }
  if (o.glowChest > 0) glow(ctx, lean, sy + 30, 110, [255, 225, 150], o.glowChest);
  // head
  const hx = lean + dir * (3 + o.headDown * 8), hy = sy - 34 + o.headDown * 6;
  ctx.save(); ctx.translate(hx, hy); ctx.rotate(o.headDown * 0.3 * dir);
  if (o.halo > 0) { glow(ctx, 0, -4, 100, [255, 210, 130], 0.35 * o.halo); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba([255, 230, 170], 0.6 * o.halo); ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, -4, 42, 0, 7); ctx.stroke(); ctx.restore(); }
  ctx.fillStyle = rgba(L.skin); ctx.fillRect(-9, 18, 18, 20);
  if (her) { ctx.fillStyle = rgba(L.hair); ctx.beginPath(); ctx.ellipse(-dir * 7, -2, 30, 34, 0, 0, 7); ctx.fill(); }
  if (!her && o.christ > 0) { ctx.globalAlpha = o.christ; ctx.fillStyle = rgba(shade(L.hair, 1.2)); ctx.beginPath(); ctx.ellipse(-dir * 6, -2, 29, 34, 0, 0, 7); ctx.fill(); ctx.globalAlpha = 1; }
  ctx.fillStyle = rgba(L.skin); ctx.beginPath(); ctx.ellipse(0, 0, 25, 30, 0, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.15)'; ctx.beginPath(); ctx.ellipse(-dir * 10, 2, 16, 28, 0, 0, 7); ctx.fill();
  if (!her && o.christ > 0) { ctx.globalAlpha = o.christ; ctx.fillStyle = rgba(shade(L.hair, 1.6)); ctx.beginPath(); ctx.moveTo(-24, 4); ctx.bezierCurveTo(-24, 30, -12, 42, dir * 6, 44); ctx.bezierCurveTo(14, 42, 24, 30, 24, 4); ctx.bezierCurveTo(16, 18, dir * 12, 10, dir * 10, 10); ctx.bezierCurveTo(-8, 10, -16, 18, -24, 4); ctx.fill(); ctx.globalAlpha = 1; }
  if (her) { ctx.fillStyle = 'rgb(112,42,48)'; ctx.beginPath(); ctx.ellipse(0, -12, 28, 24, 0, Math.PI, 0); ctx.fill(); ctx.fillRect(-28, -15, 56, 8); }
  else { ctx.fillStyle = rgba(L.hair); ctx.beginPath(); ctx.ellipse(-dir * 3, -12, 27, 21, 0, Math.PI * 0.95, Math.PI * 2.05); ctx.fill(); }
  const ex = dir * 11, ey = -2;
  ctx.strokeStyle = 'rgb(30,20,18)'; ctx.fillStyle = 'rgb(30,20,18)'; ctx.lineWidth = 2;
  if (o.eyesClosed > 0.5 || o.blink > 0.5) { ctx.beginPath(); ctx.arc(ex, ey, 4, 0.2, Math.PI - 0.2); ctx.stroke(); }
  else { ctx.beginPath(); ctx.ellipse(ex + dir * o.look * 1.5, ey, 2.6, 3.4, 0, 0, 7); ctx.fill(); }
  if (o.red > 0) glow(ctx, ex, ey, 16, [255, 40, 10], o.red);
  if (o.mouth > 0.08) { ctx.fillStyle = 'rgb(70,25,30)'; ctx.beginPath(); ctx.ellipse(dir * 10, 16, 3.5, 2 + o.mouth * 4, 0, 0, 7); ctx.fill(); }
  else { ctx.strokeStyle = o.christ > 0.5 ? 'rgb(60,35,30)' : 'rgb(30,20,18)'; ctx.beginPath(); ctx.moveTo(dir * 6, 16); ctx.lineTo(dir * 14, 16); ctx.stroke(); }
  if (o.horns > 0) {
    for (const s of [-1, 1]) {
      ctx.fillStyle = 'rgb(30,12,14)'; ctx.shadowColor = 'rgba(255,40,10,0.9)'; ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.moveTo(s * 12 - 6, -22); ctx.quadraticCurveTo(s * 34 * o.horns, -40 * o.horns - 20, s * 28 * o.horns, -62 * o.horns - 22); ctx.quadraticCurveTo(s * 18, -36, s * 12 + 6, -24); ctx.fill(); ctx.shadowBlur = 0;
    }
  }
  ctx.restore();
  ctx.restore();
}

function drawPedestrian(ctx, x, y, h, ph, dir, col = [20, 22, 30], umbrella = true) {
  ctx.save(); ctx.translate(x, y); ctx.scale(h / 300, h / 300);
  ctx.fillStyle = rgba(col);
  const legA = Math.sin(ph) * 0.4;
  limb(ctx, [[0, -150], [Math.sin(legA) * 75 * dir, -75], [Math.sin(legA) * 140 * dir, 0]], 26, col);
  limb(ctx, [[0, -150], [-Math.sin(legA) * 75 * dir, -75], [-Math.sin(legA) * 140 * dir, 0]], 26, col);
  ctx.beginPath(); ctx.moveTo(-34, -260); ctx.lineTo(34, -260); ctx.lineTo(38, -120); ctx.lineTo(-38, -120); ctx.fill();
  ctx.beginPath(); ctx.arc(0, -290, 26, 0, 7); ctx.fill();
  if (umbrella) {
    limb(ctx, [[dir * 20, -230], [dir * 12, -360]], 5, col);
    ctx.beginPath(); ctx.moveTo(dir * 12 - 110, -350); ctx.quadraticCurveTo(dir * 12, -440, dir * 12 + 110, -350);
    for (let i = 0; i < 4; i++) ctx.quadraticCurveTo(dir * 12 + 110 - i * 55 - 27, -365, dir * 12 + 110 - (i + 1) * 55, -350);
    ctx.fill();
  }
  ctx.restore();
}
