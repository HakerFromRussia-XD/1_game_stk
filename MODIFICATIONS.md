# Motorica modifications

This file identifies the prominent changes made by MOTORICA RESEARCH LLC to
the upstream SuperTuxKart code base. It is not a substitute for the Git
history; the complete source and commit history remain authoritative.

## iOS integration

- Added the `motorica-stk` URL scheme so Motorica Start can open the game.
- Added local exchange of controller snapshots through an Apple App Group.
- Added launch-mode detection so a Motorica Start launch uses Motorica device
  control, while a direct Home Screen launch retains standard touch and motion
  controls for independent operation and App Review.
- Added pause and connection-state handling for Motorica Start sessions.
- Added game-version snapshots used by Motorica Start to identify the installed
  game build.
- Centralized the App Group identifier in the
  `MOTORICA_GAME_CONTROL_APP_GROUP` Xcode build setting. Entitlements,
  Info.plist, and runtime code resolve the same setting, preventing the group
  name from drifting between signing and application logic.
- Added Motorica Apple signing identifiers and the App Store bundle identifier.

The main implementation is in:

- `src/input/motorica_game_control_ios.mm`
- `src/input/motorica_game_control_ios.hpp`
- `src/input/multitouch_device.cpp`
- `src/main.cpp`
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
