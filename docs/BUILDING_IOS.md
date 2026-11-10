# Building Fluxara Drift for iOS

Android STK and iOS Fluxara Drift share the engine in this checkout.
The iOS runtime inputs are `iosApp/BaseResources` and the current
`iosApp/FluxaraResources` overlay. No previous build or downloaded catalog
is required. Keep `dependencies-iphoneos` in the repository root.

## Device build

```sh
cmake -S . -B build-ios-device -G Xcode \
  -DDEPS_PATH="$PWD" \
  -DCMAKE_TOOLCHAIN_FILE=cmake/Toolchain-ios-xcode.cmake \
  -DFLUXARA_IOS_PLATFORM=iphoneos -DCHECK_ASSETS=OFF
xcodebuild -project build-ios-device/FluxaraDrift.xcodeproj \
  -target fluxaradrift -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' build
```

`IOS_ASSETS` defaults to the permanent base resources; override it only to
use another compatible input tree. The generated project and products may
be deleted and recreated.

The bundle identifier is `io.fluxara.drift`, the developer team is
`R7M384QD5A`, and the input bridge App Group is
`group.io.fluxara.drift.inputbridge`. These settings are defined in
`cmake/Toolchain-ios-xcode.cmake`. The current resource version is maintained
by `cmake/UpdateFluxaraIosVersion.py`; inspect the resulting Info.plist for
its marketing and build versions.

Signing and provisioning must match the bundle and App Group. A successful
build verifies compilation and resource packaging. Installation, runtime
validation, archiving, and App Store publication are separate operations.

## iPad support

The application targets both iPhone and iPad (`TARGETED_DEVICE_FAMILY=1,2`).
The iOS Info.plist requests full-screen presentation, portrait menus and
landscape races on iPad as well as iPhone. Race HUD artwork and touch bounds
fit the actual window using the smaller of the width and height scales for
the 844 x 390 design. The renderer uses the full window; the HUD design frame
does not constrain the 3D viewport.

Regenerate the Xcode project and build a new bundle after changing supported
device families. An existing installed app or uploaded archive is unchanged.
