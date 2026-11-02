#!/usr/bin/env node
/* Step through the film and record when each on-screen line first becomes readable and who says it.
   Output: tools/voice/cues.json  [{T0, T1, text, kind, who, scene}] in absolute film seconds. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 640, height: 360 } });
  await p.goto('file://' + path.join(root, 'index.html') + '?test&w=640');
  await p.waitForFunction(() => window.Film && Film.ready);
  const cues = await p.evaluate(() => {
    const seen = new Map();
    let T = 0, sid = '';
    const rec = (kind, text, o) => {
      const a = o && o.alpha !== undefined ? o.alpha : 1;
      const rv = o && o.reveal !== undefined ? o.reveal : 1;
      if (!text || a < 0.25 || rv <= 0.01) return;
      const key = kind + '|' + text + '|' + sid;
      const e = seen.get(key);
      if (e) e.T1 = T; else seen.set(key, { T0: T, T1: T, text: String(text), kind, who: (o && o.who) || null, scene: sid });
    };
    const wrap = (name, kind) => { const f = Art[name]; Art[name] = function (ctx, text, o) { rec(kind, text, o || {}); return f.apply(this, arguments); }; };
    wrap('caption', 'narration'); wrap('bubble', 'dialogue'); wrap('hand', 'hand'); wrap('title', 'title');
    for (T = 0; T <= FILM.duration; T += 0.1) { T = Math.round(T * 10) / 10; sid = Film.scenes[Film.locate(T).i].id; FILM.renderAt(T); }
    return [...seen.values()];
  });
  await b.close();
  fs.writeFileSync(path.join(__dirname, 'cues.raw.json'), JSON.stringify(cues, null, 1));
  console.log(cues.length + ' raw cues');
})();
