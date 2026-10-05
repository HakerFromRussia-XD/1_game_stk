#!/bin/sh
# Remove only source/authoring files from the fully overlaid iOS app bundle.
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <Fluxara Drift.app>" >&2
    exit 64
fi

bundle=$1
case "$bundle" in
    *.app) ;;
    *) echo "refusing to finalize a non-app path: $bundle" >&2; exit 64 ;;
esac
data="$bundle/data"
[ -d "$data" ] || { echo "missing bundle data: $data" >&2; exit 66; }

garage="$data/gui/fluxara/home"
rm -f \
    "$garage/garage-background.png" \
    "$garage/garage-background-figma.png" \
    "$garage/garage-background-outpaint-v1.png" \
    "$garage/garage-background-outpaint-v2.png" \
    "$garage/garage-floor-extension-v1.png" \
    "$data/skins/fluxara/background.png" \
    "$data/skins/fluxara/data/ttf/Baloo2-ExtraBold.ttf" \
    "$data/skins/fluxara/data/ttf/Baloo2-ExtraBold-Cyrillic.ttf"

# iOS always resolves its public skin to Fluxara, whose only dependency is
# Classic. Keep those and Common; remove only these known alternate themes
# from the generated bundle, never from the source asset library.
for skin in cartoon cartoon-coal cartoon-desert cartoon-forest cartoon-ocean \
            cartoon-ruby classic-coal classic-desert classic-forest \
            classic-ocean classic-ruby; do
    [ -d "$data/skins/$skin" ] && rm -rf "$data/skins/$skin"
done

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

# Debug symbols remain in the generated .dSYM. They need not occupy the
# installed app as well; Xcode signs the bundle after this post-build phase.
# MinSizeRel also retains local symbols by default, adding about 7 MiB.
case "${CONFIGURATION:-}" in
    Debug|MinSizeRel)
        /usr/bin/xcrun strip -S -x "$bundle/Fluxara Drift"
        ;;
esac

echo "FLUXARA_IOS_BUNDLE_FINALIZED bundle=$bundle"
