#!/bin/bash
# Counting semaphore for Blender processes (shared by all agents). Source this, then exec your command.
# RENDER_SLOTS (default 3) concurrent Blender renders machine-wide; waits for a free slot.
SLOTS="${RENDER_SLOTS:-3}"
while :; do
  for i in $(seq 1 "$SLOTS"); do
    exec {SLOT_FD}>"/tmp/psalm22_render_slot_${SLOT_PREFIX:-}$i.lock"
    if flock -n "$SLOT_FD"; then export PSALM22_SLOT=$i; break 2; fi
    exec {SLOT_FD}>&-
  done
  sleep 3
done
