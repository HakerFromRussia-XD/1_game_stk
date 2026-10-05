#!/bin/sh
# Resize only generated iOS bundle HUD rasters. The approved Figma masters
# stay untouched. A 512px HUD layer exceeds its largest iPhone render cell.
set -eu

bundle=${1:?missing app bundle}
hud="$bundle/data/gui/fluxara/hud"
[ -d "$hud" ] || exit 66

resize_if_larger() {
    image=$1
    limit=$2
    [ -f "$image" ] || return 0
    size=$(/usr/bin/sips -g pixelWidth -g pixelHeight "$image" |
        /usr/bin/awk '/pixelWidth:/ { w=$2 } /pixelHeight:/ { h=$2 }
            END { print (w > h ? w : h) }')
    if [ "$size" -gt "$limit" ]; then
        /usr/bin/sips -s format png --resampleHeightWidthMax "$limit" "$image" \
            --out "$image" >/dev/null
    fi
}

for image in "$hud"/*.png; do
    [ -f "$image" ] || continue
    resize_if_larger "$image" 512
done

# Pause artwork is drawn in an 844x390 layout on a 3x iPhone. Keep at least
# its physical on-screen resolution, without packaging the oversized exports.
pause="$bundle/data/gui/fluxara/pause"
for name in logo star icon-exit checkers-left checkers-right; do
    resize_if_larger "$pause/$name.png" 512
done
resize_if_larger "$pause/panel.png" 1024
for name in button-continue button-restart button-settings button-exit; do
    resize_if_larger "$pause/$name.png" 768
done

# Garage stats are capped at 512px by the engine texture loader. A 1024px
# packaged image still exceeds that runtime limit and allows future HD use.
resize_if_larger "$bundle/data/gui/fluxara/stats/fluxara-panel-transparent.png" 1024

# These two fullscreen backdrops have no alpha. JPEG 98 retains their native
# dimensions and avoids shipping multi-megabyte lossless PNGs.
for relative in home/home-background race/background; do
    png="$bundle/data/gui/fluxara/$relative.png"
    jpg="$bundle/data/gui/fluxara/$relative.jpg"
    [ -f "$png" ] || continue
    /usr/bin/sips -s format jpeg -s formatOptions 98 "$png" --out "$jpg" >/dev/null
    [ -s "$jpg" ] || exit 74
    rm -f "$png"
done

# These exact source revisions were inspected and are fully opaque despite
# carrying a PNG alpha channel. Fail closed if either master changes: a new
# transparent export must not silently lose its alpha in the iOS package.
convert_reviewed_opaque() {
    png=$1
    jpg=$2
    expected_sha=$3
    [ -f "$png" ] || { [ -s "$jpg" ] && return 0; exit 66; }
    actual_sha=$(/usr/bin/shasum -a 256 "$png" | /usr/bin/awk '{ print $1 }')
    [ "$actual_sha" = "$expected_sha" ] || {
        echo "review required for changed opaque artwork: $png" >&2
        exit 65
    }
    /usr/bin/sips -s format jpeg -s formatOptions 98 "$png" --out "$jpg" >/dev/null
    [ -s "$jpg" ] || exit 74
    rm -f "$png"
}

convert_reviewed_opaque \
    "$bundle/data/gui/fluxara/home/garage-background-figma-outpaint-v1.png" \
    "$bundle/data/gui/fluxara/home/garage-background-figma-outpaint-v1.jpg" \
    71e68f6967fb1c088a9ec93f50a3429a146f3fca9746c68c9e9fbc9d0dddaa4f
convert_reviewed_opaque \
    "$bundle/data/skins/fluxara/background-v2.png" \
    "$bundle/data/skins/fluxara/background-v2.jpg" \
    ba303c511aa33d7f793e8cd0dfa54c32f1ac9630fc682bee9212de462dfa5ee8
