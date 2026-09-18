"""Verify curated resource copies in an already built iOS app (not gameplay)."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / 'iosApp/FluxaraResources'
    data = args.app / 'data'
    failures = []
    checked = 0
    events = ET.parse(source / 'fluxara-campaign.xml').getroot().findall('event')
    karts = json.loads((root / 'docs/fluxara-content/karts-15.json').read_text())
    kart_ids = karts['existing'] + [k['id'] for k in karts['added']]
    assert len(events) == 50 and len(set(kart_ids)) == 15
    paths = [source / 'fluxara-campaign.xml']
    folders = [source / 'tracks' / e.attrib['track'] for e in events]
    folders += [source / 'karts' / k for k in kart_ids]
    folders += [source / 'gui/fluxara', source / 'gui/screens']
    for folder in folders:
        if not folder.is_dir():
            failures.append('missing source directory: ' + str(folder))
        paths.extend(p for p in folder.rglob('*') if p.is_file())
    for path in sorted(set(paths)):
        # Documentation is not required for UI rendering; retained track/kart
        # license files, on the other hand, are checked with all package files.
        relative = path.relative_to(source)
        if str(relative).startswith('gui/fluxara/') and path.suffix != '.png':
            continue
        target = data / relative
        checked += 1
        if not target.is_file():
            failures.append('missing: ' + str(relative))
        elif hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
            failures.append('different: ' + str(relative))
    print(json.dumps({'scope': 'resource copies only', 'checked': checked,
                      'failures': failures}, indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
