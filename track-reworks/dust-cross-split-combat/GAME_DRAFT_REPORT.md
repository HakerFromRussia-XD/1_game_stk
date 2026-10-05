# Early in-game draft — verdict (2026-09-26)

## How it was verified
- Runtime experiment: copy of `build-ios/MinSizeRel-iphonesimulator/Fluxara Drift.app` in
  `runtime-sim/`, scenery line added **only to the copy's** scene.xml; installed on own
  simulator device `Buffy-DustCross` (UDID in `runtime-sim/udid.txt`). Repo + baseline untouched.
- Proof scenery loads: control run (original bundle) → scene complexity 109; scenery bundle → 110.
  Re-import of `dust-cross_scenery.spm` back into Blender gives 3 mesh objects (atlas plate 808 m,
  barrier 527 m, canyon atlas 409 m) matching what the game draws.
- Launch args used: `--race-now --track=fluxara-user-dust-cross-split-combat --numkarts=6`
  (FFA battle, ~30+ s of gameplay, kart respawns; static camera though).

## What the game shows (evidence in `progress/`)
- `v2-3s/7s/14s` (patched bundle) vs `orig-03` (original): new in-game content confirmed —
  yellow stone arena floor (my atlas plate, wrong flat texture), light-grey mesa on horizon,
  dark barrier walls, pink patches (tent/waterfall placeholder colors), grey block on horizon.
- Game draft IS visible in-game; large forms are standing. BUT everything renders in
  flat placeholder colors, not the pool textures.

## Key finding — placeholder colors are an export artifact
The workfile's objects carry my provisional colored materials; my SPM export wrote
plain color materials instead of UV-mapped images. The pool textures
(`concrete_barrier_diffuse.png`, `fluxara_canyon_atlas.png`) are inside the SPM and the
track folder, but the export never bound them as image textures. That is why the floor
is flat yellow and the mesa is flat grey. Fix: in the workfile assign the real image
textures (UV-mapped) to the reused objects and re-export. No geometry work needed.

## Reference comparison (refs 01–04) — what matches / differs
Matches (composition/silhouettes):
- Red-rock canyon framing around a dirt arena (ref-02/03): mesas present at the perimeter,
  correct scale relationship (they tower over the bowl).
- Arena bowl reading (ref-01): visible dish with barriers; splittable layout intact.
- Sky/atmosphere: bright blue sky, cloud layer visible (ref-03/04) — direction is right.

Differences (to fix in the next iteration, in priority order):
1. Materials/textures: everything flat-colored; refs demand layered red sandstone with
   visible banding (canyon atlas), dirt with granular detail, wood grain on stands.
2. Waterfall: pink flat blob now; ref-03 shows a teal multi-stream cascade on NW rock.
3. Barriers: currently dark meshy walls; ref-01 wants concrete barriers with red/white chevrons.
4. Stands/tents: pink patches instead of red/yellow tented grandstands (ref-01, south side).
5. Green-blue tint spots floating in air (7s/14s frames) — untextured bits of the big
   atlas plate; must map atlas correctly or separate the plate per material.
6. Clouds-sea under the bridges (ref-03) and light masts (ref-01) are not yet readable in-game.

## Blockers encountered (honest log)
- `--profile-laps` crashes this app build on the arena map (springboard at ~35 s, reproducible
  with default and 4 karts) — full AI route traversal not available in this build.
- `--aiNP` races end in ~1.5 s (fast trophy) — unusable for camera coverage.
- FFA battle camera is static (no player input) — periodic respawns give limited viewpoints.

## Preservation
All five protected files bit-identical to baseline after all runs
(track.xml / scene.xml / materials.xml / navmesh.xml / course SPM). The scenery line
exists only inside the runtime-sim bundle copy; integrating it into the repo's scene.xml
requires the same one-line edit as Ski Dash (pending owner's approval since scene.xml
is baseline-protected for this pass).

## Next iteration checklist
1. Bind real image textures in workfile (canyon atlas → mesas/floor accents, barrier
   diffuse → walls, wood → stands), re-export, re-run this same runtime check.
2. Replace waterfall/tent placeholder colors with pool materials.
3. Fix the atlas plate material split (green-blue floating spots).
4. After visual pass: propose the one-line scene.xml integration for repo approval.
