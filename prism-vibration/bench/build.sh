#!/bin/sh
# assemble the single-file page: ui.html with physics.js and app.js inlined
cd "$(dirname "$0")"
python3 - <<'PY'
ui = open('ui.html').read()
phys = open('physics.js').read().split('// PHYSICS-END')[0]
app = open('app.js').read()
open('shake-a-rainbow-bench.html', 'w').write(ui.replace('/*PHYSICS*/', phys).replace('/*APP*/', app))
PY
