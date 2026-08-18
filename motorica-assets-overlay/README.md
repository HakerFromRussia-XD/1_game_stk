# Motorica standalone asset overlay

This directory is the tracked source of the permanent Motorica Training Hub
gameplay content. It is derived from the compatible `stk-assets` checkout and
keeps each upstream `licenses.txt` file next to the reused assets.

- `motorica_signal_pilot`: original static hover vehicle geometry with four
  outboard hover modules, a visor pilot and Motorica-only materials.
- `motorica_signal_lab`: original generated track mesh, waveform route,
  driveline, quads, checkpoints, twelve neon gates and three exercise zones.
- `motorica_signal_lab.music/.ogg`: original deterministic ambient soundtrack.
- `motorica_precision`, `motorica_reaction`, `motorica_signal_hold`: three
  independent training definitions sharing only the purpose-built Lab.

Regenerate intentionally with `tools/motorica_assets/build_assets.py overlay`.
Never edit `build-ios-assets` as a source of truth.
