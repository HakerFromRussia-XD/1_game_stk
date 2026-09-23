#!/bin/sh
# Assemble the iOS runtime baseline from an explicit allowlist. Fluxara
# overlays its own screens, karts and tracks afterwards in CMakeLists.txt.
set -eu

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <generated-data-source> <bundle-data-directory>" >&2
    exit 64
fi

source_root=$1
target_root=$2

[ -d "$source_root" ] || {
    echo "missing generated iOS data source: $source_root" >&2
    exit 66
}

case "$target_root" in
    */data) ;;
    *)
        echo "refusing to prepare a destination outside an app data directory: $target_root" >&2
        exit 64
        ;;
esac

mkdir -p "$target_root"

copy_required() {
    entry=$1
    [ -e "$source_root/$entry" ] || {
        echo "missing required iOS runtime resource: $entry" >&2
        exit 66
    }
    /usr/bin/rsync -a --delete "$source_root/$entry" "$target_root/"
}

# Files read before a track is selected, plus generic engine data used by the
# race modes. Do not add a folder merely because it exists in upstream FLUXARA_DRIFT.
for entry in \
    achievements.xml cacert.pem country_names.tsv graphical_restrictions.xml \
    items.xml official_karts.xml fluxaradrift.git \
    kart_characteristics.xml powerup.xml skin_names.xml fluxara_drift_config.xml \
    thaidict.txt tips.xml \
    challenges gamerzilla gfx grandprix gui library models music packaged-scripts \
    replay sfx shaders skins textures
do
    copy_required "$entry"
done

# Fluxara iOS deliberately supports Russian and English only. English is the
# engine's built-in fallback and therefore has no en.po file. The file manager
# requires a base ttf asset during startup even though Fluxara then prepends
# its own Baloo Cyrillic face from the selected skin.
rm -rf "$target_root/po" "$target_root/ttf"
mkdir -p "$target_root/po"
for locale in ru.po
do
    [ -f "$source_root/po/$locale" ] || {
        echo "missing selected Fluxara locale: $locale" >&2
        exit 66
    }
    /usr/bin/rsync -a "$source_root/po/$locale" "$target_root/po/"
done

# Keep only the two Latin fallback faces referenced below. The Fluxara skin
# remains the first face and supplies Russian glyphs.
mkdir -p "$target_root/ttf"
for font in Cantarell-Regular.otf SigmarOne.otf
do
    [ -f "$source_root/ttf/$font" ] || {
        echo "missing required Fluxara fallback font: $font" >&2
        exit 66
    }
    /usr/bin/rsync -a "$source_root/ttf/$font" "$target_root/ttf/"
done

# Do not leave fluxara_drift_config.xml pointing to fonts deliberately excluded above:
# FontManager resolves every listed base font before the Fluxara skin loads.
/usr/bin/perl -0pi -e 's{<fonts-list\b[^>]*/>}{<fonts-list normal-ttf="Cantarell-Regular.otf" digit-ttf="SigmarOne.otf"/>}s' \
    "$target_root/fluxara_drift_config.xml"

# Build, authoring and desktop metadata cannot be loaded by the iOS runtime.
find "$target_root" -type f \( \
    -name '*.xcf' -o -name '*.pot' -o -name '*.py' -o -name '*.sh' \
    -o -name '*.md' -o -name '*.desktop' -o -name '*.metainfo.xml' \
\) -delete

echo "FLUXARA_IOS_RUNTIME_BASE source=$source_root target=$target_root locales=ru,en-fallback"
