"""The creature cast. `from film.lib import characters as ch`

Every module in this package (except base.py and names starting with "_") is imported
automatically, and the names listed in its `__all__` are re-exported here, so scenes write
`ch.draw_dragon(...)`, `ch.DragonPose(...)`, `ch.draw_gnome(...)`. The shared rig kit is
available as `ch.base` and its most used names (Light, LIGHTS, Mat, Expr, MOODS, expr,
contact_shadow, ...) are re-exported too.

Module conventions (see API.md "Cast" and STYLE.md):
  * export public names via __all__, prefixed by the creature (draw_gnome, GnomePose, GNOME_HEIGHT)
  * optional character-sheet hook: sheet_items() -> [base.SheetItem, ...]  (preferred)
    or draw_sheet(cr, w, h) for a fully custom page; render.py --sheet collects them.
  * line-up hook: lineup() -> [base.LineupItem(name, draw(cr, x, ground_y, scale), width)]
    puts the creature on the shared height chart (character_sheet_lineup.png).

A module that fails to import does not take the others down: a warning (with traceback) is
printed and recorded in IMPORT_ERRORS. Set FILM_STRICT=1 to raise instead.
"""

import importlib
import os
import pkgutil
import sys
import traceback

from . import base
from .base import (BENCH_SEAT_H, CAST_HEIGHTS, LIGHTS, LINE, MOODS, Expr, HandFrame, Light,  # noqa: F401
                   LineupItem, Mat, Path, Proj, SheetItem, auto_blink, breathing, chain,
                   contact_shadow, expr, eye, hand, palette, shade, spring, sway, walk_cycle, wobble)

REGISTRY = {}        # module name -> module (every creature module, in name order)
IMPORT_ERRORS = {}   # module name -> traceback text

_SKIP = {"base"}


def _load_all():
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        name = info.name
        if name.startswith("_") or name in _SKIP:
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{name}")
        except Exception:
            tb = traceback.format_exc()
            IMPORT_ERRORS[name] = tb
            if os.environ.get("FILM_STRICT"):
                raise
            print(f"[characters] WARNING: failed to import {name}:\n{tb}", file=sys.stderr)
            continue
        REGISTRY[name] = mod
        g = globals()
        for pub in getattr(mod, "__all__", ()):
            obj = getattr(mod, pub)
            if pub in g and g[pub] is not obj and not isinstance(g[pub], type(sys)):
                print(f"[characters] WARNING: {name}.{pub} shadows an existing name", file=sys.stderr)
            g[pub] = obj


def sheet_providers():
    """[(module_name, module)] for every module that has sheet_items() or draw_sheet()."""
    return [(n, m) for n, m in REGISTRY.items() if hasattr(m, "sheet_items") or hasattr(m, "draw_sheet")]


def lineup_items():
    """Every creature's base.LineupItem (modules with a lineup() hook), tallest planned first."""
    items = []
    for n, m in REGISTRY.items():
        if hasattr(m, "lineup"):
            try:
                items += list(m.lineup())
            except Exception:
                print(f"[characters] WARNING: {n}.lineup() failed:\n{traceback.format_exc()}", file=sys.stderr)
    return sorted(items, key=lambda it: -base.CAST_HEIGHTS.get(it.name, 0))


_load_all()
