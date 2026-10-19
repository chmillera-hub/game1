// Shared drawing helpers and timeline runner for the explainer videos.
// Every frame is a pure function of time, so render.mjs can step through
// a page frame by frame to export a video.

const W = 1920, H = 1080;
const canvas = document.getElementById('stage');
const ctx = canvas.getContext('2d');
const FONT = "'Inter', 'Inter Display', system-ui, sans-serif";

const C = {
    bg1: '#12141d', bg2: '#1c2030', cream: '#f4ecdc', amber: '#f2b84b',
    teal: '#4fc3a1', coral: '#ef6f5e', sky: '#7fb0e8', violet: '#c792ea',
    muted: '#9aa0b4', stone: '#4a5070', stoneDark: '#343850', gold: '#d9a441',
    ink: '#1a1c26', grass: '#2b4637'
};
const VCOL = [C.amber, C.teal, C.coral, C.sky, C.violet, '#f7c59f'];

// ---------- math helpers ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, u) => a + (b - a) * u;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const easeOut = u => 1 - Math.pow(1 - u, 3);
const easeInOut = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
const backOut = u => { const c = 1.7; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };

function hexToRgb(h) {
    const n = parseInt(h.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function mix(a, b, u) {
    const x = hexToRgb(a), y = hexToRgb(b);
    return `rgb(${x.map((v, i) => Math.round(lerp(v, y[i], u))).join(',')})`;
}
function rgba(h, a) {
    const [r, g, b] = hexToRgb(h);
    return `rgba(${r},${g},${b},${a})`;
}

// ---------- drawing helpers ----------
function rr(x, y, w, h, r) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
}

function circle(x, y, r) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
}

function text(str, x, y, o = {}) {
    const size = o.size || 48;
    ctx.save();
    ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.font = `${o.weight || 700} ${size}px ${FONT}`;
    ctx.fillStyle = o.color || C.cream;
    ctx.textAlign = o.align || 'center';
    ctx.textBaseline = 'middle';
    ctx.letterSpacing = (o.spacing || 0) + 'px';
    const lines = o.maxWidth ? wrap(str, o.maxWidth) : [str];
    const lh = size * (o.lineHeight || 1.2);
    const y0 = y - (lines.length - 1) * lh / 2;
    lines.forEach((ln, i) => ctx.fillText(ln, x, y0 + i * lh));
    ctx.restore();
}

function wrap(str, maxW) {
    const words = str.split(' ');
    const lines = [];
    let cur = '';
    for (const w of words) {
        const test = cur ? cur + ' ' + w : w;
        if (ctx.measureText(test).width > maxW && cur) {
            lines.push(cur);
            cur = w;
        } else {
            cur = test;
        }
    }
    if (cur) lines.push(cur);
    return lines;
}

// Shows the latest caption whose start time has passed, fading between them.
function captions(t, items, y, o = {}) {
    for (let i = 0; i < items.length; i++) {
        const [t0, str, color] = items[i];
        const t1 = i + 1 < items.length ? items[i + 1][0] : Infinity;
        if (t < t0 || t > t1) continue;
        const a = easeOut(prog(t, t0, t0 + 0.45)) * (1 - prog(t, t1 - 0.3, t1));
        text(str, W / 2, y + (1 - easeOut(prog(t, t0, t0 + 0.45))) * 24,
            { ...o, color: color || o.color, alpha: a });
    }
}

function villager(x, y, s, col, o = {}) {
    const ph = o.walk;
    const bob = ph == null ? 0 : -Math.abs(Math.sin(ph)) * 5;
    ctx.save();
    ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.translate(x, y + bob * s);
    ctx.scale(s * (o.flip ? -1 : 1), s);
    if (o.glow) {
        const g = ctx.createRadialGradient(0, -60, 0, 0, -60, 110);
        g.addColorStop(0, rgba(col, 0.55 * o.glow));
        g.addColorStop(1, rgba(col, 0));
        ctx.fillStyle = g;
        circle(0, -60, 110);
        ctx.fill();
    }
    const sw = ph == null ? 0 : Math.sin(ph) * 14;
    ctx.strokeStyle = mix(col, '#000000', 0.35);
    ctx.lineWidth = 11;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(-9, -32); ctx.lineTo(-9 + sw, 0);
    ctx.moveTo(9, -32); ctx.lineTo(9 - sw, 0);
    ctx.stroke();
    ctx.fillStyle = col;
    rr(-24, -84, 48, 60, 22);
    ctx.fill();
    circle(0, -106, 20);
    ctx.fill();
    ctx.fillStyle = C.ink;
    circle(-7, -108, 2.8); ctx.fill();
    circle(7, -108, 2.8); ctx.fill();
    ctx.strokeStyle = C.ink;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    if (o.sad) ctx.arc(0, -92, 6, 1.15 * Math.PI, 1.85 * Math.PI);
    else ctx.arc(0, -102, 6, 0.15 * Math.PI, 0.85 * Math.PI);
    ctx.stroke();
    ctx.restore();
}

function house(x, y, s, col, o = {}) {
    ctx.save();
    ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = col;
    if (o.outline) {
        ctx.setLineDash([14, 12]);
        ctx.strokeStyle = col;
        ctx.lineWidth = 6;
    }
    ctx.beginPath();
    ctx.moveTo(-70, 0); ctx.lineTo(-70, -90); ctx.lineTo(0, -150);
    ctx.lineTo(70, -90); ctx.lineTo(70, 0); ctx.closePath();
    o.outline ? ctx.stroke() : ctx.fill();
    ctx.setLineDash([]);
    ctx.fillStyle = o.outline ? col : rgba(C.ink, 0.55);
    rr(-18, -56, 36, 56, 4);
    ctx.fill();
    if (!o.outline) {
        ctx.fillStyle = rgba(C.amber, 0.85);
        rr(30, -74, 24, 22, 3);
        ctx.fill();
    }
    ctx.restore();
}

function background(t, warm = 0) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, mix(C.bg1, '#3a2a2a', warm));
    g.addColorStop(1, mix(C.bg2, '#5a3a2a', warm));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    // slow drifting motes
    for (let i = 0; i < 40; i++) {
        const sx = (i * 397) % W;
        const sy = (i * 211) % H;
        const x = (sx + t * (8 + (i % 5) * 4)) % W;
        const y = (sy - t * (5 + (i % 3) * 3) + H * 4) % H;
        const a = 0.08 + 0.08 * Math.sin(t * 0.7 + i);
        ctx.fillStyle = rgba(i % 4 === 0 ? C.amber : C.cream, a);
        circle(x, y, 2 + (i % 3));
        ctx.fill();
    }
}

function ground(y, col = C.grass, alpha = 1) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = col;
    ctx.fillRect(0, y, W, H - y);
    ctx.fillStyle = rgba('#000000', 0.18);
    ctx.fillRect(0, y, W, 6);
    ctx.restore();
}

function meter(x, y, w, h, value, col, o = {}) {
    ctx.save();
    ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.fillStyle = rgba(C.cream, 0.1);
    rr(x, y, w, h, h / 2);
    ctx.fill();
    ctx.fillStyle = col;
    rr(x, y, Math.max(h, w * clamp(value)), h, h / 2);
    ctx.fill();
    ctx.restore();
}

const scenes = [];
const scene = (start, end, draw) => scenes.push({ start, end, draw });

// warmAt(t) tints the background (0 = night, 1 = full warm).
function startTimeline(duration, warmAt = () => 0) {
    function render(t) {
        ctx.save();
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = 1;
        background(t, warmAt(t));
        for (const s of scenes) {
            if (t < s.start || t >= s.end) continue;
            const lt = t - s.start;
            const fadeOut = s.end === duration ? 1.2 : 0.45;
            ctx.save();
            ctx.globalAlpha = prog(lt, 0, 0.45) * (1 - prog(t, s.end - fadeOut, s.end));
            s.draw(lt);
            ctx.restore();
        }
        ctx.restore();
    }

    window.render = render;
    window.DURATION = duration;

    // Interactive preview (skipped when render.mjs drives the page).
    if (!location.search.includes('render')) {
        let t = 0, playing = true, last = performance.now();
        const loop = now => {
            if (playing) t = (t + (now - last) / 1000) % duration;
            last = now;
            render(t);
            requestAnimationFrame(loop);
        };
        addEventListener('keydown', e => {
            if (e.code === 'Space') { playing = !playing; e.preventDefault(); }
            if (e.code === 'ArrowRight') t = Math.min(duration - 0.01, t + 5);
            if (e.code === 'ArrowLeft') t = Math.max(0, t - 5);
            if (e.key === 'r' || e.key === 'R') t = 0;
        });
        canvas.addEventListener('click', () => { playing = !playing; });
        document.fonts.ready.then(() => requestAnimationFrame(loop));
    } else {
        document.body.classList.add('render');
    }
}
