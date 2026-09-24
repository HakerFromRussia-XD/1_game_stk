#!/bin/sh
# Resize only generated iOS bundle HUD rasters. The approved Figma masters
# stay untouched. A 512px HUD layer exceeds its largest iPhone render cell.
set -eu

bundle=${1:?missing app bundle}
hud="$bundle/data/gui/fluxara/hud"
[ -d "$hud" ] || exit 66

for image in "$hud"/*.png; do
    [ -f "$image" ] || continue
    # No-op for small icons; sips preserves the alpha channel of large layers.
    size=$(/usr/bin/sips -g pixelWidth -g pixelHeight "$image" |
        /usr/bin/awk '/pixelWidth:/ { w=$2 } /pixelHeight:/ { h=$2 }
            END { print w > h ? w : h }')
    if [ "$size" -gt 512 ]; then
        /usr/bin/sips -s format png --resampleHeightWidthMax 512 "$image" \
            --out "$image" >/dev/null
    fi
done
