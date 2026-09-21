#!/bin/sh
# Verifies that the iOS Simulator bundle contains only Fluxara's mobile UI.
# It does not build, install, or select a device SDK.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <Fluxara Drift.app>" >&2
    exit 64
fi

bundle="$1"
data="$bundle/data"
hud="$data/gui/fluxara/hud"

[ -d "$data" ] || { echo "missing bundle data: $data" >&2; exit 66; }
[ -d "$hud" ] || { echo "missing Fluxara HUD: $hud" >&2; exit 66; }

for asset in \
    steering-wheel.png accelerator.png throttle-pedal.png pause.png \
    nitro.png nitro-empty.png mirror.png reset.png drift.png \
    halo-idle.png halo-pressed.png counter-small.png counter-time.png \
    minimap-panel.png up.png down.png screen-other.png \
    bonus-zipper.png bonus-bowling.png bonus-bubblegum.png bonus-cake.png \
    bonus-anchor.png bonus-swap.png bonus-swatter.png bonus-rubber-ball.png \
    bonus-parachute.png bonus-plunger.png
do
    [ -f "$hud/$asset" ] || {
        echo "missing approved HUD asset: $asset" >&2
        exit 65
    }
done

if find "$data" \( -iname '*motorica*.stkgui' -o -iname '*signal*lab*' \
    -o -path '*/challenges/motorica_*' \) -print -quit | grep -q .
then
    echo "legacy Motorica content remains in iOS bundle" >&2
    exit 65
fi

if [ -d "$data/gui/icons/android" ]; then
    echo "legacy Android STK HUD masks remain in iOS bundle" >&2
    exit 65
fi

for retired_dir in \
    "$data/gui/screens/help" \
    "$data/gui/screens/online" \
    "$data/gui/screens/options" \
    "$data/gui/dialogs/online" \
    "$data/gui/icons/online"
do
    [ ! -d "$retired_dir" ] || {
        echo "retired STK UI remains in iOS bundle: $retired_dir" >&2
        exit 65
    }
done

# Fluxara provides the complete public flow.  Keeping upstream .stkgui files
# in the product makes the retired STK menus an accidental fallback and is not
# a successful UI cleanup even when the normal route does not open them.
legacy_screen=$(find "$data/gui/screens" -maxdepth 1 -type f -name '*.stkgui' \
    ! -name 'fluxara_*.stkgui' -print -quit)
[ -z "$legacy_screen" ] || {
    echo "legacy STK screen remains in iOS bundle: $legacy_screen" >&2
    exit 65
}
fluxara_screens=$(find "$data/gui/screens" -maxdepth 1 -type f \
    -name 'fluxara_*.stkgui' | wc -l | tr -d ' ')
[ "$fluxara_screens" = 6 ] || {
    echo "expected 6 Fluxara screens, found $fluxara_screens" >&2
    exit 65
}

tracks=$(find "$data/tracks" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')
karts=$(find "$data/karts" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')
[ "$tracks" = 50 ] || { echo "expected 50 Fluxara tracks, found $tracks" >&2; exit 65; }
[ "$karts" = 15 ] || { echo "expected 15 Fluxara karts, found $karts" >&2; exit 65; }

echo "FLUXARA_IOS_PACKAGE_AUDIT hud=27 screens=$fluxara_screens tracks=$tracks karts=$karts retired-ui=0 bundle=$bundle"
