# Runtime import checkpoint

50 selected source maps are present in `iosApp/FluxaraResources/tracks`:48new `fluxara-user-*` directories plus unchanged `fluxara-canyon` and `fluxara-summit-run`. The older `fluxara-circuit` remains on disk but is outside this roster. Campaign code must consume the manifest, not enumerate every Fluxara-group directory.

Runtime contract: `iosApp/FluxaraResources/fluxara-campaign.xml`, version1,50events. Each event has stable `id`, `mode`, `track`; Ghost entries carry `requires-replay=true`, CTF carries `requires-offline-ctf=true`. Detailed source URLs, revisions, retained licenses, enum mapping and dependency findings are in `runtime-roster-v1.json`. This is imported content, not runtime/visual acceptance.

Reproduction from downloaded source packages:

1. `python3 tools/fluxara_content/import_user_roster.py --apply`
2. `python3 tools/fluxara_content/resolve_roster_textures.py`
3. `python3 tools/fluxara_content/import_user_roster.py --apply --audit-only`

The first step refuses to overwrite differing pre-existing source files. All copied source files except track.xml are SHA-256 verified. Only the new descriptor's groups attribute changes to Fluxara. Source geometry, AI graph, quads, checkpoints, material physics and script files are preserved. Existing approved Canyon/Summit are never written.

Five exact texture copies restore missing historical names without changing SPM: grey-b1 extension alias for both Maple Overpass variants, stripes DDS-name alias for Skid Grounds, OBJ DDS-name alias for Motorsport Land, and neocity_concrete.png copied from the already selected Lap Catch with its license retained. Provenance: `texture-dependency-repairs.json`. Irrlicht falls back to detecting image content after extension lookup (`lib/irrlicht/source/Irrlicht/CNullDriver.cpp:1322`), so PNG bytes remain unchanged at the historical DDS filenames. Rendering still needs checking.

Shared stock dependencies resolve against `../fluxara_drift-assets`, which contains the stock library/music/textures. The partial reference-runtime extraction is not an adequate library baseline. Track-local `library/<name>` is supported by `src/tracks/track_object_presentation.cpp:209`–226 and already copied with Canyon42. No wholesale stock-library duplication was added.

Final selected resources:725,577,901bytes.11entries retain static warnings; exact findings are in the JSON. Strongest remaining issues: Motorsport Land mesh texture table references missing `SZK.dds`; Green Hill scene directly references absent `fluxara_driftlib_wilbertCam_a`. Orbital Simulation's `reset.spm` references missing `icon.png`, but reset.spm has no XML scene reference, so runtime use is unproven. Other warnings concern material/normal/gloss declarations and Subsea's animated texture; declarations may be unused and must not be silently replaced by arbitrary similarly named textures.

Ghost matching replay files and offline CTF AI remain unresolved. No simulator, phone, build or gameplay tests were run by this import task. CMake packaging and gameplay/UI mode dispatch belong to the coordinating agents.

## Exact-resource follow-up

The two strongest missing dependencies remain unresolved; no stand-in was installed.

- Motorsport Land's original revision-1 ZIP (`https://online.fluxaradrift.net/dl/1519848119642c252b3d5cc.zip`, SHA-256 `f59f70d652536abcd72f78f3ef510643f106d40a9226c3dafdc68bf2a1e67479`) has no `SZK.dds`. Its mesh texture table requests that exact filename. The retained license attributes the Assetto Corsa port to CrystalDaEevee and original track to Frito (ZFLB), with GNU GPL / CC-BY-SA 3.0 stated. Neither the downloaded catalog nor available stock resources yielded an exact SZK asset.
- Green Hill's source ZIP (SHA-256 `b3254e41cd34baec823cd838daf42cbe8688ac88aa8f1c472f27890ed9544f77`) omits `fluxara_driftlib_wilbertCam_a`, despite `scene.xml:387` using that library. Another catalog track, Stadium V, also references it without supplying it. The historical `Nomagno/fluxara_drift-assets` README credits this name to GeekPenguinBR / TuxKartDriver (2016, CC-BY-SA 3.0), but its current recursive tree has no corresponding directory. Its similarly named `fluxara_driftlib_wilbertSecurity_a` is a different asset and was not substituted. The exact SourceForge SVN library URL also returned 404. An attribution mention is not the missing model itself.

After the coordinator regenerated `build-ios/FluxaraDrift.xcodeproj/project.pbxproj`, Canyon42's `library` is a folder-type PBXFileReference included in a PBXCopyFilesBuildPhase targeting `data/tracks/fluxara-user-canyon-42` with resource destination spec 7. Thus the generated project retains the nested folder rather than flattening its contents. This is project-configuration evidence only, not inspection of the completed app bundle or runtime loading. Generated line numbers and object IDs can change on regeneration.
