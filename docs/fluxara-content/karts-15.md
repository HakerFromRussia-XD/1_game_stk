# Fluxara: 15 existing-look karts

Ace and Halo remain unchanged. The thirteen additions preserve all model, animation, texture, sound and license bytes. Only kart.xml groups is changed to Fluxara.

| ID | Source name | Source package | Size MiB |
|---|---|---|---|
| fluxara-automated-knight | Automated Knight | automated-knight | 1.30 |
| fluxara-aeroroach | Aeroroach | aeroroach | 1.21 |
| fluxara-racing-drone-ii | Racing Drone II | racing-drone-ii | 2.26 |
| fluxara-cz45-desert-buggy | cz45-Desert Buggy | cz45-desert-buggy | 0.33 |
| fluxara-atmoboat | Atmoboat | atmoboat | 0.63 |
| fluxara-tarentula | Tarentula | tarentula | 1.34 |
| fluxara-tri-booster | Tri-Booster | tri-booster | 1.86 |
| fluxara-spacecraft | Spacecraft | spacecraft_1 | 0.93 |
| fluxara-quad-rider | Quad Rider | quad-rider | 6.60 |
| fluxara-hotrod | Hotrod | hotrod | 2.77 |
| fluxara-egg-car | egg car | egg-car | 0.12 |
| fluxara-earthglider | earthglider | earthglider | 0.26 |
| fluxara-hisser | Hisser | hisser | 1.81 |

Models, wheel-model references and declared icons exist. Runtime selection, animation and racing need simulator verification. Some source packages intentionally declare nonexistent shadow filenames; these are inherited and listed in the source descriptors.

Static SPM audit parsed all 58 new SPM files. Five shared stock textures resolve in the existing Debug simulator app's data/textures: gfxGlow_red_a.png, gfxGlow_blue_a.png, gfxGlow_White_a.png, gfx_distord_AlphaTested.png, fluxara_drift_conelight_a.png. Other SPM material textures resolve inside the copied kart folders. This verifies dependency presence, not runtime rendering.

Original license texts remain next to each asset. GPL/CC license labels are source declarations, not a publication clearance finding.
