# Building the Motorica iOS application

These instructions describe the source layout and configuration used for the
Motorica App Store build. Xcode, CMake, the game assets, and the iOS dependency
archives are required.

## Release identity

- App Store version: `1.0`
- build number: `28`
- bundle identifier: `com.motorica.games.stktt`
- Apple Developer team: `WWLXR9V94H`
- App Group build setting:
  `MOTORICA_GAME_CONTROL_APP_GROUP=group.com.motorica.start.gamecontroll`

The App Group has a single source of truth in
`cmake/Toolchain-ios-xcode.cmake`. Do not place a second literal identifier in
the entitlements or Objective-C++ runtime code.

## Inputs

1. Clone the corresponding release source. For local development, use the
   current branch until the final build-28 source tag is created:

   ```sh
   git clone https://github.com/HakerFromRussia-XD/1_game_stk.git
   cd 1_game_stk
   ```

2. Obtain the source-compatible iOS dependencies from the SuperTuxKart
   dependency project and prepare these directories in the repository root:

   - `dependencies-iphoneos`
   - `dependencies-iphonesimulator`

   Dependency sources and releases:
   <https://github.com/supertuxkart/dependencies>

3. Prepare the compatible upstream assets at
   `/Users/motoricallc/Downloads/stk-assets`, then build the tracked Motorica
   overlay, the minimal IPA assets, and the data-only full package:

   ```sh
   python3 tools/motorica_assets/build_assets.py all
   ```

   The generated minimal source is
   `build-motorica-ios-assets/assets/data`. Never edit ignored
   `build-ios-assets` or a generated build directory as the source of truth.

## Generate the Xcode project

Configure with the generated minimal asset directory:

```sh
cmake -S . -B build-ios -G Xcode \
  -DDEPS_PATH="$PWD" \
  -DIOS_ASSETS="$PWD/build-motorica-ios-assets/assets/data" \
  -DCMAKE_TOOLCHAIN_FILE=cmake/Toolchain-ios-xcode.cmake
```

Open:

```text
build-ios/SuperTuxKart.xcodeproj
```

Select the `supertuxkart` scheme and an iOS device. Signing uses the Denis
Oskhin Personal Team and requires a provisioning profile that contains both
the bundle identifier and App Group listed above.

Automatic Signing may create a development-signed product for device testing.
Do not upload a development-signed product directly; the final distribution
operation must use a compatible App Store distribution identity and profile
with the same Bundle ID and App Group.

## Command-line verification

```sh
xcodebuild \
  -project build-ios/SuperTuxKart.xcodeproj \
  -scheme supertuxkart \
  -configuration Release \
  -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  build
```

Before submission, inspect the signed product and confirm that its identifier,
team identifier, and application-groups entitlement match this document.
Also compare `dwarfdump --uuid` for the application executable and
`dSYMs/supertuxkart.app.dSYM/Contents/Resources/DWARF/supertuxkart` inside the
archive; the UUIDs must be identical.

Also confirm that the IPA contains only `motorica_night_island`,
`motorica_signal_circuit`, and `motorica_kiki`; that all 24 upstream
AngelScript files are under `data/packaged-scripts`; and that the remote ZIP
contains no executable or script files.
