#!/bin/sh
# Package the permanent Android STK runtime resources kept in this repository.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_root="$script_dir/ResourceSource"
output_root="${OUTPUT_PATH:-$script_dir/assets}"
case "$output_root" in /*) ;; *) output_root="$script_dir/$output_root" ;; esac
[ -f "$source_root/stk_config.xml" ] || { echo "Missing Android STK ResourceSource" >&2; exit 1; }
[ "$output_root" != "$source_root" ] || { echo "Output cannot replace ResourceSource" >&2; exit 1; }
mkdir -p "$output_root/data"
/usr/bin/rsync -a --delete "$source_root/" "$output_root/data/"
printf 'has_assets\n' > "$output_root/has_assets.txt"
version="${PROJECT_VERSION:-git}"
printf 'STK Android resources\n' > "$output_root/data/supertuxkart.$version"
python3 - "$output_root" <<'METADATA'
from pathlib import Path
import sys
root = Path(sys.argv[1])
entries = ['data/'] + [p.relative_to(root).as_posix() + ('/' if p.is_dir() else '')
                       for p in (root / 'data').rglob('*')]
(root / 'files.txt').write_text('\n'.join(sorted(entries)) + '\n')
(root / '.nomedia').touch()
METADATA
echo "Android STK assets: $output_root"
