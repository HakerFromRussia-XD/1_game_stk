#!/usr/bin/env python3
"""Static mode capability counts; no runtime compatibility claim."""
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


def yes(v):
    return str(v).lower() in {'y', 'yes', 'true', '1'}


def inspect(root):
    counts = Counter()
    for path in root.glob('*/track.xml'):
        node = ET.parse(path).getroot()
        counts['total'] += 1
        if node.get('version') not in {'6', '7'}:
            counts['unsupported_version'] += 1
            continue
        arena, soccer, ctf = (yes(node.get(k)) for k in ('arena', 'soccer', 'ctf'))
        internal = yes(node.get('internal')) or yes(node.get('cutscene'))
        navmesh = (path.parent / 'navmesh.xml').is_file()
        counts['arena'] += arena
        counts['soccer'] += soccer
        counts['ctf'] += ctf
        counts['arena_with_navmesh'] += arena and navmesh
        counts['soccer_with_navmesh'] += soccer and navmesh
        counts['linear_with_graph_quads'] += not (arena or soccer or internal) and all((path.parent / p).is_file() for p in ('graph.xml', 'quads.xml'))
        eggs = path.parent / 'easter_eggs.xml'
        if eggs.is_file():
            try:
                counts['nonempty_egg_layout'] += any(len(child) for child in ET.parse(eggs).getroot())
            except ET.ParseError:
                counts['invalid_egg_xml'] += 1
    return dict(counts)


catalog = Path('.codex-downloads/fluxara-addon-catalog')
latest = {}
for node in ET.parse(catalog / 'online_assets.xml').getroot():
    if node.tag not in {'track', 'arena', 'kart'}:
        continue
    key = (node.tag, node.get('id'))
    if key not in latest or int(node.get('revision', 0)) > int(latest[key].get('revision', 0)):
        latest[key] = node.attrib
print(json.dumps({'downloaded_tracks': inspect(catalog / 'extracted/tracks'),
                  'downloaded_arenas': inspect(catalog / 'extracted/arenas'),
                  'original_app_tracks': inspect(Path('/private/tmp/original-fluxara_drift-pre-fluxara.app/data/tracks')),
                  'manifest_latest_counts': dict(Counter(k[0] for k in latest)),
                  'manifest_arena_v6_v7': sum(k[0] == 'arena' and v.get('format') in {'6', '7'} for k,v in latest.items()),
                  'manifest_arena_v6_v7_approved': sum(k[0] == 'arena' and v.get('format') in {'6', '7'} and bool(int(v.get('status', 0)) & 1) for k,v in latest.items()),
                  'caveat': 'File/flag counts only; navmesh validity, teams/flags, egg placement, runtime and rights unverified.'}, indent=2))
