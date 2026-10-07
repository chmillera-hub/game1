'use strict';
// Shot-by-shot choreography. Times are absolute seconds within each part
// and match script.py.

// ---------------------------------------------------------------- shared character states
function singerSinging(t, o = {}) {
  const e = env('singer', t), rd = env('singerRound', t);
  return Object.assign({
    kind: 'singer', time: t, blink: o.eyesOpen ? blink(t, 'singer') : 1, sad: 0.75,
    mouth: e * 0.95, round: rd, tilt: -0.08 + Math.sin(t * 0.8) * 0.05, turn: 0.25 + Math.sin(t * 0.37) * 0.06,
  }, o);
}
function listenerBase(t, o = {}) {
  const [mx, my] = micro(t, 1);
  return Object.assign({ kind: 'listener', time: t, blink: blink(t, 'listener'), gx: mx, gy: my }, o);
}

// lights used on characters in the room
function roomLights(bulb, extra = []) {
  return [
    { world: true, x: bulb[0], y: bulb[1], r: 520, c: 'rgba(255,200,140,0.18)' },
    { world: true, x: 1090, y: 330, r: 420, c: 'rgba(90,130,200,0.22)' },
    ...extra,
  ];
}

// blurred room behind close-ups: drawn and blurred once per shot, then reused
const _bgCache = {};
function blurredRoom(key, t, tx, ty, sc, blur) {
  if (!_bgCache[key]) {
    const tmp = document.createElement('canvas'); tmp.width = W + 400; tmp.height = H + 400;
    const y = tmp.getContext('2d');
    y.translate(200, 200); y.translate(tx, ty); y.scale(sc, sc);
    drawRoom(y, t, { door: 0.85 });
    const cnv = document.createElement('canvas'); cnv.width = W + 400; cnv.height = H + 400;
    const x = cnv.getContext('2d');
    x.filter = `blur(${blur}px)`;
    x.drawImage(tmp, 0, 0);
    _bgCache[key] = cnv;
  }
  g.drawImage(_bgCache[key], -200, -200);
}

// ================================================================= PART 1
const P1 = {
  street(t, u) {
    const z = lerp(1.0, 1.22, ease(clamp(u / 16)));
    setCam(lerp(640, 760, ease(clamp(u / 16))), lerp(360, 420, ease(clamp(u / 16))), z);
    applyCam(g);
    drawStreet(g, t, { windowLight: 0.35 });
    // passers-by, heads down, never stopping
    const walkers = [[-150, 70, 0.9, '#1d2633'], [1450, -60, 0.95, '#2b1d1d'], [200, 55, 0.85, '#20262a'], [1700, -80, 1.0, '#1a1f2a']];
    for (const [x0, v, sc, col] of walkers) {
      const x = x0 + v * t;
      lit(c => person(c, { kind: 'passer', pose: 'stand', x, y: 520, R: 13 * sc, flip: v < 0, turn: 0.7, walking: true, walk: t * 6 + x0,
        umbrella: true, umbrellaColor: col, tilt: 0.25, blink: 0.5, gx: 0, gy: 0.8 }), [], 'rgba(8,10,16,0.72)');
    }
    applyCam(g);
    drawRain(g, t, 1, { x0: -200, y0: -200, w: W + 400, h: H + 400 });
    titleText('THE SPARK IN THE STORM', 300, 54, pulse(u, 2, 10, 1.6, 1.6), { spacing: 6 });
    titleText('Part One · The Song', 360, 28, pulse(u, 3.5, 10, 1.6, 1.6), { italic: true });
  },

  street_listener(t, u) {
    // he walks in from the left, hears the song, stops, turns toward the window
    const x = kf(t, [[16, 120], [22, 600], [28.4, 600], [31.6, 900]]);
    const walking = t < 22 || t > 28.4;
    setCam(clamp(x + 110, 330, 860), 440, 3.0);
    applyCam(g);
    drawStreet(g, t, { windowLight: 0.4 });
    const look = sstep(t, 22.3, 23.3);
    const st = listenerBase(t, {
      pose: 'stand', x, y: 498, R: 9.5, hood: 1, walking, walk: t * 6.5,
      turn: lerp(0.75, 0.55, look), tilt: lerp(0.28, -0.05, look),
      gy: lerp(0.8, -0.1, look), gx: lerp(0.2, 0.9, look),
      browUp: look * 0.6 * (1 - sstep(t, 26, 28)), sad: sstep(t, 25, 27) * 0.5,
      mouth: look * 0.12, dilate: 1 + look * 0.3,
    });
    lit(c => person(c, st), [
      { world: true, x: STREET.lamp[0], y: STREET.lamp[1] + 40, r: 260, c: 'rgba(255,200,140,0.25)' },
      { world: true, x: STREET.win[0] + 60, y: STREET.win[1] + 50, r: 200, c: `rgba(255,190,110,${0.15 + 0.2 * look})` },
    ], 'rgba(10,14,24,0.35)');
    applyCam(g);
    drawRain(g, t, 1, { x0: -200, y0: -200, w: W + 400, h: H + 400 });
  },

  room_wide(t, u) {
    setCam(lerp(640, 660, u / 18), lerp(360, 375, u / 18), lerp(1.0, 1.08, u / 18));
    applyCam(g);
    const door = kf(t, [[32, 0.2], [34.2, 0.85]]);
    const R = { x: kf(t, [[32, 200], [36.5, 200], [43.5, 430]]), y: kf(t, [[32, 565], [36.5, 565], [43.5, 625]]),
      R: kf(t, [[32, 30], [36.5, 30], [43.5, 33]]) };
    const inside = sstep(t, 37, 42);
    const room = drawRoom(g, t, { door });
    // singer by the window
    const sg = singerSinging(t, { pose: 'sit', x: 935, y: 410, R: 32 });
    lit(c => person(c, sg), roomLights(room.bulb), 'rgba(10,12,20,0.25)');
    // the listener: a silhouette in the doorway, then lit as he steps in
    if (t > 33.2) {
      const walking = t > 36.5 && t < 43.5;
      const st = listenerBase(t, {
        pose: 'stand', x: R.x, y: R.y - 8 * R.R, R: R.R, walking, walk: (t - 36.5) * 5,
        turn: 0.55, gx: 0.9, gy: 0.1, sad: 0.35 + inside * 0.2, browUp: 0.3, mouth: 0.1 * inside,
      });
      applyCam(g);
      g.save(); g.globalAlpha = sstep(t, 33.2, 34.2);
      lit(c => person(c, st), roomLights(room.bulb), `rgba(5,8,14,${lerp(0.88, 0.25, inside)})`);
      g.restore();
    }
    applyCam(g);
    roomLight(g, t, room.bulb, 1);
  },

  singer_close(t, u) {
    setCam(lerp(640, 655, u / 22), lerp(380, 370, u / 22), lerp(1.0, 1.12, u / 22));
    applyCam(g);
    // blurred room behind her
    blurredRoom('singer_close', 50, -500, -300, 2, 10);
    applyCam(g);
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(-200, -200, W + 400, H + 400);
    const tearDrops = drops(t, [[64.5, 1]], 2.6);
    const sg = singerSinging(t, { pose: 'bust', x: 620, y: 300, R: 150, tears: sstep(t, 60, 64) * 0.6, drops: tearDrops });
    lit(c => person(c, sg), [
      { x: 1200, y: 250, r: 900, c: 'rgba(90,130,210,0.22)' },
      { x: 200, y: 0, r: 800, c: 'rgba(255,200,140,0.2)' },
    ], 'rgba(10,12,22,0.18)');
    // rain shadows sliding across her from the window
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.save(); g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 10; i++) {
      const x = 700 + hrand(i + 1) * 500, y = ((hrand(i + 2) * 900 + t * (20 + hrand(i) * 40)) % 900) - 100;
      g.fillStyle = 'rgba(120,160,230,0.05)'; g.fillRect(x, y, 3, 60);
    }
    g.restore();
  },

  memories(t, u) {
    // three faded memories of the singer's life
    const panel = u < 8 ? 0 : u < 16 ? 1 : 2, pu = u - panel * 8;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    setCam(640 + pu * 4, 360, 1.0 + pu * 0.01 * (panel === 2 ? -1 : 1) + (panel === 2 ? 0.12 : 0));
    applyCam(g);
    if (panel === 0) {
      g.fillStyle = '#2a2622'; g.fillRect(-100, -100, W + 200, 720);
      g.fillStyle = '#3a342c'; g.fillRect(-100, 600, W + 200, 300);
      // door with a sign; it closes
      const shut = sstep(pu, 3.6, 4.1);
      g.fillStyle = '#e8c890'; g.fillRect(700, 190, 200, 410);
      g.fillStyle = '#3a2a1f'; g.fillRect(700 + 200 * (1 - shut), 190, 200 * shut, 410);
      g.strokeStyle = '#1d1510'; g.lineWidth = 10; g.strokeRect(700, 190, 200, 410);
      g.fillStyle = '#e9e1cc'; g.fillRect(715, 120, 170, 50);
      g.fillStyle = '#7a1f1a'; g.font = 'bold 22px "Liberation Sans"'; g.fillText('NO VACANCY', 728, 153);
      const st = { kind: 'singer', pose: 'stand', x: 540, y: 600 - 8 * 42, R: 42, turn: 0.6, gx: 0.9, gy: 0,
        blink: blink(t, 'singer'), sad: 0.4 + shut * 0.5, browUp: shut * 0.2 * (1 - sstep(pu, 5, 6)),
        tilt: lerp(0, 0.18, sstep(pu, 4.5, 6.5)), time: t, mouth: shut * 0.1 * (1 - sstep(pu, 4.6, 5)) };
      if (shut > 0.5) { st.gy = lerp(0, 0.7, sstep(pu, 4.6, 6.5)); st.gx = lerp(0.9, 0.2, sstep(pu, 4.6, 6.5)); }
      lit(c => { person(c, st); c.fillStyle = '#3d3028'; c.fillRect(st.x - 92, 520, 46, 70); }, [], null);
    } else if (panel === 1) {
      g.fillStyle = '#2e2a26'; g.fillRect(-100, -100, W + 200, 720);
      g.fillStyle = 'rgba(0,0,0,0.25)'; for (let k = 0; k < 16; k++) g.fillRect(-100, k * 40, W + 200, 3);
      g.fillStyle = '#3c3731'; g.fillRect(-100, 600, W + 200, 300);
      const st = { kind: 'singer', pose: 'sit', crate: false, x: 640, y: 600 - 4.9 * 40, R: 40, turn: 0.1,
        blink: blink(t, 'singer'), sad: 0.8, time: t, tilt: 0.05, droop: 0.2 };
      // her eyes follow each passer-by hoping someone stops
      const gxs = Math.sin(pu * 1.3) * 0.9;
      st.gx = gxs; st.gy = 0.35;
      lit(c => {
        person(c, st);
        // outstretched cup
        c.fillStyle = '#d8d0bf'; c.fillRect(640 + 30, 600 - 2.2 * 40, 26, 30);
      }, [], null);
      // legs of passers-by crossing in front
      applyCam(g);
      for (let i = 0; i < 6; i++) {
        const dir = i % 2 ? -1 : 1, sp = 260 + i * 40;
        const x = dir > 0 ? -200 + ((pu * sp + i * 400) % 1700) : W + 200 - ((pu * sp + i * 300) % 1700);
        for (const s of [-1, 1]) {
          const ph = Math.sin(pu * 7 + i + (s > 0 ? Math.PI : 0)) * 40;
          g.strokeStyle = '#121010'; g.lineWidth = 34; g.lineCap = 'round';
          g.beginPath(); g.moveTo(x + s * 18, 380); g.lineTo(x + s * 18 + ph, 700); g.stroke();
        }
      }
    } else {
      g.fillStyle = '#16151a'; g.fillRect(-300, -300, W + 600, 1020);
      g.fillStyle = '#26252a'; g.fillRect(-300, 560, W + 600, 400);
      g.fillStyle = '#121216'; g.fillRect(-300, 590, W + 600, 300);
      g.fillStyle = '#0c0c0f'; g.fillRect(830, 120, 10, 450);
      g.save(); g.globalCompositeOperation = 'lighter';
      const lg = g.createRadialGradient(835, 130, 0, 835, 130, 420);
      lg.addColorStop(0, 'rgba(255,220,170,0.4)'); lg.addColorStop(1, 'rgba(255,220,170,0)');
      g.fillStyle = lg; g.beginPath(); g.moveTo(820, 130); g.lineTo(850, 130); g.lineTo(1050, 600); g.lineTo(600, 600); g.fill(); g.restore();
      const st = { kind: 'singer', pose: 'sit', crate: false, x: 760, y: 590 - 4.9 * 34, R: 34, turn: -0.2, tilt: 0.3,
        blink: 1, sad: 0.9, time: t, tears: 0.5 };
      lit(c => person(c, st), [], null);
      // an eviction notice blowing past in the wind
      const px = kf(pu, [[0, 1400], [8, -200]]), py = 520 + Math.sin(pu * 2) * 40;
      g.save(); g.translate(px, py); g.rotate(pu * 2.5);
      g.fillStyle = '#d8d0bc'; g.fillRect(-25, -32, 50, 64);
      g.fillStyle = '#7a1f1a'; g.font = 'bold 9px "Liberation Sans"'; g.fillText('EVICTION', -21, -18);
      g.restore();
      applyCam(g);
      drawRain(g, t, 0.8, { x0: -300, y0: -300, w: W + 600, h: H + 600 });
    }
    // sepia memory look: wash, flicker, soft edges, crossfades
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.save(); g.globalCompositeOperation = 'color'; g.fillStyle = 'rgb(150,115,80)'; g.fillRect(0, 0, W, H); g.restore();
    g.fillStyle = `rgba(30,20,10,${0.18 + 0.05 * noise1(t * 8)})`; g.fillRect(0, 0, W, H);
    const vg = g.createRadialGradient(W / 2, H / 2, 200, W / 2, H / 2, 760);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(10,6,2,0.85)');
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
    fade(1 - sstep(pu, 0, 0.8) + sstep(pu, 7.3, 8));
  },

  listener_close(t, u) {
    setCam(640, 360 - u * 0.5, lerp(1.0, 1.1, u / 22));
    applyCam(g);
    blurredRoom('listener_close', 96, -1200, -400, 2.2, 12);
    applyCam(g);
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(-200, -200, W + 400, H + 400);
    // the storm begins to seep in behind him
    const seep = sstep(t, 111, 118);
    if (seep > 0) drawStorm(g, t, { amount: seep * 0.9, cx: 640, cy: 330 });
    const look = [[96, 0.75], [103.6, 0.75], [104, 0.1], [106.4, 0.1], [106.8, -0.5], [108.2, -0.5], [108.6, 0.7]];
    const lookY = [[96, 0.05], [103.6, 0.05], [104, 0.6], [106.4, 0.6], [106.8, 0.2], [108.2, 0.2], [108.6, 0.0]];
    const st = listenerBase(t, {
      pose: 'bust', x: 640, y: 300, R: 155, turn: 0.18,
      gx: kf(t, look) + micro(t, 3)[0], gy: kf(t, lookY) + micro(t, 3)[1],
      tears: sstep(t, 98, 108), sad: 0.4 + sstep(t, 100, 110) * 0.5, browUp: 0.15,
      mouth: 0.06 + 0.06 * sstep(t, 108, 112), tremble: sstep(t, 108, 112), dilate: 1.25,
      drops: drops(t, [[110.2, 1], [113.4, -1], [116.5, 1]], 2.2), wind: seep,
    });
    lit(c => person(c, st), [
      { x: 1250, y: 300, r: 900, c: 'rgba(90,130,210,0.2)' },
      { x: 150, y: 50, r: 800, c: 'rgba(255,200,140,0.22)' },
      { x: 640, y: 900, r: 700, c: `rgba(60,20,60,${0.35 * seep})` },
    ], 'rgba(10,12,22,0.15)');
  },

  storm(t, u) {
    const shake = 2 * sstep(t, 140, 160);
    setCam(640 + noise1(t * 3) * shake, 350 + noise1(t * 3 + 5) * shake, lerp(1.0, 1.12, u / 44), Math.sin(t * 0.3) * 0.02 * sstep(t, 130, 160));
    applyCam(g);
    const [L, idx] = strike(t, TL.thunder);
    drawStorm(g, t, { amount: 1, flicker: true, speed: 1 + sstep(t, 118, 160) * 1.5, red: sstep(t, 145, 162) * 0.6 });
    // memories painted into the clouds, revealed by the lightning
    for (let i = 0; i < 5; i++) {
      const tt = TL.thunder[i]; if (tt === undefined) continue;
      const a = sstep(t, tt - 0.05, tt + 0.1) * (1 - sstep(t, tt + 1.4, tt + 2.6));
      const pos = [[300, 180], [990, 200], [260, 470], [1010, 480], [640, 120]][i];
      memoryInCloud(g, i, t, a * 0.85, pos[0], pos[1], 0.9);
    }
    if (idx >= 0) lightningBolt(g, idx + 3, [380, 900, 200, 1080, 640, 300, 1000, 500, 700][idx % 9], -50, 600, L);
    const fury = sstep(t, 146, 160);
    const st = listenerBase(t, {
      pose: 'bust', x: 640, y: 320, R: 118, turn: 0.05 + noise1(t * 0.5) * 0.05,
      gx: noise1(t * 0.8) * 0.4, gy: 0.25 + noise1(t * 0.6 + 2) * 0.2,
      tears: 1, sad: lerp(0.9, 0.3, fury), angry: fury * 0.8, squint: fury * 0.5,
      mouth: 0.05, tremble: 1 - fury * 0.5, smile: -0.3 - fury * 0.4, grit: sstep(t, 149, 152),
      drops: drops(t, [[119, -1], [123.5, 1], [128, -1], [133, 1], [137.5, -1], [142, 1], [146, -1], [150, 1], [154, -1], [158, 1]], 2.0),
      wind: 1, blink: t > 150 && t < 151 ? 1 : blink(t, 'listener'),
      horns: sstep(t, 156, 162) * 0.15,
    });
    lit(c => person(c, st), [
      { x: 640, y: -100, r: 900, c: `rgba(220,215,255,${0.55 * L})` },
      { x: 640, y: 900, r: 700, c: `rgba(150,20,30,${0.3 * sstep(t, 140, 162)})` },
    ], `rgba(15,10,25,${0.35 - 0.2 * L})`);
    flash(L * 0.28);
  },

  horns(t, u) {
    const shake = 2 + 4 * sstep(t, 170, 178);
    setCam(640 + noise1(t * 4) * shake, lerp(350, 300, ease(u / 16.5)) + noise1(t * 4 + 7) * shake, lerp(1.12, 1.55, ease(u / 16.5)));
    applyCam(g);
    const [L, idx] = strike(t, TL.thunder);
    drawStorm(g, t, { amount: 1, flicker: true, speed: 2.5, red: 0.6 + 0.4 * sstep(t, 166, 176) });
    // the giant demon of storm rising behind him
    drawDemon(g, t, sstep(t, 164, 175) * 0.8, 640, lerp(420, 230, sstep(t, 164, 176)), lerp(0.7, 1.05, sstep(t, 164, 178)),
      { eyes: sstep(t, 171, 175) });
    if (idx >= 0) lightningBolt(g, idx + 7, [300, 980, 520][idx % 3], -60, 650, L);
    const st = listenerBase(t, {
      pose: 'bust', x: 640, y: 330, R: 118, turn: 0.02,
      gx: 0, gy: lerp(0.3, -0.1, sstep(t, 170, 174)),
      tears: 1, sad: 0.35, angry: 0.95, squint: 0.4, smile: -0.6, grit: 1,
      tremble: 0.6,
      drops: drops(t, [[163, 1], [167, -1], [171, 1], [174.5, -1]], 2.0),
      wind: 1.4, horns: lerp(0.15, 1, sstep(t, 162.5, 174)),
      red: sstep(t, 168, 175), underlight: sstep(t, 164, 176),
    });
    lit(c => person(c, st), [
      { x: 640, y: -100, r: 900, c: `rgba(220,215,255,${0.5 * L})` },
      { x: 640, y: 1000, r: 800, c: `rgba(200,20,10,${0.35 + 0.25 * sstep(t, 166, 176)})` },
    ], `rgba(15,5,10,${0.35 - 0.2 * L})`);
    flash(L * 0.3);
    flash(sstep(t, 177.6, 178.5) * 0.4, '255,40,20');
  },

  black(t, u) { g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#000'; g.fillRect(0, 0, W, H); },

  card(t, u) {
    g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    titleText('End of Part One', 340, 34, pulse(u, 0.5, 4.5, 1, 1), { italic: true });
    const a = pulse(u, 5, 10, 1.2, 1.0);
    titleText('Part Two', 320, 30, a, { italic: true });
    titleText('THE SPARK', 390, 58, a, { spacing: 8 });
    setCam(640, 360, 1); applyCam(g);
    drawSpark(g, 640, 440, 2.4 * a, t, {});
  },
};

// ================================================================= PART 2
function stormListener(t, o) {
  return listenerBase(t, Object.assign({ pose: 'bust', x: 640, y: 330, R: 118, turn: 0.02, wind: 1.2 }, o));
}

const P2 = {
  storm_peak(t, u) {
    const shake = 3;
    setCam(640 + noise1(t * 4) * shake, 320 + noise1(t * 4 + 7) * shake, 1.3);
    applyCam(g);
    const [L, idx] = strike(t, TL.thunder);
    const slow = 1 - 0.85 * sstep(t, 23.5, 24.2);
    drawStorm(g, t, { amount: 1, flicker: t < 24, speed: 2.5 * slow, red: 0.9 });
    drawDemon(g, t, 0.72, 640, 230, 1.05, { eyes: 1 });
    // flashes of what the world does, again and again
    for (let i = 0; i < TL.thunder.length; i++) {
      const tt = TL.thunder[i];
      const a = sstep(t, tt - 0.05, tt + 0.1) * (1 - sstep(t, tt + 1.2, tt + 2.2));
      memoryInCloud(g, [0, 3, 1, 4][i], t, a * 0.75, [[260, 200], [1020, 230], [240, 520], [1040, 500]][i][0], [[260, 200], [1020, 230], [240, 520], [1040, 500]][i][1], 0.8);
    }
    if (idx >= 0) lightningBolt(g, idx + 11, [260, 1010, 420, 860][idx % 4], -60, 650, L);
    const st = stormListener(t, {
      gx: noise1(t * 0.9) * 0.3, gy: 0.2, tears: 1, sad: 0.5, angry: 0.85, squint: 0.4, smile: -0.55,
      grit: 1 - sstep(t, 22, 24.5), tremble: 0.8, horns: 1, red: 1, underlight: 1,
      drops: drops(t, [[1, 1], [5, -1], [9, 1], [13, -1], [17, 1], [21, -1]], 2.0),
    });
    lit(c => person(c, st), [
      { x: 640, y: -100, r: 900, c: `rgba(220,215,255,${0.5 * L})` },
      { x: 640, y: 1000, r: 800, c: 'rgba(200,20,10,0.55)' },
    ], `rgba(15,5,10,${0.35 - 0.2 * L})`);
    flash(L * 0.3);
    fade(1 - sstep(u, 0, 2));
  },

  spark_appear(t, u) {
    // the storm all but stops; something tiny shines in the darkest corner
    const toward = sstep(t, 31, 40);
    setCam(lerp(640, 540, toward), lerp(320, 360, toward), lerp(1.3, 1.4, toward));
    applyCam(g);
    drawStorm(g, t, { amount: 1, tt: 24 * 2.5 + (t - 24) * 0.25, red: lerp(0.9, 0.3, sstep(t, 28, 38)) });
    drawDemon(g, t, lerp(0.72, 0.6, sstep(t, 28, 40)), 640, 230, 1.05, { eyes: lerp(1, 0.3, sstep(t, 30, 38)) });
    const sp = [250, 470];
    drawSpark(g, sp[0], sp[1], lerp(0, 1.6, sstep(t, 24.3, 25.5)) + 0.3 * sstep(t, 30, 40), t, { rays: sstep(t, 32, 40) * 0.5 });
    // eyes search, then find it
    const gxk = [[24, 0], [24.6, 0], [24.8, -0.7], [25.6, -0.7], [25.8, 0.8], [26.8, 0.8], [27.0, 0.1], [27.6, 0.1], [27.9, -0.85], [40, -0.85]];
    const gyk = [[24, 0.2], [24.8, 0.4], [25.8, -0.3], [27.0, 0.0], [27.9, 0.55], [40, 0.55]];
    const found = sstep(t, 28, 30);
    const st = stormListener(t, {
      gx: kf(t, gxk), gy: kf(t, gyk), turn: lerp(0.02, -0.25, sstep(t, 28, 33)), tilt: lerp(0, 0.1, sstep(t, 28, 33)),
      tears: 1, sad: lerp(0.5, 0.75, found), angry: lerp(0.85, 0, sstep(t, 26, 34)), squint: lerp(0.4, 0, sstep(t, 26, 32)),
      smile: lerp(-0.55, 0, sstep(t, 27, 36)), mouth: 0.1 + found * 0.08, tremble: lerp(0.8, 0.1, found),
      horns: 1, red: 1 - sstep(t, 29, 37), underlight: 1 - sstep(t, 28, 38), browUp: found * 0.5,
      dilate: 1 + found * 0.45, wind: lerp(1.2, 0.2, sstep(t, 24, 26)),
      blink: t > 33.5 && t < 33.75 ? blink(t, 'listener') : (t > 24 && t < 33 ? 0 : blink(t, 'listener')),
    });
    lit(c => person(c, st), [
      { x: 640, y: 1000, r: 800, c: `rgba(200,20,10,${0.55 * (1 - sstep(t, 28, 38))})` },
      { world: true, x: sp[0], y: sp[1], r: 700, c: `rgba(255,220,160,${0.22 * sstep(t, 25, 38)})` },
    ], 'rgba(15,5,10,0.3)');
    // desaturate the storm moment it stops
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.save(); g.globalCompositeOperation = 'saturation'; g.fillStyle = `rgba(128,128,128,${0.5 * pulse(t, 24, 40, 0.3, 6)})`; g.fillRect(0, 0, W, H); g.restore();
    flash(pulse(t, 24.2, 24.9, 0.05, 0.6) * 0.15, '255,240,210');
  },

  spark_close(t, u) {
    setCam(640, 360, lerp(1.0, 1.35, ease(u / 22)));
    applyCam(g);
    const surge = pulse(t, 56.8, 60.5, 1.0, 2.0); // the storm tries to smother it
    drawStorm(g, t, { amount: 1, cx: 640, cy: 360, tt: 60 + (t - 24) * (0.25 + 1.5 * surge), red: 0.2 * surge });
    // clouds closest to the light get golden edges
    g.save(); g.globalCompositeOperation = 'lighter';
    const rim = g.createRadialGradient(640, 360, 20, 640, 360, 330);
    rim.addColorStop(0, `rgba(255,210,140,${0.15 + 0.15 * sstep(t, 44, 56)})`); rim.addColorStop(1, 'rgba(255,200,120,0)');
    g.fillStyle = rim; g.fillRect(0, 0, W, H); g.restore();
    // a darkness that closes in, then is pushed back
    const close = 1 - 0.5 * surge;
    const dk = g.createRadialGradient(640, 360, 120 * close + 40 * sstep(t, 59, 62), 640, 360, 640);
    dk.addColorStop(0, 'rgba(0,0,0,0)'); dk.addColorStop(1, `rgba(5,2,8,${0.6 + 0.3 * surge})`);
    g.fillStyle = dk; g.fillRect(-300, -300, W + 600, H + 600);
    motes(g, t, 640, 360, 34, 520, { inward: true, life: 6, alpha: 0.5 });
    drawSpark(g, 640, 360, 3.2 + 1.2 * sstep(t, 59, 62) + 0.8 * surge, t, { rays: 0.6 + 0.4 * sstep(t, 46, 56) + 0.6 * sstep(t, 59, 62) });
    fade(1 - sstep(u, 0, 0.6));
  },

  transform(t, u) {
    setCam(640, lerp(330, 345, u / 38), lerp(1.3, 1.15, ease(clamp(u / 30))));
    applyCam(g);
    const gold = sstep(t, 78, 94), room = sstep(t, 95, 100);
    drawStorm(g, t, { amount: 1, tt: 70 + (t - 62) * 0.35, gold, red: 0.3 * (1 - sstep(t, 66, 76)) });
    drawDemon(g, t, 0.6 * (1 - sstep(t, 72, 84)), 640, 230 - sstep(t, 72, 84) * 60, 1.05 + sstep(t, 72, 84) * 0.2, { eyes: 0.3 * (1 - sstep(t, 70, 74)), gold: sstep(t, 72, 82) });
    // the spark travels from the storm into his chest
    const travel = sstep(t, 62, 67.5);
    const sx = lerp(250, 640, travel), sy = lerp(470, 330 + 2.3 * 118, travel) - Math.sin(travel * Math.PI) * 60;
    const absorbed = t > 67.5;
    if (!absorbed) drawSpark(g, sx, sy, 2.2, t, { rays: 0.4 });
    const j = sstep(t, 80, 90);
    const glow = sstep(t, 67, 70);
    const crack = sstep(t, 70, 75), crumble = sstep(t, 74, 82);
    const st = stormListener(t, {
      gx: lerp(-0.85, 0, sstep(t, 63, 67)), gy: lerp(0.55, 0.7, sstep(t, 63, 67)) * (1 - sstep(t, 70, 74)),
      turn: lerp(-0.25, 0, sstep(t, 63, 68)), tilt: lerp(0.1, 0.08, sstep(t, 63, 68)) * (1 - sstep(t, 72, 78)),
      tears: 1, sad: lerp(0.75, 0.3, sstep(t, 75, 92)), browUp: lerp(0.5, 0.1, sstep(t, 70, 80)),
      smile: sstep(t, 88, 95) * 0.35, mouth: 0.1 * (1 - sstep(t, 82, 88)), tremble: 0.2 * (1 - sstep(t, 70, 80)),
      horns: 1, crack, crumble, red: 0, underlight: 0, dilate: 1.4,
      blink: t > 83 && t < 88.5 ? 1 - sstep(t, 87.5, 88.5) : blink(t, 'listener'),
      jesus: j, halo: sstep(t, 84, 94), gold: sstep(t, 86, 92), wind: lerp(0.2, 0, sstep(t, 75, 85)),
      drops: drops(t, [[71, 1], [79, -1]], 2.2),
    });
    lit(c => person(c, st), [
      { x: 640, y: 600, r: 700, c: `rgba(255,220,160,${0.35 * glow})` },
      { x: 640, y: 0, r: 900, c: `rgba(255,235,190,${0.3 * gold})` },
    ], `rgba(15,8,10,${0.3 * (1 - gold)})`);
    // embers rising where the horns crumble
    if (crumble > 0 && crumble < 1) {
      applyCam(g);
      for (const s of [-1, 1]) motes(g, t, 640 + s * 118 * 0.9, 330 - 118 * 1.5, 30, 140, { life: 3, rise: 300, color: s > 0 ? '255,190,110' : '255,210,140', alpha: Math.sin(crumble * Math.PI) });
    }
    chestGlow(640, 330 + 2.3 * 118, 300, glow * (0.7 + 0.3 * j), t);
    // the moment of change hidden in light
    flash(pulse(t, 81, 89, 2.5, 4.0) * 0.85, '255,246,225');
    // fade into the room
    if (room > 0) {
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = room;
      g.fillStyle = '#000'; g.fillRect(0, 0, W, H); g.globalAlpha = 1;
    }
  },

  kneel(t, u) {
    setCam(lerp(860, 835, u / 21), lerp(455, 470, u / 21), lerp(1.55, 1.75, u / 21));
    applyCam(g);
    const room = drawRoom(g, t, { door: 0.85 });
    const kneel = sstep(t, 106, 110);
    const singing = t < 110.2;
    const looks = sstep(t, 110.8, 111.6);
    const sg = singerSinging(t, {
      pose: 'sit', x: 935, y: 410, R: 32,
      blink: singing ? 1 : (t < 110.8 ? 1 : blink(t, 'singer')),
      gx: -0.9 * looks, gy: 0.15 * looks, turn: lerp(0.25, -0.35, looks), tilt: lerp(-0.08, 0.04, looks),
      browUp: looks * 0.6 * (1 - sstep(t, 113, 116)), sad: 0.75, tears: sstep(t, 112, 116),
      smile: sstep(t, 117, 119) * 0.15,
    });
    if (!singing) { sg.mouth = env('singer', t) * 0.8; sg.round = 0.2; }
    lit(c => person(c, sg), roomLights(room.bulb, [{ world: true, x: 720, y: 470, r: 260, c: 'rgba(255,220,160,0.25)' }]), 'rgba(10,12,20,0.2)');
    const R = 33;
    const jx = kf(t, [[100, 690], [104, 730]]);
    const st = listenerBase(t, {
      pose: 'kneel', x: jx, y: 640 - 8 * R + kneel * 2.3 * R, R, turn: 0.6, gx: 0.85, gy: lerp(0.1, 0.35, kneel),
      jesus: 1, halo: 0.75, gold: 1, sad: 0.25, smile: 0.25, kneel, walking: t < 104, walk: (t - 100) * 5,
      tears: 0.6, blink: blink(t, 'jesus'),
    });
    applyCam(g);
    lit(c => person(c, st), roomLights(room.bulb, [{ world: true, x: jx, y: st.y + 2.3 * R, r: 220, c: 'rgba(255,225,170,0.35)' }]), 'rgba(10,12,20,0.1)');
    applyCam(g);
    roomLight(g, t, room.bulb, 0.9);
    chestGlow(jx, st.y + 2.3 * R, 120, 0.8, t);
    fade(1 - sstep(u, 0, 1.2));
  },

  jesus_close(t, u) {
    setCam(640, 360, lerp(1.0, 1.06, u / 7));
    applyCam(g);
    blurredRoom('jesus_close', 121, -1300, -500, 2.2, 12);
    applyCam(g);
    g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(-200, -200, W + 400, H + 400);
    const st = listenerBase(t, {
      pose: 'bust', x: 600, y: 320, R: 150, turn: 0.35, gx: 0.8, gy: 0.3, tilt: 0.05,
      jesus: 1, halo: 0.8, gold: 1, sad: 0.2, smile: 0.3, tears: 0.55,
      mouth: env('jesus', t) * 0.85, blink: blink(t, 'jesus'),
    });
    lit(c => person(c, st), [
      { x: 300, y: 50, r: 900, c: 'rgba(255,210,150,0.25)' },
      { x: 1200, y: 300, r: 800, c: 'rgba(90,130,210,0.15)' },
    ], 'rgba(10,12,20,0.08)');
    chestGlow(600, 320 + 2.3 * 150, 380, 0.55, t);
  },

  singer_reply(t, u) {
    const pull = sstep(t, 139, 145);
    setCam(lerp(640, 760, pull), lerp(360, 420, pull), lerp(1.0, 0.82, pull));
    applyCam(g);
    blurredRoom('singer_reply', 128, -500, -300, 2, 10);
    applyCam(g);
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(-400, -400, W + 800, H + 800);
    const singing = t > 132;
    const sg = singerSinging(t, {
      pose: 'bust', x: 640, y: 310, R: 150, turn: lerp(-0.3, 0.2, sstep(t, 131, 134)),
      blink: singing ? (t < 132.4 ? sstep(t, 131.6, 132.4) : 1) : blink(t, 'singer'),
      gx: -0.8, gy: 0.2, sad: lerp(0.7, 0.45, sstep(t, 128, 132)),
      smile: sstep(t, 129.5, 131) * 0.35 * (singing ? 0.4 : 1), tears: 0.9, tremble: singing ? 0 : 0.8,
      drops: drops(t, [[128.6, -1], [130.8, 1]], 2.4),
    });
    if (!singing) { sg.mouth = 0.04; sg.round = 0; }
    lit(c => person(c, sg), [
      { x: 1200, y: 250, r: 900, c: 'rgba(90,130,210,0.2)' },
      { x: 0, y: 300, r: 900, c: 'rgba(255,215,160,0.28)' },
    ], 'rgba(10,12,22,0.15)');
    // his open hand offers a small light; it floats to rest over her heart
    const hand = pulse(t, 135, 143, 1.2, 1.5);
    applyCam(g);
    if (hand > 0) {
      const hx = lerp(-80, 250, hand), hy = lerp(820, 640, hand);
      g.save(); g.translate(hx, hy); g.rotate(-0.35);
      g.fillStyle = '#efe7d8'; g.beginPath(); g.ellipse(-150, 40, 150, 70, 0, 0, TAU); g.fill(); // sleeve
      g.fillStyle = '#d8a283';
      g.beginPath(); g.ellipse(-10, 10, 62, 36, 0, 0, TAU); g.fill();                     // palm, facing up
      for (let k = 0; k < 4; k++) { g.beginPath(); g.roundRect(30 + k * 2, -24 + k * 15, 58 - k * 6, 15, 8); g.fill(); } // fingers
      g.beginPath(); g.ellipse(-5, -28, 36, 13, -0.5, 0, TAU); g.fill();                  // thumb
      g.strokeStyle = 'rgba(120,70,50,0.4)'; g.lineWidth = 2;
      g.beginPath(); g.arc(-10, 12, 34, Math.PI * 1.1, Math.PI * 1.8); g.stroke();
      g.restore();
    }
    const fly = sstep(t, 137, 141);
    const lx = lerp(250, 640, fly), ly = lerp(615, 310 + 2.4 * 150, fly) - Math.sin(fly * Math.PI) * 80;
    if (t > 136) {
      drawSpark(g, lx, ly, 1.8 + fly * 0.4, t, { rays: 0.3 });
      chestGlow(lx, ly, 160 + 60 * fly, 0.5 * sstep(t, 136, 137), t);
    }
  },

  leave_room(t, u) {
    setCam(lerp(600, 520, u / 13), 380, 1.05);
    applyCam(g);
    const door = 0.85;
    const room = drawRoom(g, t, { door });
    const sg = singerSinging(t, { pose: 'sit', x: 935, y: 410, R: 32 });
    lit(c => person(c, sg), roomLights(room.bulb), 'rgba(10,12,20,0.2)');
    chestGlow(935, 410 + 2.4 * 32, 80, 0.7, t); // the light she keeps
    const R = 33;
    const kneel = 1 - sstep(t, 145, 147.2);
    const x = kf(t, [[147.2, 730], [152.4, 230], [155, 230], [157.5, 200]]);
    const yb = kf(t, [[147.2, 640], [152.4, 575], [155, 575], [157.5, 565]]);
    const Rr = kf(t, [[147.2, 33], [152.4, 30], [157.5, 29]]);
    const walking = (t > 147.2 && t < 152.4) || t > 155;
    const lookBack = pulse(t, 152.6, 155, 0.6, 0.6);
    const out = sstep(t, 155.3, 157.6);
    const st = listenerBase(t, {
      pose: 'kneel', x, y: yb - 8 * Rr + kneel * 2.3 * Rr, R: Rr, jesus: 1, halo: 0.7, gold: 1, kneel,
      walking, walk: t * 5, turn: lerp(-0.7, 0.75, lookBack), back: t > 147.5 && lookBack < 0.3, gx: 0.8, gy: 0.1, smile: 0.25,
      blink: blink(t, 'jesus'),
    });
    applyCam(g);
    g.save(); g.globalAlpha = 1 - out;
    lit(c => person(c, st), roomLights(room.bulb), `rgba(5,8,14,${lerp(0.1, 0.6, sstep(t, 150, 155))})`);
    chestGlow(x, st.y + 2.3 * Rr, 100, 0.7, t);
    g.restore();
    applyCam(g);
    roomLight(g, t, room.bulb, 0.9);
  },

  night_walk(t, u) {
    setCam(kf(t, [[158, 900], [166, 700], [172, 680], [177.5, 1060], [184, 1060], [190, 640]]),
      kf(t, [[158, 470], [184, 480], [190, 330]]), kf(t, [[158, 1.8], [177.5, 1.8], [184, 2.0], [190, 1.0]]));
    applyCam(g);
    const clear = sstep(t, 163, 180);
    drawStreet(g, t, { clear, wet: 1 - 0.5 * clear, windowLight: 0.4, doorAjar: 0.5 });
    // someone asleep in the shop doorway
    const helped = sstep(t, 180, 183);
    const hd = { kind: 'huddled', pose: 'sit', crate: false, x: 1175, y: 568 - 4.9 * 12, R: 12, turn: -0.4, tilt: 0.35 - helped * 0.3,
      blink: helped > 0.5 ? blink(t, 'huddled') : 1, sad: 0.8, gx: -0.8, gy: -0.2 * helped, time: t, browUp: helped * 0.5, smile: sstep(t, 184, 186) * 0.2 };
    lit(c => person(c, hd), [], 'rgba(10,12,20,0.45)');
    // he walks away from the door, carrying the light
    const R = 13;
    const jx = kf(t, [[158, 965], [190, 80]]);
    const jy = kf(t, [[158, 520], [160, 568]]) - 8 * R;
    const st = listenerBase(t, { pose: 'stand', x: jx, y: jy, R, jesus: 1, halo: 0.6, gold: 1, walking: true, walk: t * 5.2,
      flip: true, turn: 0.7, gx: 0.8, smile: 0.2 });
    lit(c => person(c, st), [{ world: true, x: jx, y: jy + 30, r: 120, c: 'rgba(255,225,170,0.35)' }], 'rgba(10,12,20,0.25)');
    chestGlow(jx, jy + 2.3 * R, 70, 0.8, t);
    // a stranger with an umbrella walks toward him; the light passes on
    const px = kf(t, [[160, -60], [176, 1100], [178.5, 1140]]);
    const stopped = t > 176;
    const crouch = sstep(t, 178.5, 180.5);
    const sitting = crouch > 0.5;
    const ps = { kind: 'passer', pose: sitting ? 'sit' : 'stand', crate: false, x: px,
      y: 568 - (sitting ? 4.9 : 8) * R + (sitting ? 0 : crouch * 1.4 * R), R, turn: stopped ? 0.6 : 0.7,
      walking: !stopped, walk: t * 6, umbrella: true, umbrellaColor: '#2b3346', time: t,
      tilt: stopped ? 0.1 : lerp(0.25, 0.0, sstep(t, 170, 172)), blink: blink(t, 'passer'),
      gx: stopped ? 0.8 : lerp(0, -0.8, pulse(t, 169, 174, 0.5, 1)), gy: stopped ? 0.4 : 0.5, browUp: pulse(t, 170, 176, 0.4, 2) * 0.5 };
    lit(c => person(c, ps), [{ world: true, x: px, y: 520, r: 120, c: `rgba(255,225,170,${0.3 * sstep(t, 170.3, 172)})` }], 'rgba(10,12,20,0.4)');
    // the spark leaping from one to the other
    const leap = sstep(t, 169.6, 171.0);
    if (leap > 0 && leap < 1) {
      const ax = jx, ay = jy + 2.3 * R, bx = px, by = 568 - 8 * R + 2.3 * R;
      drawSpark(g, lerp(ax, bx, leap), lerp(ay, by, leap) - Math.sin(leap * Math.PI) * 50, 1.2, t, {});
    }
    if (t > 171) chestGlow(px, ps.y + 2.3 * R, 50, 0.6, t);
    applyCam(g);
    drawRain(g, t, 1 - sstep(t, 158, 168), { x0: -200, y0: -200, w: W + 400, h: H + 400 });
    fade(1 - sstep(u, 0, 0.8));
  },

  finale(t, u) {
    setCam(640, lerp(300, 260, u / 20), lerp(1.0, 0.72, ease(u / 20)));
    applyCam(g);
    // lights spread from the singer's window across the city
    const spread = (u - 1) * 120;
    const wl = (x, y, k) => {
      const d = Math.hypot(x - STREET.win[0], y - STREET.win[1]);
      return d < spread ? 0.75 * sstep(spread - d, 0, 60) * (hrand(k + 77) < 0.55 ? 1 : 0) : 0;
    };
    drawStreet(g, t, { clear: 1, wet: 0.5, windowLight: 0.5, doorAjar: 0.5, windowsLit: wl });
    applyCam(g);
    chestGlow(STREET.win[0] + 50, STREET.win[1] + 70, 60, 0.7, t);
    motes(g, t, 640, 450, 50, 900, { life: 7, rise: 220, alpha: 0.5 });
    titleText('Even in the storm, something sacred remains.', 640, 34, pulse(u, 6, 17, 1.5, 2), { italic: true });
    fade(sstep(u, 16, 20));
  },
};

const PARTS_JS = { 1: P1, 2: P2 };

function renderFrame(t) {
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  const shots = TL.shots;
  let shot = shots[shots.length - 1];
  for (const s of shots) if (t >= s[1] && t < s[2]) { shot = s; break; }
  const fn = PARTS_JS[TL.part][shot[0]];
  g.save();
  fn(t, t - shot[1]);
  g.restore();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.filter = 'none'; g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  if (shot[0] !== 'black' && shot[0] !== 'card') overlays(t);
  // quick dip at hard cuts for softness
  const since = t - shot[1], until = shot[2] - t;
  if (shot[0] !== 'black') fade(0.6 * (1 - sstep(since, 0, 0.12)));
  subtitle(t);
  // fade the very start and end of each part
  fade(1 - sstep(t, 0, 1.0));
  fade(sstep(t, TL.duration - 1.0, TL.duration));
}

function setup(tl) { TL = tl; }
