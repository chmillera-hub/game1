'use strict';
// One large portrait at close-up scale: node tools/portrait.js who expr out.png [jsonExtra]
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawCharacter } = require('../lib/character');
const { makeCast } = require('../lib/cast');
const { EXPR } = require('../lib/expressions');
const [who, expr, out, extra] = process.argv.slice(2);
const A = makeCast()[who];
const c = createCanvas(1080, 1300); const ctx = c.getContext('2d');
const g = ctx.createLinearGradient(0, 0, 0, 1300); g.addColorStop(0, '#5a4636'); g.addColorStop(1, '#2a1e18');
ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 1300);
drawCharacter(ctx, A, { x: 540, y: 1150, scale: 560, ...EXPR[expr], ...(extra ? JSON.parse(extra) : {}) }, { light: { x: -0.6, y: -0.8 } });
fs.writeFileSync(out, c.toBuffer('image/png'));
