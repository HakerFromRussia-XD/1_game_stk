# Content migration checkpoint

Read-only inspection, 2026-09-18. This is not rendering, driving, performance, or publication acceptance.

Run `python3 tools/fluxara_content/inventory.py iosApp/FluxaraResources/tracks/* iosApp/FluxaraResources/karts/* --shared data/textures data/models data/music data/library`.

| Existing resource | Bytes | Finding |
|---|---:|---|
| fluxara-canyon | 16,257,361 | XML parses; XML resource references resolve within inspected scope; graph/quads present; LICENSE.txt present. Approved art untouched. |
| fluxara-circuit | 1,490,007 | graph.xml line 1 contains `<?xml version="1.0"?> encoding="utf-8"?>` and fails standard XML parsing. |
| fluxara-summit-run | 15,715,766 | Four unresolved material declarations: rock_brown.jpg, rock_grey.jpg, fluxara_drift_generic_snow_a.png, transparence.png. Mesh use of these declarations is unverified. |
| fluxara-ace | 2,975,115 | XML parses; no unresolved XML resources; License.txt present. |
| fluxara-halo | 775,762 | XML parses; no unresolved XML resources; License.txt present. |

The checker now inspects SPM v2 texture tables, but not runtime library lookup, texture GPU memory, or geometry counts. Shared basename hits may not resolve at runtime. Do not interpret a clear inventory as a working race.

## Follow-up repair and packaged dependency verification

Circuit graph.xml declaration repaired to `<?xml version="1.0" encoding="utf-8"?>`. The diff changes exactly one line; graph body, nodes and edges are unchanged.

Summit SPM texture tables confirm six shared references: rock.jpg, rock_brown.jpg, rock_grey.jpg, snowrock.jpg, fluxara_drift_generic_snow_a.png, transparence.png. All six exist in `.codex-downloads/fluxara-addon-catalog/reference-runtime/extracted/FluxaraDrift.app/Contents/Resources/data/textures` and `/private/tmp/fluxara_drift_public_debug/Fluxara Drift.app/data/textures`. Running the inventory with that existing app's textures as `--shared` produces zero unresolved XML or SPM dependencies. Thus the initial repository-only findings do not establish a packaged resource defect. No Summit asset changes are needed on this evidence. The new simulator bundle still needs its own resource and rendering verification by the root agent.

## Prioritized next work

1. Finish validation of already-selected Summit Run and Ace/Halo before importing another catalog package. Summit Run is already the agreed snow environment; another snow package is not a substitute for finishing it.
2. Correct the malformed Circuit graph declaration while preserving graph nodes/edges. This needs root-agent coordination because content changes are outside this agent's assigned write scope.
3. If another kart is needed, inspect catalog `extracted/karts/mechatux`: version 3, animated heavy kart, four referenced wheel models, 656,956 bytes, 20 files, no unresolved XML references. Its retained license.txt includes GPL-3 and Johann C attribution. It is a candidate only, not an approved visual or imported asset.
4. If another snow route is needed, inspect `extracted/tracks/alpine-2_1`: version 6, graph/quads present, 11,045,121 bytes, 85 files. Missing `kart_grand_prix.music`; retained License.txt names Daniel Schellhammer, Andrew Sumner, and Free Art license. Visual approval and binary dependency audit remain necessary.

Old Snow Peak was also checked (version 7, 3,425,209 bytes, graph/quads present), but has unresolved ice/wood textures, bridge sound, and smoke declarations. It is lower priority than completing the selected Summit Run.

No package was imported, no license was removed, and no existing asset was modified by this inventory task.
