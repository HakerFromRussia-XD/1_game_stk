# Figma implementation fidelity audit — 2026-09-18

Scope: approved Home `19:2`, Garage `54:2`, Settings `55:2`, Race Setup `56:2` in Figma file `Pws4Hw0fwwTmTMf6OJvil8`. Live metadata and Settings design context inspected; implementation and exported layers inspected. Simulator screenshot comparison is **pending**, so 1:1 acceptance is not established.

## Findings

1. **P1 — Orientation transition needs runtime acceptance.** The inspected existing Debug simulator bundle listed only LandscapeLeft/Right. `src/states_screens/fluxara_ui.hpp:35` fits a 360×780 portrait canvas, so landscape produces a narrow central menu. Source fix now adds Portrait capability and initial SDL portrait hint, with a StateManager hook requesting portrait for MENU and landscape for GAME/INGAME_MENU through public UIKit APIs. Fluxara RaceResultGUI::init explicitly requests portrait; popping Results back to GAME requests landscape for retry, and returning to campaign requests portrait. Root must compile the new helper and verify menu→race→results→retry/menu rotation. Ordinary pause remains landscape.
2. **P1 — Font fidelity not established.** Figma uses Baloo 2 ExtraBold; `fluxara_ui.hpp:77` and Settings use the engine's generic title font. No Baloo mapping was found in current resource/code lookup. Glyph shapes, widths, vertical metrics and shadow softness cannot be called 1:1 until the actual font is mapped and compared. Shared label drawing centers text, whereas most Figma labels use left alignment inside their boxes; Settings now explicitly uses left alignment.
3. **P2 — Garage requires runtime composition verification.** Agent1 confirms the current background is an exported clean empty podium, avoiding the earlier baked-kart duplication. A live 3D model occupies `(32,162,296,260)` and the separate stats table `(54,431,254,254)`. Need screenshots with Ace and a differently proportioned kart to verify no model/table overlap, wheel scaling or clipping; static layout alone cannot prove this.
4. **P2 — Settings off-state appearance is an adaptation.** The approved screen depicts ON states only. The current OFF state moves the original knob left and displays OFF, retaining the cyan track. Actual values use original music/SFX APIs and immediate persistence. Both states require simulator captures; do not imply a designer-approved OFF variant exists.

## Fixed during audit

- Settings initially retained native button labels and skin behind the transparent art. `layoutControls` and `refreshLabels` now call `FluxaraUI::rasterHitTarget` for all three controls, preventing old button text from reappearing after a toggle. Runtime verification remains pending.

## Intentional scope adaptation, not a Figma match

- Race Setup includes opponents and difficulty in the otherwise blank lower area. Agent1 confirms root explicitly required these functional controls. They are absent from the approved frame and must be disclosed as an adaptation, not counted as 1:1 fidelity.

## Runtime acceptance still needed

- Portrait Home/Garage/Setup/Settings screenshots at the same normalized360×780 crop as Figma.
- Home icons remain distinct layers without doubled or clipped silhouettes; long labels fit.
- Garage: selected model changes with arrows, only one model is visible, stats/name update, lower navigation is unobscured.
- Settings: music/sound ON→OFF→ON and reopen retain real values with no native text/border bleed.
- Setup: plus/minus and Start Race hit boxes align with art; non-Circuit previews preserve recognizable source content and rounded boundaries.

No phone, build or Figma write was performed by this audit role. Root authorized the focused Settings overlay and orientation source fixes after findings were reported.
