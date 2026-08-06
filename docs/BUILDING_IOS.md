# Building the Motorica iOS application

These instructions describe the source layout and configuration used for the
Motorica App Store build. Xcode, CMake, the game assets, and the iOS dependency
archives are required.

## Release identity

- marketing version: `1.0.16`
- bundle identifier: `com.motorica.games.stkttt`
- Apple Developer team: `R7M384QD5A`
- App Group build setting:
  `MOTORICA_GAME_CONTROL_APP_GROUP=group.com.motorica.start.gamecontrolll`

The App Group has a single source of truth in
`cmake/Toolchain-ios-xcode.cmake`. Do not place a second literal identifier in
the entitlements or Objective-C++ runtime code.

## Inputs

1. Clone the corresponding release source:

   ```sh
   git clone --branch ios-appstore-1.0.16 \
     https://github.com/HakerFromRussia-XD/1_game_stk.git
   cd 1_game_stk
   ```

2. Obtain the source-compatible iOS dependencies from the SuperTuxKart
   dependency project and prepare these directories in the repository root:

   - `dependencies-iphoneos`
   - `dependencies-iphonesimulator`

   Dependency sources and releases:
   <https://github.com/supertuxkart/dependencies>

3. Generate or obtain the mobile asset tree. The configured source tree must
   end in `assets/data` and retain the asset license files.

## Generate the Xcode project

Replace `/absolute/path/to/assets` with the directory containing `assets/data`:

```sh
cmake -S . -B build-ios -G Xcode \
  -DDEPS_PATH="$PWD" \
  -DIOS_ASSETS=/absolute/path/to/assets \
  -DCMAKE_TOOLCHAIN_FILE=cmake/Toolchain-ios-xcode.cmake
```

Open:

```text
build-ios/SuperTuxKart.xcodeproj
```

Select the `supertuxkart` scheme and an iOS device. Signing requires access to
the MOTORICA RESEARCH LLC Apple Developer team and a provisioning profile that
contains both the bundle identifier and App Group listed above.

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
