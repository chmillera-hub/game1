'use strict';
// Which photographs are on screen at time t in the realistic version.
// Returns a list of layers: { img } (a generated shot, faces animated if it has
// any), { ui: 'chat' | 'phoneMom' | 'phoneJordan' }, with an optional region
// ('top' / 'bottom' for the split-screen call).

function realLayers(env, sc, sh, t) {
  const L = env.L;
  switch (sc.id) {
    case 'table': {
      const m = { wide: 'table_wide', mom: 'table_mom', maya: 'table_maya', dad: 'table_dad', jordan: 'table_jordan', mayaFinal: 'table_maya' };
      return [{ img: m[sh.name] || 'table_wide' }];
    }
    case 'sword':
      return [{ img: sh.name === 'mayaCU' ? 'sword_maya' : 'sword_table' }];
    case 'mask': {
      if (sh.name === 'mirror') {
        // the reflection keeps smiling after Maya's own smile has gone
        const e = L('L14').end;
        if (t < e + 0.4) return [{ img: 'mirror_reflection' }];
        if (t < e + 1.5) return [{ img: 'mirror_real' }];
        if (t < e + 2.9) return [{ img: 'mirror_reflection' }];
        return [{ img: 'mirror_real' }];
      }
      if (sh.name === 'bedWide') return [{ img: 'bed_wide' }];
      if (sh.name === 'screen') return [{ ui: 'chat' }];
      return [{ img: 'bed_cu' }];
    }
    case 'cross':
      return sh.name === 'mirror' ? [{ img: 'cross_true' }, { img: 'mirror_reflection', mask: true }] : [{ img: 'cross_moon' }];
    case 'office': {
      const tOver = sc.tOver;
      if (sh.name === 'mayaCU') return [{ img: t < L('L22').start ? 'office_temple' : 'office_maya' }];
      if (sh.name === 'two') return [{ img: 'office_two' }];
      if (sh.name === 'gregCU') return [{ img: 'office_greg' }];
      if (sh.name === 'overwhelm') return [{ img: t < tOver + 1.7 ? 'office_maya' : 'office_overwhelm' }];
      return [{ img: 'office_maya' }];
    }
    case 'park':
      return [{ img: sh.name === 'cu' ? 'park_cu' : 'park_wide' }];
    case 'sparrows':
      return [{ img: sh.name === 'flock' ? 'sparrows_flock' : 'sparrows_shoulder' }];
    case 'call': {
      if (sh.name === 'phone') return [{ ui: 'phoneMom' }];
      if (sh.name === 'screen') return [{ ui: 'chat' }];
      if (sh.name === 'split') {
        if (t < sc.tHang + 1.2) return [{ img: 'call_mom', region: 'top' }, { img: 'call_maya', region: 'bottom' }];
        return [{ img: 'call_maya_mouth' }];
      }
      // before answering she looks at the phone in her lap; after the call, hand to her mouth
      if (t < L('L31').start) return [{ img: 'call_maya_after' }];
      if (t < L('L37').start + 1.0) return [{ img: 'call_maya_mouth' }];
      return [{ img: 'call_maya_after' }];
    }
    case 'road':
      return [{ img: 'road_night' }, { img: 'road_dawn', fade: true }];
    case 'epilogue': {
      const m = { two: 'epi_two', mayaCU: 'epi_maya', window: 'epi_window' };
      if (sh.name === 'phone') return [{ ui: 'phoneJordan' }];
      if (sh.name === 'phone2') return [{ ui: 'phoneJordanReply' }];
      return [{ img: m[sh.name] || 'epi_maya' }];
    }
    default:
      return [];
  }
}

module.exports = { realLayers };
