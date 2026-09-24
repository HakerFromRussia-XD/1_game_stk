#!/bin/sh
# Copy exactly the reviewed starter set to an iOS bundle.  The remaining
# campaign directories stay in source control to build signed data-only packs.
set -eu

source_root=${1:?missing source tracks root}
destination_root=${2:?missing destination tracks root}

starter_tracks='
fluxara-canyon
fluxara-user-ski-dash
fluxara-user-dust-cross-split-combat
fluxara-user-spell-lab
fluxara-user-orbital-simulation---soccer
fluxara-user-dp-motorsports-land-ii
fluxara-user-lap-catch
fluxara-user-motorsport-land
fluxara-summit-run
fluxara-user-volcano-remake
'

mkdir -p "$destination_root"

# A reused incremental Xcode bundle can still contain a previously embedded
# Fluxara track.  Delete only Fluxara-prefixed directories in this generated
# bundle location before putting the exact starter set back.
for destination in "$destination_root"/fluxara-*; do
    [ -d "$destination" ] || continue
    name=${destination##*/}
    case "
$starter_tracks
" in
        *"
$name
"*) ;;
        *) rm -rf "$destination" ;;
    esac
done

for track in $starter_tracks; do
    /usr/bin/rsync -a --delete "$source_root/$track/" "$destination_root/$track/"
done
