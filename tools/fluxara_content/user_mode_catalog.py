#!/usr/bin/env python3
"""Map user-created content to mode-specific static prerequisites and previews."""
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageOps
from campaign_catalog import yes, license_info

catalog = Path('.codex-downloads/fluxara-addon-catalog')
out = Path('docs/fluxara-content')
latest = {}
for node in ET.parse(catalog / 'online_assets.xml').getroot():
    if node.tag not in {'track', 'arena'}:
        continue
    key = (node.tag, node.get('id'))
    if key not in latest or int(node.get('revision', 0)) > int(latest[key].get('revision', 0)):
        latest[key] = node.attrib
all_items, pools = [], defaultdict(list)
for kind, directory in [('track', 'tracks'), ('arena', 'arenas')]:
    for descriptor in sorted((catalog / 'extracted' / directory).glob('*/track.xml')):
        try:
            root = ET.parse(descriptor).getroot()
            scene = ET.parse(descriptor.parent / 'scene.xml').getroot()
        except (ET.ParseError, FileNotFoundError):
            continue
        if root.get('version') not in {'6', '7'}:
            continue
        asset_id = descriptor.parent.name
        metadata = latest.get((kind, asset_id), {})
        files = [p for p in descriptor.parent.rglob('*') if p.is_file()]
        licenses, labels = license_info(files)
        preview = descriptor.parent / root.get('screenshot', '')
        if not preview.is_file() or not licenses or labels == ['unclassified; inspect license file'] or not int(metadata.get('status', 0)) & 1:
            continue
        arena, soccer, ctf = (yes(root.get(k)) for k in ('arena', 'soccer', 'ctf'))
        navmesh = (descriptor.parent / 'navmesh.xml').is_file()
        graph_ok = all((descriptor.parent / n).is_file() for n in ('graph.xml', 'quads.xml'))
        if graph_ok:
            try:
                for n in ('graph.xml', 'quads.xml'): ET.parse(descriptor.parent / n)
            except ET.ParseError:
                graph_ok = False
        linear = not (arena or soccer or yes(root.get('internal')) or yes(root.get('cutscene'))) and graph_ok
        eggs = descriptor.parent / 'easter_eggs.xml'
        egg_layout = False
        if eggs.is_file():
            try:
                egg_layout = any(len(n) for n in ET.parse(eggs).getroot())
            except ET.ParseError:
                pass
        tags = [n.tag for n in scene.iter()]
        goals = sum(n.tag == 'goal' for n in scene.iter())
        ball = any(yes(n.get('soccer_ball')) for n in scene.iter())
        flags = 'red-flag' in tags and 'blue-flag' in tags
        modes = []
        if linear: modes += ['normal', 'time_trial', 'follow_leader', 'lap_trial', 'ghost_geometry', 'grand_prix_geometry']
        if arena and navmesh: modes += ['three_strikes', 'free_for_all']
        if soccer and navmesh and goals >= 2 and ball: modes += ['soccer']
        if ctf and flags: modes += ['capture_the_flag']
        if egg_layout and linear: modes += ['egg_hunt']
        item = {'key': kind + '/' + asset_id, 'id': asset_id, 'name': root.get('name'), 'kind': kind,
                'source_url': metadata.get('file'), 'revision': metadata.get('revision'), 'rating': float(metadata.get('rating') or 0),
                'descriptor': str(descriptor), 'preview': str(preview), 'licenses': [str(p) for p in licenses], 'license_labels': labels,
                'bytes': sum(p.stat().st_size for p in files), 'modes': modes,
                'evidence': {'linear_graph_quads': linear, 'arena': arena, 'soccer': soccer, 'ctf': ctf, 'navmesh_file': navmesh,
                             'goal_count': goals, 'soccer_ball': ball, 'both_flag_nodes': flags, 'egg_layout': egg_layout},
                'runtime_verified': False, 'ghost_ready': False}
        all_items.append(item)
        for mode in modes: pools[mode].append(item)
for mode in ('normal', 'time_trial', 'follow_leader', 'lap_trial', 'ghost_geometry', 'grand_prix_geometry', 'three_strikes', 'free_for_all', 'soccer', 'capture_the_flag', 'egg_hunt'):
    pools[mode]  # Retain empty categories instead of silently excluding a mode.
for mode in pools:
    pools[mode].sort(key=lambda x: (-x['rating'], x['bytes'], x['id']))
# Draft allocation: five different maps per gameplay variant, with rare pools
# assigned first. This is a review proposal, not an approved campaign contract.
sample, selected_ids = {}, set()
for mode in sorted((m for m in pools if m != 'grand_prix_geometry'), key=lambda m: (len(pools[m]), m)):
    ordered = pools[mode]
    if mode == 'normal':
        ordered = sorted(ordered, key=lambda i: (i['id'] not in {'high-in-the-sky', 'ancient-summits'}, -i['rating']))
    selected = []
    for item in ordered:
        if item['key'] in selected_ids: continue
        if mode != 'normal' and item['id'] in {'high-in-the-sky', 'ancient-summits'}: continue
        selected.append(item); selected_ids.add(item['key'])
        if len(selected) == 5: break
    sample[mode] = selected
sample['grand_prix_geometry'] = sample.get('normal', [])
expanded = sorted(all_items, key=lambda x: (x['id'] not in {'high-in-the-sky', 'ancient-summits'}, -x['rating'], x['bytes'], x['key']))
supplement = []
for item in expanded:
    if len(selected_ids) >= 50: break
    if item['modes'] and item['key'] not in selected_ids:
        selected_ids.add(item['key']); supplement.append(item)
report = {'status': 'mode-specific user content candidates; no imports/runtime acceptance',
          'counts': {m: len(v) for m,v in pools.items()}, 'equal_review_sample_per_mode': 5,
          'mode_samples': sample, 'supplement_to_50_unique': supplement, 'unique_sample_maps': len(selected_ids),
          'allocation_note': 'Draft five distinct source maps per10gameplay variants; GP reuses normal sample as wrapper. Ghost remains geometry-only. Not approved/imported/runtime verified.',
          'limitations': ['ghost_geometry requires matching replay recording before ghost_ready', 'GP requires ordered stage definition',
                         'CTF scene flags do not prove offline campaign AI', 'navmesh/egg/goal presence does not prove playable placement',
                         'Mode samples overlap; final equal event quota and final unique map count are separate requirements'],
          'all_candidates': all_items}
out.mkdir(parents=True, exist_ok=True)
(out / 'user-mode-candidates.json').write_text(json.dumps(report, indent=2)+'\n')
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
preview_out = out / 'previews'
preview_out.mkdir(exist_ok=True)
for mode, items in sample.items():
    canvas = Image.new('RGB', (1400, 210), '#101d3b'); draw = ImageDraw.Draw(canvas)
    for i,item in enumerate(items):
        with Image.open(item['preview']) as image:
            thumb = ImageOps.contain(image.convert('RGB'), (264,150))
            canvas.paste(thumb, (i*280+(280-thumb.width)//2, 6))
        draw.text((i*280+8,160), item['name'][:32], fill='white', font=font)
        draw.text((i*280+8,180), item['key'][:36], fill='#70d9ff', font=font)
    canvas.save(preview_out / ('mode-'+mode+'.jpg'), quality=90)
overview_modes = [m for m in sample if m != 'grand_prix_geometry']
overview = Image.new('RGB', (1400, 240 * len(overview_modes)), '#101d3b')
overview_draw = ImageDraw.Draw(overview)
for row, mode in enumerate(overview_modes):
    overview_draw.text((10, row*240+4), mode + ' - candidate previews, not runtime acceptance', fill='white', font=font)
    with Image.open(preview_out / ('mode-'+mode+'.jpg')) as strip:
        overview.paste(strip, (0,row*240+28))
overview.save(preview_out / 'user-modes-overview.jpg', quality=90)
print(json.dumps({'counts': report['counts'], 'unique_sample_maps': len(selected_ids)}, indent=2))
lines = ['# User content for every original game mode', '',
         'Static candidates with retained source URLs/licenses/previews. No game import or runtime acceptance. Five review candidates per mode where available; the same geometry can support several modes and is counted once toward unique maps.', '',
         '| Mode | Static candidates | First five preview candidates |', '|---|---:|---|']
for mode, items in sample.items():
    lines.append('| '+mode+' | '+str(len(pools[mode]))+' | '+', '.join('`'+i['key']+'`' for i in items)+' |')
lines += ['', 'Unique maps in mode samples plus supplemental pool: '+str(len(selected_ids))+'.', '',
          'Ghost entries are geometry only: no matching replay has been validated. CTF requires runtime/network or offline design work. GP entries need stage definitions. Source approval does not establish publication rights. See JSON for exact structural evidence and source paths.', '',
          'Per-mode preview sheets: `previews/mode-<mode>.jpg`. Full candidate and supplemental mapping: `user-mode-candidates.json`.']
(out / 'user-mode-candidates.md').write_text('\n'.join(lines)+'\n')
