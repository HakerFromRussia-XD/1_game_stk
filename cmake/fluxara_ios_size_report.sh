#!/bin/sh
# Produce a deterministic size report for a finished, signed Fluxara .app.
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: $0 <Fluxara Drift.app> [report-directory]" >&2
    exit 64
fi

bundle=$1
report_dir=${2:-"$(dirname "$bundle")/size-report"}
data="$bundle/data"

[ -d "$bundle" ] || { echo "missing app bundle: $bundle" >&2; exit 66; }
[ -d "$data" ] || { echo "missing app data: $data" >&2; exit 66; }

mkdir -p "$report_dir/Payload"
rm -rf "$report_dir/Payload/Fluxara Drift.app"
/usr/bin/ditto "$bundle" "$report_dir/Payload/Fluxara Drift.app"
/usr/bin/ditto -c -k --keepParent "$report_dir/Payload" "$report_dir/FluxaraDrift.ipa"
rm -rf "$report_dir/Payload"

report="$report_dir/fluxara-ios-size-report.txt"
tsv="$report_dir/fluxara-ios-size-report.tsv"
bundle_bytes=$(find "$bundle" -type f -print0 | xargs -0 stat -f '%z' | awk '{sum += $1} END {print sum + 0}')
ipa_bytes=$(stat -f '%z' "$report_dir/FluxaraDrift.ipa")
tracks=$(find "$data/tracks" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')
karts=$(find "$data/karts" -mindepth 1 -maxdepth 1 -type d -name 'fluxara-*' | wc -l | tr -d ' ')

{
    echo "Fluxara Drift iOS size report"
    echo "bundle=$bundle"
    echo "bundle_bytes=$bundle_bytes"
    echo "bundle_mib=$(awk "BEGIN { printf \"%.1f\", $bundle_bytes / 1048576 }")"
    echo "ipa=$report_dir/FluxaraDrift.ipa"
    echo "ipa_bytes=$ipa_bytes"
    echo "ipa_mib=$(awk "BEGIN { printf \"%.1f\", $ipa_bytes / 1048576 }")"
    echo "tracks=$tracks"
    echo "karts=$karts"
    echo
    echo "top_level_data_kib"
    du -sk "$data"/* 2>/dev/null | sort -nr
    echo
    echo "track_kib"
    du -sk "$data/tracks"/* 2>/dev/null | sort -nr
    echo
    echo "extension_mib"
    find "$data" -type f -print0 | xargs -0 stat -f '%z %N' | \
        awk '{bytes=$1; sub(/^[0-9]+ /, ""); name=$0; sub(/^.*\//, "", name); original=name; sub(/^.*\./, "", name); if (name == original) name="[none]"; totals[name]+=bytes} END {for (name in totals) printf "%.1f %s\n", totals[name]/1048576, name}' | sort -nr
} > "$report"

{
    echo "category\tbytes\tmib"
    printf 'bundle\t%s\t' "$bundle_bytes"; awk "BEGIN { printf \"%.1f\\n\", $bundle_bytes / 1048576 }"
    printf 'ipa\t%s\t' "$ipa_bytes"; awk "BEGIN { printf \"%.1f\\n\", $ipa_bytes / 1048576 }"
    find "$data" -mindepth 1 -maxdepth 1 -print0 | while IFS= read -r -d '' path
    do
        bytes=$(find "$path" -type f -print0 | xargs -0 stat -f '%z' | awk '{sum += $1} END {print sum + 0}')
        printf '%s\t%s\t' "$(basename "$path")" "$bytes"
        awk "BEGIN { printf \"%.1f\\n\", $bytes / 1048576 }"
    done
} > "$tsv"

cat "$report"
