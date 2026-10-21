"""Shared visual library for "The Stone and the Bread".

Import the pieces you need explicitly (nothing is imported eagerly, so a broken
module never takes the others down):

    from film.lib import core, fx, timeline          # always available
    from film.lib import env, props                  # environment / prop kits
    from film.lib import characters as ch            # the creature cast

See film/lib/API.md for the reference and film/lib/STYLE.md for the style bible.
"""
