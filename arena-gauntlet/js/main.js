// Boot. When hosted as a Claude artifact, keep the current campaign across live updates.
(function (root) {
  'use strict';
  const AG = root.AG;

  function start(data) {
    AG.UI.init();
    if (data && data.run && !data.run.over) {
      AG.UI.run = data.run;
      AG.Run.save(data.run);
      AG.UI.route();
      return;
    }
    AG.UI.title();
  }

  const hot = root.claude && root.claude.hot;
  if (hot && hot.snapshot) hot.snapshot(() => ({ run: AG.UI.run ? JSON.parse(JSON.stringify(AG.UI.run)) : null }));
  if (hot && hot.ready) hot.ready(start);
  else start((hot && hot.data) || {});
})(window);
