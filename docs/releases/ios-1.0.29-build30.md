# Fluxara Drift — iOS release 1.0.29 (30)

Release build for iPhone and iPad. Bundle ID: `io.fluxara.drift`.
This is an iOS App Store resubmission following the Guideline 4 design rejection
of build 29. The marketing version remains 1.0.29; the build increments to 30.

## Changes

- Enable native iPad support alongside iPhone (`UIDeviceFamily = [1, 2]`).
- Fit the race HUD and touch targets to both dimensions of the window.
- Fill the complete window with portrait menu backgrounds.
- Bind touch controls to the local player for immediate race launches.
- Restore missing original track music and preserve its paths during packaging.
- Fix static dependency paths for Xcode Archive.

## Included repository maintenance

This commit also includes the previously pending platform identity separation
(Android STK / iOS Fluxara), permanent Android and iOS resource inputs, build
script/documentation updates, and removal of the old track authoring asset pack,
track-rework snapshots and related documentation. Android changes are included
at the developer's explicit request; this release build targets iOS only.
Android was not rebuilt or validated during this release preparation.

## Validation

The simulator build succeeded on iPad Air 11-inch (M3), iPadOS 18.4.
The developer manually tested the controls and confirmed that everything works.
No connected physical iPhone was available for this release preparation.
App Store archive/export results are recorded with the generated artifacts.

The campaign preflight passes for all 50 events/tracks and 15 karts.
Original music declarations and payloads missing from the permanent iOS base
have been restored from the project resources. Packaging keeps music files
beside their descriptors; a regression fixture verified that ordinary shared
sound effects remain deduplicated. The source audit now resolves shared
library nodes from the Fluxara overlay as well as the base resources.

The Xcode Archive configuration keeps dependency libraries at CMake's link
paths instead of relocating them into UninstalledProducts.

## Review notes draft

This build addresses the Guideline 4 design issue reported for build 29.
Fluxara Drift now supports iPad natively with full-screen presentation.
The race HUD and touch controls scale to fit the app window, and menu
backgrounds fill the display. The updated interface was checked on an
11-inch iPad Air (M3) simulator.

## Release status

Prepared for release packaging. This file does not indicate an upload,
App Review submission, or App Store approval.
