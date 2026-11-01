/* TEMP stub — replaced by the scene author */
(function () {
  Film.scene({ id: 'trail', order: 1, title: 'The Trail', duration: 10, chapter: 'Part One · The Hike', crossIn: 1.5, mood: 'forest',
    render(ctx, t) {
      const P = Art.TOD.morning; Art.sky(ctx, P);
      Art.ground(ctx, { y: 860, offset: t * 100, color: P.ground, color2: P.ground2 });
      Art.person(ctx, { x: 900, y: 870, look: 'me', t, walk: t * 6 });
      Art.captions(ctx, t, [[0.5, 6, 'I imagine that I’m on a hike with a group of people.']]);
    } });
})();
