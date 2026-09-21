#!/bin/sh
# Fast asset-only iteration for Fluxara Drift.  This deliberately targets an
# already-built iOS Simulator bundle and never invokes an iphoneos build.
set -eu

if [ "$#" -ne 2 ] && [ "$#" -ne 3 ]; then
    echo "usage: $0 <simulator-udid> <Fluxara Drift.app> [--restart]" >&2
    exit 64
fi

fluxara_simulator_udid="$1"
fluxara_app_bundle="$2"
fluxara_restart="${3:-}"
fluxara_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fluxara_cmake=$(command -v cmake)

if [ ! -d "$fluxara_app_bundle" ]; then
    echo "simulator bundle does not exist: $fluxara_app_bundle" >&2
    exit 66
fi

# UI files only: karts and tracks remain untouched, avoiding the expensive
# recursive asset overlay performed by the normal post-build phase.
/usr/bin/rsync -a "$fluxara_root/iosApp/FluxaraResources/gui/screens/" \
    "$fluxara_app_bundle/data/gui/screens/"
/usr/bin/rsync -a --delete "$fluxara_root/iosApp/FluxaraResources/gui/fluxara/" \
    "$fluxara_app_bundle/data/gui/fluxara/"
/usr/bin/rsync -a --delete "$fluxara_root/iosApp/FluxaraResources/skins/fluxara/" \
    "$fluxara_app_bundle/data/skins/fluxara/"
"$fluxara_cmake" -E copy_if_different \
    "$fluxara_root/iosApp/FluxaraResources/fluxara-campaign.xml" \
    "$fluxara_app_bundle/data/fluxara-campaign.xml"
"$fluxara_cmake" -E copy_if_different \
    "$fluxara_root/data/po/ru.po" \
    "$fluxara_app_bundle/data/po/ru.po"

# The default is the UI synchronization itself.  Restart is explicit because
# simulator process start-up is not an asset-sync cost and can dominate an
# otherwise sub-second edit.  Do not replace this with a generic device install.
if [ -n "$fluxara_restart" ]; then
    if [ "$fluxara_restart" != "--restart" ]; then
        echo "unknown option: $fluxara_restart" >&2
        exit 64
    fi
    # The copied UI files must be included in the bundle signature before
    # simctl receives it.  This path is deliberately restart-only: the normal
    # hot UI sync remains a sub-second file copy.
    /usr/bin/codesign --force --sign - "$fluxara_app_bundle"
    xcrun simctl terminate "$fluxara_simulator_udid" io.fluxara.drift >/dev/null 2>&1 || true
    xcrun simctl install "$fluxara_simulator_udid" "$fluxara_app_bundle"
    xcrun simctl launch "$fluxara_simulator_udid" io.fluxara.drift
fi
