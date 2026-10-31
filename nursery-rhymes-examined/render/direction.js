// Shot-by-shot direction. Per beat id: shots = [[startFraction, shotName, params]], the
// music mood, an optional note cue on one word, and sound effects at beat fractions.
// Passenger acting is driven by `crowd` states; the child (the one who notices) by `child`.
'use strict';

module.exports = {
  // ---------------- Part I: the bus
  0: { shots: [[0, 'bus_wide', {}]], mood: 'bleak', sfx: [[0, 'wind'], [0, 'hum']] },
  1: { shots: [[0, 'bus_wide', { push: true }]], mood: 'bleak' },
  2: { shots: [[0, 'bus_front', {}]], cue: ['carcass', 'low'], sfx: [[0.1, 'engine']] },
  3: { shots: [[0, 'wheel_cu', {}]], cue: ['algorithmic', 'low'], sfx: [[0, 'wheel_tick']] },
  4: { shots: [[0, 'bus_side', { horizon: true }]], mood: 'irony', cue: ['destinations', 'high'] },
  5: { shots: [[0, 'steering_cu', {}]], mood: 'dread', cue: ['wheel', 'low'] },
  6: { shots: [[0, 'compass_cu', {}]], cue: ['stars', 'high'] },
  7: { shots: [[0, 'empty_seat', {}]], cue: ['void', 'low'], sfx: [[0.2, 'creak']] },
  8: { shots: [[0, 'interior', {}]], mood: 'song', crowd: 'sing', child: 'sing', sfx: [[0.55, 'song_start']] },
  9: { shots: [[0, 'singers_cu', {}], [0.42, 'gears_cu', {}], [0.78, 'interior', {}]], crowd: 'sing', child: 'sing', sfx: [[0.5, 'gears'], [0.7, 'screech']] },
  10: { shots: [[0, 'interior', { loud: true }], [0.45, 'child_cu', {}], [0.72, 'brake_cu', {}]], crowd: 'sing_loud', child: 'notice', cue: ['brakes', 'low'], sfx: [[0.8, 'snap']] },
  11: { shots: [[0, 'cliff_approach', {}], [0.6, 'child_window', {}]], mood: 'dread', crowd: 'sing', child: 'fear', cue: ['precipice', 'low'] },
  12: { shots: [[0, 'window_blur', {}]], crowd: 'sing', child: 'fear', sfx: [[0, 'whoosh']] },
  13: { shots: [[0, 'interior', { drone: true }]], mood: 'drone', crowd: 'drone', child: 'fear', cue: ['oblivion', 'low'] },
  14: { shots: [[0, 'wheel_cu', { fast: true }], [0.35, 'bus_momentum', {}]], crowd: 'drone', child: 'fear', cue: ['momentum', 'low'], sfx: [[0.35, 'rumble']] },
  15: { shots: [[0, 'interior', { stop: true }]], mood: 'silence', crowd: 'stop', child: 'stop', cue: ['cease', 'hit'], sfx: [[0.62, 'song_stop']] },
  16: { shots: [[0, 'window_cliff', {}], [0.42, 'child_stand', {}]], mood: 'urgent', crowd: 'stop', child: 'resolve', cue: ['brakes', 'swell'] },

  // ---------------- Part II: the spider
  17: { shots: [[0, 'wall_wide', {}]], mood: 'drip', sfx: [[0, 'drip'], [0.3, 'skitter']] },
  18: { shots: [[0, 'wall_wide', { push: true }]], mood: 'drip' },
  19: { shots: [[0, 'spider_cu', {}]], spider: 'shy', cue: ['Spider', 'light'] },
  20: { shots: [[0, 'spout_up', {}], [0.55, 'spider_climb', { start: true }]], mood: 'fragile', spider: 'hopeful', cue: ['promotions', 'high'] },
  21: { shots: [[0, 'spider_climb', {}]], spider: 'hopeful', cue: ['up', 'high'], sfx: [[0.3, 'skitter']] },
  22: { shots: [[0, 'spider_burden', {}]], spider: 'sad', cue: ['weeping', 'low'] },
  23: { shots: [[0, 'spider_slip', {}]], spider: 'strain', sfx: [[0.4, 'squeak']] },
  24: { shots: [[0, 'rain_begins', {}]], mood: 'storm', spider: 'worried', sfx: [[0.1, 'rain']] },
  25: { shots: [[0, 'rain_faces', {}]], cue: ['heart', 'low'] },
  26: { shots: [[0, 'rain_faces', { heavy: true }], [0.55, 'washout', {}]], spider: 'panic', cue: ['tragedy', 'low'], sfx: [[0.55, 'torrent'], [0.85, 'splash']] },
  27: { shots: [[0, 'sun_appears', {}]], mood: 'false_hope', spider: 'dazed', cue: ['help', 'high'], sfx: [[0.15, 'shimmer']] },
  28: { shots: [[0, 'pills', {}]], spider: 'numb', cue: ['numb', 'low'], sfx: [[0.5, 'pill']] },
  29: { shots: [[0, 'therapist', {}]], mood: 'clinical', spider: 'unsure' },
  30: { shots: [[0, 'sun_cu', {}]], mood: 'false_hope', cue: ['smile', 'light'] },
  31: { shots: [[0, 'wellness_pole', {}]], cue: ['wellness', 'high'], sfx: [[0.2, 'shimmer']] },
  32: { shots: [[0, 'pole_flaws', {}]], mood: 'drip', cue: ['flaws', 'low'] },
  33: { shots: [[0, 'spider_climb', { pole: true }]], spider: 'determined', sfx: [[0.3, 'skitter']] },
  34: { shots: [[0, 'cycle_loop', {}]], mood: 'cycle', cue: ['anew', 'swell'] },
  35: { shots: [[0, 'montage', {}]], spider: 'determined', sfx: [[0.2, 'rain'], [0.4, 'splash']] },
  36: { shots: [[0, 'many_spouts', {}]], mood: 'resigned', cue: ['fall', 'low'] },
  37: { shots: [[0, 'final_spider', {}]], spider: 'final', cue: ['remain', 'low'], sfx: [[0.3, 'rain']] },
};
