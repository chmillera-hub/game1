/* ============================================================
   Boot. 3D experiments need three.js; if the CDN is blocked the
   2D experiments still run.
   ============================================================ */
(function boot() {
  if (typeof THREE === 'undefined') {
    document.querySelectorAll('[data-stage]').forEach(s => {
      if (s.closest('#ch-finger, #ch-scissors, #ch-tape, #ch-spin, #ch-music')) {
        s.append(Lab.el('p', { class: 'chip alert', style: 'position:absolute;inset:auto 12px 12px 12px', text: 'The 3D library did not load, so this experiment cannot run here. The 2D experiments (6 to 9) still work.' }));
      }
    });
  }
  Lab.start();
})();
