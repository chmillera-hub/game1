// Virtual clock for frame-exact capture: timers, rAF, smooth scrolling and every CSS
// animation/transition advance only when the harness calls window.__advance(ms).
(() => {
  let now = 0, seq = 1, timers = [], rafs = [];
  const born = new WeakMap(), tweens = new Map();
  performance.now = () => now;
  window.requestAnimationFrame = cb => { const id = seq++; rafs.push({ id, cb }); return id; };
  window.cancelAnimationFrame = id => { rafs = rafs.filter(r => r.id !== id); };
  window.setTimeout = (cb, ms, ...args) => { const id = seq++; timers.push({ id, at: now + (Number(ms) || 0), cb: () => cb(...args) }); return id; };
  window.clearTimeout = id => { timers = timers.filter(t => t.id !== id); };
  const scrollTo = Element.prototype.scrollTo;
  Element.prototype.scrollTo = function (a) {
    if (a && typeof a === 'object' && a.behavior === 'smooth') { tweens.set(this, { from: this.scrollTop, to: a.top, t0: now }); return; }
    return scrollTo.apply(this, arguments);
  };
  window.__now = () => now;
  window.__advance = ms => {
    const target = now + ms;
    for (;;) {
      timers.sort((x, y) => x.at - y.at);
      if (!timers.length || timers[0].at > target) break;
      const t = timers.shift(); now = Math.max(now, t.at); t.cb();
    }
    now = target;
    const due = rafs; rafs = [];
    due.forEach(r => r.cb(now));
    tweens.forEach((tw, el) => {
      const p = Math.min(1, (now - tw.t0) / 800), e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      el.scrollTop = tw.from + (tw.to - tw.from) * e;
      if (p >= 1) tweens.delete(el);
    });
    for (const a of document.getAnimations()) {
      if (!born.has(a)) { born.set(a, now); a.pause(); }
      a.currentTime = now - born.get(a);
    }
  };
})();
