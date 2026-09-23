#!/bin/sh
# Remove only source/authoring files from the fully overlaid iOS app bundle.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <Fluxara Drift.app>" >&2
    exit 64
fi

bundle=$1
data="$bundle/data"
[ -d "$data" ] || { echo "missing bundle data: $data" >&2; exit 66; }

garage="$data/gui/fluxara/home"
rm -f \
    "$garage/garage-background.png" \
    "$garage/garage-background-figma.png" \
    "$garage/garage-background-outpaint-v1.png" \
    "$garage/garage-background-outpaint-v2.png" \
    "$garage/garage-floor-extension-v1.png" \
    "$data/skins/fluxara/data/ttf/Baloo2-ExtraBold.ttf" \
    "$data/skins/fluxara/data/ttf/Baloo2-ExtraBold-Cyrillic.ttf"

find "$data" -type f \( \
    -name '*.xcf' -o -name '*.pot' -o -name '*.py' -o -name '*.sh' \
    -o -name '*.md' -o -name '*.desktop' -o -name '*.metainfo.xml' \
\) -delete

# Deduplicate only byte-identical root-level track resources after every
# Fluxara overlay has been applied.  The script keeps screenshots in their
# track folders and uses the engine's existing global texture/SFX/music paths.
/usr/bin/ruby "$(dirname "$0")/DeduplicateFluxaraTrackResources.rb" "$bundle"

if [ "${FLUXARA_IOS_TEXTURE_FORMAT:-none}" = "astc" ]; then
    : "${FLUXARA_ASTCENC:?missing host ASTC encoder}"
    : "${FLUXARA_ASTC_CACHE:?missing ASTC cache directory}"
    /usr/bin/ruby "$(dirname "$0")/CompressFluxaraIosTextures.rb" \
        "$bundle" "$FLUXARA_ASTCENC" "$FLUXARA_ASTC_CACHE"
fi

if [ "${FLUXARA_IOS_AUDIO_FORMAT:-none}" = "opus" ]; then
    : "${FLUXARA_SOX:?missing host SoX}"
    : "${FLUXARA_WAV_TO_OPUS:?missing host wav-to-opus encoder}"
    : "${FLUXARA_OPUS_CACHE:?missing Opus cache directory}"
    /usr/bin/ruby "$(dirname "$0")/CompressFluxaraIosAudio.rb" \
        "$bundle" "$FLUXARA_SOX" "$FLUXARA_WAV_TO_OPUS" "$FLUXARA_OPUS_CACHE"
fi

echo "FLUXARA_IOS_BUNDLE_FINALIZED bundle=$bundle"
