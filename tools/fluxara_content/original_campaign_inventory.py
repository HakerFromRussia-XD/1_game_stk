#!/usr/bin/env python3
"""Inventory original challenge/GP XML; no game launch or data mutation."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter

root = Path(__file__).resolve().parents[2]
events, unlocks, tracks, modes = [], [], set(), Counter()
for path in sorted((root / 'data/challenges').glob('*.challenge')):
    node = ET.parse(path).getroot()
    requirements = node.find('requirements')
    if node.find('unlock_list').get('list') == 'true':
        unlocks.append(path.stem)
        continue
    mode = node.find('mode').attrib
    ids = []
    if node.find('track') is not None:
        ids = [node.find('track').get('id')]
    if node.find('grandprix') is not None:
        gp = root / 'data/grandprix' / (node.find('grandprix').get('id') + '.grandprix')
        ids = [t.get('id') for t in ET.parse(gp).getroot().findall('track')]
    tracks.update(ids)
    modes[mode['minor']] += 1
    events.append({'challenge': path.stem, 'source': str(path.relative_to(root)), 'mode': mode,
                   'tracks': ids, 'requirements': requirements.attrib,
                   'difficulty_requirements': {d: node.find(d).find('requirements').attrib for d in ('easy', 'medium', 'hard', 'best')}})
print(json.dumps({'unique_tracks': len(tracks), 'track_ids': sorted(tracks), 'race_challenges': len(events),
                  'unlock_only': unlocks, 'minor_modes': modes, 'events': events}, indent=2))
