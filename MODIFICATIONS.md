# Motorica modifications

This file identifies the prominent changes made by MOTORICA RESEARCH LLC to
the upstream SuperTuxKart code base. It is not a substitute for the Git
history; the complete source and commit history remain authoritative.

## iOS integration

- Added the `motorica-stk` URL scheme so Motorica Start can open the game.
- Added local exchange of controller snapshots through an Apple App Group.
- Added a permanent launch-mode state machine. Only a valid `motorica-stk://`
  URL enables Motorica Start mode; a recent App Group snapshot or an installed
  asset package cannot silently switch a direct launch.
- Added Motorica Training Hub for direct launches, with a separate Motorica
  Night Island, Motorica Kiki kart ID, and fixed Motorica Signal Circuit race.
- Direct launches expose no upstream kart/track selection and never scan the
  downloaded full catalog.
- Added pause and connection-state handling for Motorica Start sessions.
- Added game-version snapshots used by Motorica Start to identify the installed
  game build.
- Centralized the App Group identifier in the
  `MOTORICA_GAME_CONTROL_APP_GROUP` Xcode build setting. Entitlements,
  Info.plist, and runtime code resolve the same setting, preventing the group
  name from drifting between signing and application logic.
- Added Motorica Apple signing identifiers and the App Store bundle identifier.
- Added a user-confirmed, data-only full catalog download for Motorica Start
  mode. The archive has a build-pinned URL, exact size and SHA-256 embedded in
  the application.
- Added archive path, extension, symlink and uncompressed-size validation plus
  atomic installation with rollback. AngelScript stays in the reviewed IPA
  and downloaded tracks resolve only to the bundled script registry.

The main implementation is in:

- `src/input/motorica_game_control_ios.mm`
- `src/input/motorica_game_control_ios.hpp`
- `src/input/multitouch_device.cpp`
- `src/main.cpp`
- `src/states_screens/motorica_hub_screen.cpp`
- `src/utils/extract_mobile_assets.cpp`
- `tools/motorica_assets/build_assets.py`
- `motorica-assets-overlay/`
- `data/SuperTuxKart-Info-iOS.plist`
- `data/SuperTuxKart-iOS.entitlements`
- `cmake/Toolchain-ios-xcode.cmake`

## Android integration

- Added Motorica Start launch and controller integration.
- Added release packaging and architecture support used for Motorica store
  distribution.
- Added temporary standalone controls required for store review builds.

## Product and documentation

- Added Motorica support and privacy pages.
- Added release signing configuration, application identifiers, icons, and
  App Store build metadata.
- Preserved upstream copyright, credit, and license notices.

## Upstream

The upstream project is <https://github.com/supertuxkart/stk-code>. This fork
is maintained independently and is not endorsed by the upstream project.
