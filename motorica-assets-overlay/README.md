# Motorica standalone asset overlay

This directory is the tracked source of the permanent Motorica Training Hub
gameplay content. It is derived from the compatible `stk-assets` checkout and
keeps each upstream `licenses.txt` file next to the reused assets.

- `motorica_kiki`: separate kart ID and derived palette; original Kiki remains untouched.
- `motorica_night_island`: standalone overworld with a Motorica-only challenge ID.
- `motorica_signal_circuit`: generated 72-section closed route with custom
  driveline, quads, checkpoints, starts, night styling and UFO decorations;
  it is the fixed three-lap race used by all six island points.

Regenerate intentionally with `tools/motorica_assets/build_assets.py overlay`.
Never edit `build-ios-assets` as a source of truth.
