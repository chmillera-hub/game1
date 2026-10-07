// ===== Character rig (close-ups) =====
// Local coords: head centre at (0,0), head half-width ~100px. Body below.
const LOOK = {
  him: { skin: [226, 184, 152], hair: [42, 30, 26], iris: [118, 82, 48], coat: [52, 58, 60], inner: [92, 94, 102], lip: [170, 100, 92] },
  her: { skin: [238, 206, 188], hair: [38, 26, 30], iris: [96, 122, 140], coat: [70, 82, 98], inner: [150, 118, 60], lip: [190, 110, 110] },
};
const ROBE = [226, 214, 190], MANTLE = [128, 44, 40];

function P0(o) {
  return Object.assign({
    who: 'him', x: W / 2, y: H / 2, s: 1, rot: 0, tilt: 0, gx: 0, gy: 0, blink: 0, open: 1, sad: 0, angry: 0, surprise: 0,
    smile: 0, mouth: 0, round: 0, tears: 0, drops: [], red: 0, horns: 0, christ: 0, halo: 0, breath: 0, wind: 0, t: 0,
    tired: 0, closedHappy: 0, mantle: 0, cracks: 0, crumble: 0, slit: 0, grit: 0, hood: 0,
  }, o);
}

function drawCharacter(ctx, p) {
  p = P0(p);
  const L = LOOK[p.who];
  const skin = L.skin;
  ctx.save();
  ctx.translate(p.x, p.y); ctx.scale(p.s, p.s); ctx.rotate(p.rot);
  if (p.halo > 0) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createRadialGradient(0, -20, 60, 0, -20, 330);
    g.addColorStop(0, rgba([255, 220, 140], 0.55 * p.halo)); g.addColorStop(0.45, rgba([255, 200, 110], 0.22 * p.halo)); g.addColorStop(1, 'rgba(255,200,100,0)');
    ctx.fillStyle = g; ctx.fillRect(-340, -360, 680, 680);
    ctx.strokeStyle = rgba([255, 236, 180], 0.55 * p.halo); ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(0, -25, 170 + Math.sin(p.t * 1.3) * 3, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = rgba([255, 236, 180], 0.2 * p.halo); ctx.lineWidth = 12; ctx.stroke();
    ctx.restore();
  }
  const breath = Math.sin(p.t * 1.6) * 3 * (1 + p.breath);
  // ---- body ----
  ctx.save(); ctx.translate(0, breath * 0.6);
  drawBackHair(ctx, p, L, 'body');
  drawBody(ctx, p, L);
  ctx.restore();
  // ---- head ----
  ctx.save();
  ctx.translate(0, 110 + breath * 0.3); ctx.rotate(p.tilt); ctx.translate(0, -110);
  drawBackHair(ctx, p, L, 'head');
  // neck
  ctx.fillStyle = rgba(shade(skin, 0.86));
  ctx.beginPath(); ctx.moveTo(-36, 70); ctx.lineTo(36, 70); ctx.lineTo(42, 175); ctx.lineTo(-42, 175); ctx.fill();
  ctx.fillStyle = rgba(shade(skin, 0.7), 0.6);
  ctx.beginPath(); ctx.moveTo(-36, 90); ctx.quadraticCurveTo(0, 140, 36, 90); ctx.lineTo(36, 70); ctx.lineTo(-36, 70); ctx.fill();
  // ears
  for (const sx of [-1, 1]) {
    ctx.fillStyle = rgba(shade(skin, 0.92));
    ctx.beginPath(); ctx.ellipse(sx * 94, 10, 14, 26, sx * 0.15, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = rgba(shade(skin, 0.7), 0.6); ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(sx * 95, 10, 7, 16, sx * 0.15, -1, 1.5); ctx.stroke();
  }
  // head shape
  const nw = p.who === 'her' ? 0.9 : 1;
  ctx.save(); ctx.scale(nw, 1);
  headPath(ctx);
  const fg = ctx.createLinearGradient(-100, 0, 100, 0);
  fg.addColorStop(0, rgba(shade(skin, 0.86))); fg.addColorStop(0.55, rgba(skin)); fg.addColorStop(1, rgba(shade(skin, 0.93)));
  ctx.fillStyle = fg; ctx.fill();
  // jaw shadow
  ctx.save(); headPath(ctx); ctx.clip();
  ctx.fillStyle = rgba(shade(skin, 0.75), 0.25); ctx.beginPath(); ctx.ellipse(0, 150, 120, 60, 0, 0, Math.PI * 2); ctx.fill();
  // cheeks
  radial(ctx, -58, 48, 34, p.who === 'her' ? [235, 130, 130] : [220, 130, 110], p.who === 'her' ? 0.28 + p.tears * 0.15 : 0.12 + p.tears * 0.12);
  radial(ctx, 58, 48, 34, p.who === 'her' ? [235, 130, 130] : [220, 130, 110], p.who === 'her' ? 0.28 + p.tears * 0.15 : 0.12 + p.tears * 0.12);
  // tired under-eyes
  const tired = p.tired + (p.who === 'her' ? 0.4 : 0.25);
  for (const sx of [-1, 1]) { ctx.fillStyle = rgba([110, 70, 90], 0.12 * tired); ctx.beginPath(); ctx.ellipse(sx * 40, 26, 22, 8, 0, 0, Math.PI * 2); ctx.fill(); }
  // stubble / beard
  if (p.who === 'him') drawBeard(ctx, p, L);
  if (p.who === 'her') { const r = rng(5); ctx.fillStyle = 'rgba(150,90,70,0.35)'; for (let i = 0; i < 18; i++) { const sx = r() > .5 ? 1 : -1; ctx.beginPath(); ctx.arc(sx * (35 + r() * 35), 30 + r() * 22, 1.3, 0, 7); ctx.fill(); } }
  ctx.restore();
  ctx.restore();
  // features
  drawNose(ctx, p, skin);
  drawMouth(ctx, p, L);
  for (const side of [-1, 1]) { ctx.save(); ctx.translate(side * 41, 8); ctx.scale(1.18, 1.18); ctx.translate(-side * 41, -8); drawEye(ctx, p, L, side); ctx.restore(); }
  for (const side of [-1, 1]) drawBrow(ctx, p, L, side);
  drawTears(ctx, p);
  drawFrontHair(ctx, p, L);
  if (p.horns > 0) drawHorns(ctx, p);
  ctx.restore();
  ctx.restore();
}

function headPath(ctx) {
  ctx.beginPath(); ctx.moveTo(0, -122);
  ctx.bezierCurveTo(62, -124, 100, -84, 100, -12);
  ctx.bezierCurveTo(100, 42, 84, 82, 52, 108);
  ctx.bezierCurveTo(32, 124, 14, 130, 0, 130);
  ctx.bezierCurveTo(-14, 130, -32, 124, -52, 108);
  ctx.bezierCurveTo(-84, 82, -100, 42, -100, -12);
  ctx.bezierCurveTo(-100, -84, -62, -124, 0, -122); ctx.closePath();
}

function drawBody(ctx, p, L) {
  const c = p.christ;
  if (p.who === 'him') {
    const coat = mixc(L.coat, ROBE, c), inner = mixc(L.inner, mixc(ROBE, [200, 186, 160], 0.5), c);
    // shoulders / jacket
    ctx.fillStyle = rgba(coat);
    ctx.beginPath(); ctx.moveTo(-50, 150); ctx.bezierCurveTo(-130, 165, -235, 190, -270, 270); ctx.lineTo(-300, 520); ctx.lineTo(300, 520); ctx.lineTo(270, 270);
    ctx.bezierCurveTo(235, 190, 130, 165, 50, 150); ctx.fill();
    const sg = ctx.createLinearGradient(-280, 0, 280, 0); sg.addColorStop(0, 'rgba(0,0,0,0.35)'); sg.addColorStop(0.5, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.2)');
    ctx.fillStyle = sg; ctx.fill();
    // inner hoodie / robe neckline
    ctx.fillStyle = rgba(inner);
    ctx.beginPath(); ctx.moveTo(-60, 150); ctx.quadraticCurveTo(0, 175, 60, 150); ctx.lineTo(lerp(70, 40, c), 520); ctx.lineTo(lerp(-70, -40, c), 520); ctx.fill();
    if (c < 0.9) { // hood bunched behind neck + lapels
      ctx.globalAlpha = 1 - c;
      ctx.fillStyle = rgba(shade(L.inner, 0.85)); ctx.beginPath(); ctx.moveTo(-95, 150); ctx.bezierCurveTo(-90, 115, 90, 115, 95, 150); ctx.bezierCurveTo(60, 180, -60, 180, -95, 150); ctx.fill();
      ctx.strokeStyle = rgba(shade(L.coat, 0.6)); ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(-70, 160); ctx.lineTo(-30, 520); ctx.moveTo(70, 160); ctx.lineTo(30, 520); ctx.stroke();
      ctx.strokeStyle = rgba([210, 210, 215], 0.8); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-20, 175); ctx.lineTo(-24, 260); ctx.moveTo(20, 175); ctx.lineTo(24, 260); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    if (c > 0) { // mantle drape
      ctx.globalAlpha = c;
      ctx.fillStyle = rgba(MANTLE);
      ctx.beginPath(); ctx.moveTo(60, 150); ctx.bezierCurveTo(160, 165, 250, 200, 275, 280); ctx.lineTo(300, 520); ctx.lineTo(-120, 520); ctx.bezierCurveTo(-20, 400, 60, 260, 60, 150); ctx.fill();
      ctx.strokeStyle = rgba(shade(MANTLE, 0.6)); ctx.lineWidth = 3;
      for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(90 + i * 40, 190 + i * 10); ctx.quadraticCurveTo(40 + i * 40, 360, -60 + i * 60, 520); ctx.stroke(); }
      ctx.globalAlpha = 1;
    }
  } else {
    // her: thin shoulders, blanket, scarf
    ctx.fillStyle = rgba(L.coat);
    ctx.beginPath(); ctx.moveTo(-45, 150); ctx.bezierCurveTo(-110, 160, -200, 185, -230, 260); ctx.lineTo(-250, 520); ctx.lineTo(250, 520); ctx.lineTo(230, 260); ctx.bezierCurveTo(200, 185, 110, 160, 45, 150); ctx.fill();
    ctx.save(); ctx.clip(); ctx.strokeStyle = 'rgba(255,255,255,0.07)'; ctx.lineWidth = 9;
    for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(-240, 300 + i * 40); ctx.quadraticCurveTo(0, 270 + i * 40, 240, 300 + i * 40); ctx.stroke(); }
    ctx.restore();
    const sg = ctx.createLinearGradient(-250, 0, 250, 0); sg.addColorStop(0, 'rgba(0,0,0,0.3)'); sg.addColorStop(0.6, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.25)');
    ctx.fillStyle = sg; ctx.beginPath(); ctx.moveTo(-45, 150); ctx.bezierCurveTo(-110, 160, -200, 185, -230, 260); ctx.lineTo(-250, 520); ctx.lineTo(250, 520); ctx.lineTo(230, 260); ctx.bezierCurveTo(200, 185, 110, 160, 45, 150); ctx.fill();
    // scarf
    ctx.fillStyle = rgba(L.inner);
    ctx.beginPath(); ctx.moveTo(-70, 140); ctx.bezierCurveTo(-80, 200, 80, 200, 70, 140); ctx.bezierCurveTo(40, 165, -40, 165, -70, 140); ctx.fill();
    ctx.beginPath(); ctx.moveTo(20, 175); ctx.lineTo(60, 175); ctx.lineTo(70, 330); ctx.lineTo(35, 335); ctx.fill();
    ctx.strokeStyle = rgba(shade(L.inner, 0.7)); ctx.lineWidth = 2; for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(38 + i * 1, 190 + i * 24); ctx.lineTo(64, 192 + i * 24); ctx.stroke(); }
    if (p.mantle > 0) {
      ctx.globalAlpha = p.mantle;
      ctx.fillStyle = rgba(MANTLE);
      ctx.beginPath(); ctx.moveTo(-95, 150); ctx.bezierCurveTo(-180, 160, -235, 200, -255, 280); ctx.lineTo(-270, 520); ctx.lineTo(-40, 520); ctx.bezierCurveTo(-60, 380, -80, 220, -95, 150); ctx.fill();
      ctx.beginPath(); ctx.moveTo(95, 150); ctx.bezierCurveTo(180, 160, 235, 200, 255, 280); ctx.lineTo(270, 520); ctx.lineTo(70, 520); ctx.bezierCurveTo(90, 380, 90, 220, 95, 150); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-100, 150); ctx.bezierCurveTo(-60, 120, 60, 120, 100, 150); ctx.bezierCurveTo(60, 170, -60, 170, -100, 150); ctx.fill();
      glow(ctx, 0, 250, 260, [255, 200, 120], 0.12 * p.mantle);
      ctx.globalAlpha = 1;
    }
  }
}

function drawBeard(ctx, p, L) {
  const c = p.christ;
  // stubble: soft gradient shadow over jaw
  ctx.save();
  const sg2 = ctx.createRadialGradient(0, 105, 10, 0, 95, 115);
  sg2.addColorStop(0, rgba(L.hair, 0.2 * (1 - c))); sg2.addColorStop(0.6, rgba(L.hair, 0.13 * (1 - c))); sg2.addColorStop(1, rgba(L.hair, 0));
  ctx.fillStyle = sg2; ctx.fillRect(-110, 20, 220, 120);
  const r = rng(11); ctx.fillStyle = rgba(L.hair, 0.1 * (1 - c));
  for (let i = 0; i < 260; i++) { const a = r() * Math.PI, rr = 0.6 + r() * 0.4; const x = Math.cos(a) * 86 * rr, y = 55 + Math.sin(a) * 80 * rr; ctx.fillRect(x, y, 1.1, 1.1); }
  ctx.restore();
  if (c > 0) {
    ctx.globalAlpha = c;
    const bc = shade(L.hair, 1.25);
    ctx.fillStyle = rgba(bc);
    ctx.beginPath(); ctx.moveTo(-96, 0); ctx.bezierCurveTo(-96, 70, -70, 120, -30, 142); ctx.quadraticCurveTo(0, 162, 30, 142);
    ctx.bezierCurveTo(70, 120, 96, 70, 96, 0); ctx.lineTo(80, 10); ctx.bezierCurveTo(70, 70, 45, 92, 26, 90);
    ctx.quadraticCurveTo(0, 82, -26, 90); ctx.bezierCurveTo(-45, 92, -70, 70, -80, 10); ctx.closePath(); ctx.fill();
    // moustache
    ctx.beginPath(); ctx.moveTo(-36, 76); ctx.quadraticCurveTo(-20, 56, 0, 62); ctx.quadraticCurveTo(20, 56, 36, 76); ctx.quadraticCurveTo(20, 68, 0, 70); ctx.quadraticCurveTo(-20, 68, -36, 76); ctx.fill();
    ctx.strokeStyle = rgba(shade(bc, 0.6), 0.6); ctx.lineWidth = 1.5;
    const r2 = rng(4);
    for (let i = 0; i < 40; i++) { const x = (r2() - .5) * 150, y = 80 + r2() * 60; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x * 0.95, y + 10, x * 0.9, y + 18); ctx.stroke(); }
    ctx.globalAlpha = 1;
  }
}

function drawNose(ctx, p, skin) {
  ctx.strokeStyle = rgba(shade(skin, 0.68), 0.7); ctx.lineWidth = 2.2; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(6, 18); ctx.quadraticCurveTo(12, 38, 9, 48); ctx.stroke();
  ctx.fillStyle = rgba(shade(skin, 0.7), 0.5);
  ctx.beginPath(); ctx.ellipse(-8, 51, 5, 2.6, 0.2, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(8, 51, 5, 2.6, -0.2, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.beginPath(); ctx.ellipse(3, 38, 2, 5, 0, 0, 7); ctx.fill();
}

function drawMouth(ctx, p, L) {
  const o = clamp(p.mouth), my = 80, sm = p.smile - p.sad * 0.5 - p.angry * 0.6;
  const wdt = (p.who === 'her' ? 20 : 23) * (1 - p.round * 0.35 + p.grit * 0.15);
  ctx.lineCap = 'round';
  if (o < 0.04) {
    ctx.strokeStyle = rgba(shade(L.lip, 0.55)); ctx.lineWidth = 2.6;
    ctx.beginPath(); ctx.moveTo(-wdt, my - sm * 5); ctx.quadraticCurveTo(0, my + sm * 7 + (p.grit ? -2 : 0), wdt, my - sm * 5); ctx.stroke();
    ctx.fillStyle = rgba(L.lip, p.who === 'her' ? 0.55 : 0.3); ctx.beginPath(); ctx.ellipse(0, my + 7, wdt * 0.55, 3.5, 0, 0, 7); ctx.fill();
    if (p.grit > 0) { // clenched jaw tension lines
      ctx.strokeStyle = rgba(shade(L.skin, 0.6), 0.5 * p.grit); ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(-wdt - 4, my - 4); ctx.lineTo(-wdt - 8, my + 6); ctx.moveTo(wdt + 4, my - 4); ctx.lineTo(wdt + 8, my + 6); ctx.stroke();
    }
    return;
  }
  const h = 4 + o * 24;
  ctx.fillStyle = 'rgb(58,22,26)';
  ctx.beginPath(); ctx.moveTo(-wdt, my - sm * 4); ctx.quadraticCurveTo(0, my - 5 - o * 2, wdt, my - sm * 4);
  ctx.quadraticCurveTo(wdt * 0.8, my + h * 0.9, 0, my + h); ctx.quadraticCurveTo(-wdt * 0.8, my + h * 0.9, -wdt, my - sm * 4); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(240,235,230,0.9)'; ctx.fillRect(-wdt, my - 8, wdt * 2, 6 + o * 2);
  ctx.fillStyle = 'rgb(170,70,80)'; ctx.beginPath(); ctx.ellipse(0, my + h + 2, wdt * 0.6, h * 0.45, 0, 0, 7); ctx.fill();
  ctx.restore();
  ctx.strokeStyle = rgba(shade(L.lip, 0.7)); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-wdt, my - sm * 4); ctx.quadraticCurveTo(0, my - 5 - o * 2, wdt, my - sm * 4); ctx.stroke();
  ctx.fillStyle = rgba(L.lip, 0.55); ctx.beginPath(); ctx.ellipse(0, my + h + 4, wdt * 0.55, 3.5, 0, 0, 7); ctx.fill();
}

function eyeGeom(p, side) {
  const ex = side * 41, ey = 8;
  let open = clamp(p.open * (1 - p.blink) * (1 + p.surprise * 0.2) * (1 - p.angry * 0.32), 0, 1.2);
  if (p.closedHappy) open *= (1 - p.closedHappy);
  const h = 18;
  const inner = [ex - side * 25, ey + 3], outer = [ex + side * 27, ey - 1 + p.sad * 2];
  // upper lid control points: inner side lowered when angry, outer side lowered when sad
  const topIn = lerp(ey + 7, ey - h * 1.25 + p.angry * 13 - p.sad * 5, open);
  const topOut = lerp(ey + 7, ey - h * 1.3 + p.sad * 7, open);
  return { ex, ey, open, inner, outer, topIn, topOut };
}
function eyePath(ctx, g, side) {
  const { ex, ey, inner, outer, topIn, topOut } = g;
  ctx.beginPath(); ctx.moveTo(inner[0], inner[1]);
  ctx.bezierCurveTo(ex - side * 13, topIn, ex + side * 12, topOut, outer[0], outer[1]);
  ctx.bezierCurveTo(ex + side * 14, ey + 13, ex - side * 10, ey + 13, inner[0], inner[1]); ctx.closePath();
}
function drawEye(ctx, p, L, side) {
  const g = eyeGeom(p, side);
  const { ex, ey, open } = g;
  if (open > 0.06) {
    ctx.save(); eyePath(ctx, g, side);
    ctx.fillStyle = rgba(mixc([248, 244, 240], [70, 18, 16], p.red * 0.75)); ctx.fill(); ctx.clip();
    const ix = ex + p.gx * 11, iy = ey + 2 + p.gy * 6;
    const ir = 12.5, irisC = mixc(L.iris, [255, 40, 20], p.red);
    const ig = ctx.createRadialGradient(ix, iy + 3, 2, ix, iy, ir);
    ig.addColorStop(0, rgba(shade(irisC, 1.35))); ig.addColorStop(0.65, rgba(irisC)); ig.addColorStop(1, rgba(shade(irisC, 0.45)));
    ctx.fillStyle = ig; ctx.beginPath(); ctx.arc(ix, iy, ir, 0, 7); ctx.fill();
    ctx.fillStyle = p.red > 0.5 ? 'rgb(20,0,0)' : 'rgb(18,12,10)';
    const pw = lerp(5.5, 2, p.slit) * (1 + p.surprise * 0.1), ph = lerp(5.5, 10, p.slit);
    ctx.beginPath(); ctx.ellipse(ix, iy, pw, ph, 0, 0, 7); ctx.fill();
    // lid shadow
    const sg = ctx.createLinearGradient(0, ey - 20, 0, ey + 2); sg.addColorStop(0, 'rgba(60,30,30,0.45)'); sg.addColorStop(1, 'rgba(60,30,30,0)');
    ctx.fillStyle = sg; ctx.fillRect(ex - 30, ey - 25, 60, 30);
    // highlights
    ctx.fillStyle = 'rgba(255,255,255,0.95)'; ctx.beginPath(); ctx.arc(ix + 4.5, iy - 5, 3.6 + p.tears * 1.2, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.beginPath(); ctx.arc(ix - 4, iy + 4.5, 1.6 + p.tears, 0, 7); ctx.fill();
    if (p.spark) { glow(ctx, ix - 1, iy - 1, 7, [255, 250, 230], p.spark); ctx.fillStyle = rgba([255, 255, 255], p.spark); ctx.beginPath(); ctx.arc(ix - 1, iy - 1, 1.8, 0, 7); ctx.fill(); }
    if (p.tears > 0) {
      const wg = ctx.createLinearGradient(0, ey + 2, 0, ey + 13);
      wg.addColorStop(0, 'rgba(200,225,255,0)'); wg.addColorStop(1, rgba([215, 235, 255], 0.55 * p.tears));
      ctx.fillStyle = wg; ctx.fillRect(ex - 30, ey, 60, 15);
      ctx.fillStyle = rgba([255, 255, 255], 0.6 * p.tears);
      for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.ellipse(ex - side * 8 + k * side * 9, ey + 9, 2.5, 1, 0, 0, 7); ctx.fill(); }
    }
    ctx.restore();
    if (p.red > 0) glow(ctx, ex + p.gx * 11, ey + 2, 40, [255, 30, 10], 0.5 * p.red);
  }
  // upper lid line + lashes
  const { inner, outer, topIn, topOut } = g;
  ctx.strokeStyle = 'rgb(30,18,16)'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.lineWidth = open > 0.06 ? 3.6 : 3;
  ctx.beginPath(); ctx.moveTo(inner[0], inner[1]);
  if (open > 0.06) ctx.bezierCurveTo(ex - side * 13, topIn, ex + side * 12, topOut, outer[0], outer[1]);
  else ctx.bezierCurveTo(ex - side * 12, ey + 13 + (p.closedHappy ? -12 : 0), ex + side * 12, ey + 13 + (p.closedHappy ? -12 : 0), outer[0], outer[1]);
  ctx.stroke();
  // outer wing / lashes
  ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(outer[0], outer[1]); ctx.lineTo(outer[0] + side * 6, outer[1] - 3); ctx.stroke();
  if (p.who === 'her') { ctx.lineWidth = 1.6; for (let k = 0; k < 3; k++) { const ox = outer[0] - side * k * 6, oy = (open > 0.06 ? lerp(outer[1], topOut, 0.25 * k) : outer[1] + 4); ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ox + side * 5, oy - (open > .06 ? 5 : -4)); ctx.stroke(); } }
  // crease
  if (open > 0.3) { ctx.strokeStyle = rgba(shade(LOOK[p.who].skin, 0.62), 0.55); ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(ex - side * 18, (topIn + ey) / 2 - 6); ctx.quadraticCurveTo(ex, Math.min(topIn, topOut) - 6, ex + side * 22, topOut + 2); ctx.stroke(); }
  // lower lid
  if (open > 0.06) {
    ctx.strokeStyle = rgba(shade(LOOK[p.who].skin, 0.6), 0.55); ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(outer[0] - side * 3, outer[1] + 4); ctx.bezierCurveTo(ex + side * 14, ey + 14, ex - side * 10, ey + 14, inner[0] + side * 3, inner[1] + 1); ctx.stroke();
    if (p.tears > 0) { ctx.strokeStyle = rgba([255, 255, 255], 0.75 * p.tears); ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(outer[0] - side * 5, outer[1] + 6); ctx.bezierCurveTo(ex + side * 12, ey + 15, ex - side * 8, ey + 15, inner[0] + side * 2, inner[1] + 3); ctx.stroke(); }
  }
}
function drawBrow(ctx, p, L, side) {
  const ex = side * 41, ey = 8;
  const inX = ex - side * (24 - p.angry * 5), outX = ex + side * 30;
  const inY = ey - 30 - p.sad * 15 - p.surprise * 10 + p.angry * 17;
  const outY = ey - 31 - p.surprise * 8 + p.sad * 6 - p.angry * 8;
  const midY = Math.min(inY, outY) - 7 - p.surprise * 3 + p.angry * 2;
  ctx.strokeStyle = rgba(shade(LOOK[p.who].hair, p.who === 'her' ? 1.1 : 0.9));
  ctx.lineCap = 'round';
  ctx.lineWidth = p.who === 'her' ? 4.5 : 7;
  ctx.beginPath(); ctx.moveTo(inX, inY); ctx.quadraticCurveTo(ex + side * 4, midY, outX, outY); ctx.stroke();
  if (p.angry > 0.3 || p.sad > 0.5) { // furrow
    ctx.strokeStyle = rgba(shade(LOOK[p.who].skin, 0.65), 0.35 * Math.max(p.angry, p.sad - 0.3)); ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(side * 8, -28); ctx.lineTo(side * 5, -14); ctx.stroke();
  }
}
function drawTears(ctx, p) {
  for (const d of p.drops) {
    if (d.p <= 0 || d.p >= 1.3) continue;
    const side = d.side, ex = side * 41;
    const x0 = ex - side * 12, y0 = 22;
    const path = u => [x0 - side * 6 * u + Math.sin(u * 3) * 3 * side, y0 + 95 * u];
    const u = Math.min(d.p, 1), a = d.p > 1 ? 1 - (d.p - 1) / 0.3 : 1;
    ctx.strokeStyle = rgba([235, 245, 255], 0.4 * a); ctx.lineWidth = 2.4; ctx.lineCap = 'round';
    ctx.beginPath(); for (let k = 0; k <= 12; k++) { const [x, y] = path(u * k / 12); k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke();
    const [x, y] = path(u);
    const col = d.red ? [255, 120, 100] : [225, 240, 255];
    ctx.fillStyle = rgba(col, 0.85 * a);
    ctx.beginPath(); ctx.moveTo(x, y - 9); ctx.quadraticCurveTo(x + 5, y, x, y + 5); ctx.quadraticCurveTo(x - 5, y, x, y - 9); ctx.fill();
    ctx.fillStyle = rgba([255, 255, 255], a); ctx.beginPath(); ctx.arc(x + 1.2, y - 1, 1.3, 0, 7); ctx.fill();
  }
}
function hairStrand(ctx, x0, y0, x1, y1, w, bend) {
  const mx = (x0 + x1) / 2 + bend, my = (y0 + y1) / 2;
  ctx.beginPath(); ctx.moveTo(x0 - w, y0); ctx.quadraticCurveTo(mx - w * 0.5, my, x1, y1); ctx.quadraticCurveTo(mx + w * 0.5, my, x0 + w, y0); ctx.fill();
}
function drawBackHair(ctx, p, L, part) {
  const hc = L.hair, wd = Math.sin(p.t * 1.1) * p.wind * 8;
  if (p.who === 'him') {
    if (part === 'head') {
      ctx.fillStyle = rgba(hc);
      ctx.beginPath(); ctx.moveTo(-104, 10); ctx.bezierCurveTo(-118, -120, -60, -158, 0, -156); ctx.bezierCurveTo(60, -158, 118, -120, 104, 10); ctx.lineTo(90, -30); ctx.lineTo(-90, -30); ctx.fill();
    }
    if (part === 'body' && p.christ > 0) {
      ctx.globalAlpha = p.christ; ctx.fillStyle = rgba(shade(hc, 1.2));
      ctx.beginPath(); ctx.moveTo(-100, -60); ctx.bezierCurveTo(-140, 20, -150, 120, -128 + wd, 200); ctx.quadraticCurveTo(-90, 215, -60, 180); ctx.lineTo(-40, 60);
      ctx.lineTo(40, 60); ctx.lineTo(60, 180); ctx.quadraticCurveTo(90, 215, 128 + wd, 200); ctx.bezierCurveTo(150, 120, 140, 20, 100, -60); ctx.fill();
      ctx.strokeStyle = rgba(shade(hc, 0.8), 0.6); ctx.lineWidth = 2;
      for (let i = 0; i < 6; i++) { const sx = i < 3 ? -1 : 1, k = i % 3; ctx.beginPath(); ctx.moveTo(sx * (100 + k * 8), 0); ctx.quadraticCurveTo(sx * (130 + k * 4), 100, sx * (110 + k * 6) + wd, 195); ctx.stroke(); }
      ctx.globalAlpha = 1;
    }
  } else {
    if (part === 'body') {
      ctx.fillStyle = rgba(hc);
      ctx.beginPath(); ctx.moveTo(-100, -40); ctx.bezierCurveTo(-150, 60, -160, 200, -140 + wd, 300); ctx.lineTo(140 + wd, 300); ctx.bezierCurveTo(160, 200, 150, 60, 100, -40); ctx.fill();
    }
    if (part === 'head') {
      ctx.fillStyle = rgba(hc);
      ctx.beginPath(); ctx.ellipse(0, -40, 112, 110, 0, 0, 7); ctx.fill();
    }
  }
}
function drawFrontHair(ctx, p, L) {
  const hc = L.hair, t = p.t, w = p.wind;
  ctx.fillStyle = rgba(hc);
  if (p.who === 'him') {
    const c = p.christ;
    if (c < 1) {
      ctx.save(); ctx.globalAlpha = 1 - c;
      // cap with messy top
      ctx.beginPath(); ctx.moveTo(-106, -8); ctx.bezierCurveTo(-116, -118, -56, -158, 0, -156); ctx.bezierCurveTo(56, -158, 116, -118, 106, -8);
      ctx.bezierCurveTo(98, -55, 72, -82, 30, -88); ctx.quadraticCurveTo(-30, -92, -78, -70); ctx.quadraticCurveTo(-100, -50, -106, -8); ctx.fill();
      const r = rng(23);
      for (let i = 0; i < 26; i++) { const a = Math.PI * (1.05 + 0.9 * i / 25), rr = 150 + r() * 4, len = 10 + r() * 14;
        const x = Math.cos(a) * 104, y = Math.sin(a) * rr * 0.98 - 4; const tx = Math.cos(a + 0.25) * (104 + len), ty = Math.sin(a + 0.25) * (rr + len) - 4;
        ctx.beginPath(); ctx.moveTo(x - 7 * Math.sin(a), y + 7 * Math.cos(a)); ctx.lineTo(tx, ty); ctx.lineTo(x + 7 * Math.sin(a), y - 7 * Math.cos(a)); ctx.fill(); }
      // fringe: locks sweeping to one side
      const locks = [[-86, -100, -70, -40, 15, 10], [-58, -112, -36, -52, 17, 12], [-26, -118, -2, -60, 18, 12], [8, -116, 34, -62, 17, 12], [40, -110, 66, -58, 15, 10], [70, -96, 92, -40, 13, 8]];
      for (const [x0, y0, x1, y1, wd, bd] of locks) hairStrand(ctx, x0, y0, x1 + Math.sin(t * 1.3 + x0) * w * 6, y1 + noise1(t + x0) * w * 3, wd, bd + noise1(t * 0.7 + x0) * w * 6);
      ctx.strokeStyle = rgba(shade(hc, 2.2), 0.28); ctx.lineWidth = 2; ctx.lineCap = 'round';
      for (const [x0, y0, x1, y1] of [[-60, -132, -20, -96], [-20, -140, 20, -100], [30, -134, 60, -96]]) { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo((x0 + x1) / 2 + 8, (y0 + y1) / 2, x1, y1); ctx.stroke(); }
      ctx.restore();
    }
    if (c > 0) {
      ctx.save(); ctx.globalAlpha = c; ctx.fillStyle = rgba(shade(hc, 1.2));
      // centre-parted long hair
      ctx.beginPath(); ctx.moveTo(0, -150); ctx.bezierCurveTo(-70, -156, -112, -110, -108, -20); ctx.bezierCurveTo(-110, 40, -116, 90, -122 + w * 4, 140); ctx.lineTo(-92, 120); ctx.bezierCurveTo(-92, 40, -88, -30, -60, -80); ctx.quadraticCurveTo(-30, -112, -4, -118); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(0, -150); ctx.bezierCurveTo(70, -156, 112, -110, 108, -20); ctx.bezierCurveTo(110, 40, 116, 90, 122 + w * 4, 140); ctx.lineTo(92, 120); ctx.bezierCurveTo(92, 40, 88, -30, 60, -80); ctx.quadraticCurveTo(30, -112, 4, -118); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = rgba(shade(hc, 2.0), 0.25); ctx.lineWidth = 2;
      for (const sx of [-1, 1]) for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.moveTo(sx * (10 + k * 12), -140 + k * 6); ctx.bezierCurveTo(sx * (80 + k * 6), -120, sx * (104 - k * 4), -30, sx * (106 - k * 5), 100); ctx.stroke(); }
      ctx.restore();
    }
  } else {
    // side strands framing face
    hairStrand(ctx, -88, -60, -96 + Math.sin(t * 1.2) * w * 6, 150, 22, -10);
    hairStrand(ctx, 88, -60, 96 + Math.sin(t * 1.1 + 1) * w * 6, 150, 22, 10);
    hairStrand(ctx, -70, -80, -62 + Math.sin(t) * w * 5, 20, 14, -6);
    hairStrand(ctx, 40, -82, 70 + Math.sin(t * 1.4) * w * 5, -10, 16, 8);
    hairStrand(ctx, -20, -86, -40, -20, 15, -6);
    // beanie
    const bc = [112, 42, 48];
    ctx.fillStyle = rgba(bc);
    ctx.beginPath(); ctx.moveTo(-112, -62); ctx.bezierCurveTo(-120, -175, 120, -175, 112, -62); ctx.fill();
    ctx.fillStyle = rgba(shade(bc, 0.8)); ctx.beginPath(); ctx.moveTo(-116, -78); ctx.quadraticCurveTo(0, -102, 116, -78); ctx.lineTo(114, -52); ctx.quadraticCurveTo(0, -76, -114, -52); ctx.fill();
    ctx.strokeStyle = rgba(shade(bc, 0.6), 0.7); ctx.lineWidth = 2;
    for (let i = -10; i <= 10; i++) { ctx.beginPath(); ctx.moveTo(i * 11, -90 + Math.abs(i) * 0.6 * Math.abs(i) / 10 * 2); ctx.lineTo(i * 11, -64 + Math.abs(i) * i * 0 + Math.abs(i) * 0.9); ctx.stroke(); }
    ctx.fillStyle = 'rgba(255,255,255,0.06)'; ctx.beginPath(); ctx.ellipse(-30, -140, 50, 18, -0.2, 0, 7); ctx.fill();
  }
}
function drawHorns(ctx, p) {
  const h = p.horns;
  for (const sx of [-1, 1]) {
    ctx.save(); ctx.translate(sx * 58, -118);
    const L = 150 * h;
    const tip = [sx * (60 + 30 * h) * h, -L], c1 = [sx * 70 * h, -L * 0.15], c2 = [sx * 40 * h, -L * 0.8];
    const w0 = 22 * Math.min(1, h * 1.6);
    if (p.crumble > 0) { ctx.globalAlpha = clamp(1 - p.crumble * 1.3); }
    ctx.beginPath(); ctx.moveTo(-w0, 6); ctx.bezierCurveTo(c1[0] - w0, c1[1], c2[0], c2[1], tip[0], tip[1]);
    ctx.bezierCurveTo(c2[0] + sx * 6, c2[1] + 10, c1[0] + w0, c1[1] + 4, w0, 8); ctx.closePath();
    const g = ctx.createLinearGradient(0, 0, tip[0], tip[1]);
    g.addColorStop(0, 'rgb(25,12,14)'); g.addColorStop(0.6, 'rgb(45,18,20)'); g.addColorStop(1, 'rgb(120,30,20)');
    ctx.fillStyle = g; ctx.shadowColor = 'rgba(255,40,10,0.9)'; ctx.shadowBlur = 25 * h * (1 - p.crumble); ctx.fill(); ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(255,90,40,0.35)'; ctx.lineWidth = 1.5;
    for (let k = 1; k < 6; k++) { const u = k / 6; ctx.beginPath(); ctx.moveTo(-w0 * (1 - u) + c1[0] * u * 0.6, -L * u * 0.7); ctx.lineTo(w0 * (1 - u) + c1[0] * u * 0.6 + sx * 4, -L * u * 0.7 + 4); ctx.stroke(); }
    if (p.cracks > 0) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba([255, 220, 140], p.cracks); ctx.lineWidth = 2; ctx.shadowColor = 'rgba(255,210,120,1)'; ctx.shadowBlur = 12;
      const r = rng(sx > 0 ? 9 : 19); ctx.beginPath(); let x = 0, y = 0; ctx.moveTo(x, y);
      for (let k = 0; k < 10 * p.cracks; k++) { const u = (k + 1) / 10; x = lerp(0, tip[0], u * u) + (r() - .5) * 14; y = lerp(0, tip[1], u); ctx.lineTo(x, y); }
      ctx.stroke(); ctx.restore();
    }
    ctx.restore();
  }
}
