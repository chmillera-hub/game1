/* Boot. Inside a Claude artifact viewer, keep the run across live updates. */
(function (AG) {
  'use strict';
  function start(data) {
    AG.App.start(data && data.run ? data : null);
  }
  const hot = globalThis.window && window.claude && window.claude.hot;
  if (hot && hot.snapshot) {
    try { hot.snapshot(function () { return AG.App.snapshot(); }); } catch (e) { /* ignore */ }
  }
  if (hot && hot.ready) hot.ready(start);
  else start(hot && hot.data ? hot.data : {});
})(globalThis.AG = globalThis.AG || {});
