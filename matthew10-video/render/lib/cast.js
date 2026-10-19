'use strict';
// Character designs (generic, original designs).

const { col, shade } = require('./util');

const BASE = {
  maya: {
    name: 'Maya', sex: 'f', skin: '#b67d58', hair: '#2a1a15', browColor: '#22150f', eyeColor: '#5a3920',
    lip: '#a0564c', hairStyle: 'curls', eyeSize: 1.04, shoulderW: 0.57, blushBase: 0.02,
    outfit: { type: 'cardigan', main: '#c4923c', inner: '#efe6d6' },
  },
  mom: {
    name: 'Mom', sex: 'f', skin: '#c28c68', hair: '#5b3b2a', browColor: '#4a2e20', eyeColor: '#4a3020',
    lip: '#a65558', hairStyle: 'bob', age: 0.55, earring: '#efe6d4', eyeSize: 1.0, shoulderW: 0.6,
    outfit: { type: 'blouse', main: '#b98386', pearls: true },
  },
  dad: {
    name: 'Dad', sex: 'm', skin: '#a26d4c', hair: '#8f8b86', browColor: '#6e6a66', eyeColor: '#3b2a1e',
    lip: '#8e5446', hairStyle: 'receding', mustache: '#7c7873', glasses: '#3a2c24', age: 0.75, jaw: 0.6, headW: 1.05,
    eyeSize: 0.92, eyeH: 0.9, shoulderW: 0.76, browThick: 1.2,
    outfit: { type: 'sweater', main: '#34425c', collar: '#dfe3ea' },
  },
  jordan: {
    name: 'Jordan', sex: 'm', skin: '#b27752', hair: '#1d1511', browColor: '#1d1511', eyeColor: '#4a3020',
    lip: '#97574a', hairStyle: 'messy', eyeSize: 1.02, shoulderW: 0.66,
    outfit: { type: 'hoodie', main: '#3f5946', trim: '#d9d9d2' },
  },
  greg: {
    name: 'Greg', sex: 'm', skin: '#e0b394', hair: '#ae8b56', browColor: '#8c6c40', eyeColor: '#4d6d8e',
    lip: '#b0706a', hairStyle: 'neat', jaw: 0.45, age: 0.35, eyeSize: 0.95, shoulderW: 0.74,
    outfit: { type: 'shirtTie', main: '#bfd3e8', tie: '#2c3e66' },
  },
  priya: {
    name: 'Priya', sex: 'f', skin: '#a26a4a', hair: '#1c1310', browColor: '#1c1310', eyeColor: '#3a2416',
    lip: '#994e47', hairStyle: 'sleek', glasses: '#6a4430', eyeSize: 1.0, shoulderW: 0.6,
    outfit: { type: 'sweater', main: '#7d8b50' },
    extraBody: braid,
  },
};

// Priya's braid over her right shoulder (screen left).
function braid(ctx, A, P, T, when) {
  if (when !== 'afterTorso') return;
  ctx.save();
  const x0 = T.cx - 0.36, y0 = -0.2;
  for (let i = 0; i < 9; i++) {
    const t = i / 8;
    const x = x0 - 0.06 * Math.sin(t * 2.2) + (P.sway ? P.sway.x * t * 0.05 : 0);
    const y = y0 + t * 1.05;
    ctx.fillStyle = col(i % 2 ? A.hair : shade(A.hair, 0.12));
    ctx.beginPath(); ctx.ellipse(x + (i % 2 ? 0.02 : -0.02), y, 0.075 * (1 - t * 0.35), 0.09, i % 2 ? 0.5 : -0.5, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = '#c9a24a';
  ctx.beginPath(); ctx.arc(x0 - 0.04, y0 + 1.1, 0.03, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// Outfit variants for different days/scenes.
const OUTFITS = {
  maya: {
    dinner: { type: 'cardigan', main: '#c4923c', inner: '#efe6d6' },
    night: { type: 'hoodie', main: '#8b84a3', trim: '#e9e4f2' },
    work: { type: 'sweater', main: '#2f6b6a', lanyard: '#c94f4f' },
    new: { type: 'sweater', main: '#b4643f' },
  },
};

function makeCast(outfitFor = {}) {
  const out = {};
  for (const [k, v] of Object.entries(BASE)) {
    out[k] = { ...v };
    if (outfitFor[k] && OUTFITS[k] && OUTFITS[k][outfitFor[k]]) out[k].outfit = OUTFITS[k][outfitFor[k]];
  }
  return out;
}

module.exports = { BASE, OUTFITS, makeCast };
