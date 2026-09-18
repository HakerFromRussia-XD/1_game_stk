#!/usr/bin/env python3
"""Build a review-only 50-track candidate catalog from existing local assets.

Does not import assets into the game. Existing previews retain source appearance.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageOps


def yes(value):
    return str(value).lower() in {'y', 'yes', 'true', '1'}


def license_info(files):
    found = [p for p in files if any(s in p.name.lower() for s in ('license', 'licence', 'copying'))]
    text = '\n'.join(p.read_text(errors='replace') for p in found)
    labels = []
    for label, pattern in [('CC-BY-SA', r'by-sa|attribution.share.?alike'), ('CC-BY', r'cc-by(?!-sa)|creativecommons.org/licenses/by/|attribution 4|attribution 3'),
                           ('CC0', r'cc0|public domain'), ('GPL', r'general public license|\bgpl\b'),
                           ('Free Art', r'free art|artlibre'), ('BSD', r'\bbsd\b')]:
        if re.search(pattern, text, re.I):
            labels.append(label)
    return found, labels or ['unclassified; inspect license file']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=Path('.codex-downloads/fluxara-addon-catalog'))
    parser.add_argument('--output', type=Path, default=Path('docs/fluxara-content'))
    args = parser.parse_args()
    source = args.catalog.resolve()
    out = args.output.resolve()
    previews = out / 'previews'
    previews.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for entry in ET.parse(source / 'online_assets.xml').getroot().findall('track'):
        key = entry.get('id')
        if key not in manifest or int(entry.get('revision', 0)) > int(manifest[key].get('revision', 0)):
            manifest[key] = entry.attrib
    counts = Counter()
    candidates = []
    rejected = []
    for folder in sorted((source / 'extracted/tracks').iterdir()):
        descriptor = folder / 'track.xml'
        if not descriptor.exists():
            continue
        try:
            root = ET.parse(descriptor).getroot()
        except ET.ParseError:
            rejected.append({'id': folder.name, 'reason': 'descriptor XML parse error'})
            continue
        kind = 'soccer' if yes(root.get('soccer')) else 'arena' if yes(root.get('arena')) else 'cutscene' if yes(root.get('cutscene')) else 'race'
        counts[kind] += 1
        preview = folder / root.get('screenshot', '')
        files = [p for p in folder.rglob('*') if p.is_file()]
        licenses, labels = license_info(files)
        metadata = manifest.get(folder.name, {})
        reasons = []
        if kind != 'race': reasons.append(kind)
        if root.get('version') not in {'6', '7'}: reasons.append('unsupported track version')
        if not all((folder / name).is_file() for name in ('graph.xml', 'quads.xml', 'scene.xml')): reasons.append('missing graph/quads/scene')
        if not preview.is_file(): reasons.append('missing declared preview')
        if not licenses: reasons.append('no retained license file')
        if not int(metadata.get('status', 0)) & 1: reasons.append('not approved in source addon manifest')
        if labels == ['unclassified; inspect license file']: reasons.append('license terms unclassified')
        for name in ('graph.xml', 'quads.xml', 'scene.xml'):
            if (folder / name).is_file():
                try:
                    ET.parse(folder / name)
                except ET.ParseError:
                    reasons.append(name + ' XML parse error')
        if reasons:
            rejected.append({'id': folder.name, 'reason': '; '.join(reasons)})
            continue
        candidates.append({'id': folder.name, 'name': root.get('name'), 'type': kind,
                           'descriptor': str(descriptor.relative_to(Path.cwd())), 'preview_source': str(preview.relative_to(Path.cwd())),
                           'preview_sha256': hashlib.sha256(preview.read_bytes()).hexdigest(),
                           'source_url': metadata.get('file'), 'author': metadata.get('designer'), 'revision': metadata.get('revision'),
                           'license_files': [str(p.relative_to(Path.cwd())) for p in licenses], 'license_labels': labels,
                           'version': int(root.get('version')), 'bytes': sum(p.stat().st_size for p in files),
                           'rating': float(metadata.get('rating') or 0), 'source_approved_flag': True,
                           'compatibility': 'format and required-file checks only; runtime, dependencies, visual approval pending'})
    # Prefer established smaller assets for a bounded mobile review queue. Keep the
    # already approved canyon and selected snow route first, without changing either.
    preferred = ['high-in-the-sky', 'ancient-summits']
    candidates.sort(key=lambda x: (0 if x['id'] in preferred else 1,
                                   preferred.index(x['id']) if x['id'] in preferred else 0,
                                   -x['rating'], x['bytes'], x['id']))
    selected = candidates[:50]
    for index, item in enumerate(selected, 1):
        item['campaign_slot'] = index
        item['current_runtime_id'] = {'high-in-the-sky': 'fluxara-canyon', 'ancient-summits': 'fluxara-summit-run'}.get(item['id'])
        # Approved canyon has new art: use its actual retained preview rather than
        # the original catalog image when available.
        if item['id'] == 'high-in-the-sky':
            approved = Path('iosApp/FluxaraResources/tracks/fluxara-canyon/track.xml')
            root = ET.parse(approved).getroot()
            image = approved.parent / root.get('screenshot')
            if image.is_file():
                item['preview_source'] = str(image)
                item['preview_sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
                item['preview_note'] = 'Package preview is still old High in the Sky artwork; must replace with approved canyon gameplay capture before campaign use.'
    result = {'status': 'review_candidates_not_imported', 'target_count': 50, 'selected_count': len(selected),
              'original_campaign_count': 21, 'original_count_gate': '50 >= 21 original unique campaign tracks. Reproduce with original_campaign_inventory.py; challenge files match archived original app.',
              'taxonomy_evidence': ['src/tracks/track.cpp:573-577', 'src/race/race_manager.hpp:114-121', 'src/addons/addon.hpp:43'],
              'mode_balance_pending': '25/25 withdrawn: two modes described only story challenges, not all original game modes. Full mode coverage requires linear/battle/soccer/CTF/egg content; see campaign-port-plan.md. This50list is a linear-source pool, not the final campaign.',
              'taxonomy': dict(counts), 'balance': 'All50entries form a LINEAR SOURCE POOL ONLY, not the final mode-balanced campaign. Include battle/soccer/CTF/egg-hunt in final selection; game modes outnumber story challenge modes.',
              'selection': 'Source manifest approved flag required (AddonStatus AS_APPROVED=1), license file with recognizable label, version6/7, graph/quads/scene parse. Existing canyon and summit first, then descending catalog rating, size as tie-breaker. Static candidate queue; not visual approval or rights clearance.',
              'candidates': selected, 'excluded': rejected}
    (out / 'campaign-50-candidates.json').write_text(json.dumps(result, indent=2) + '\n')
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
    for offset in range(0, len(selected), 25):
        canvas = Image.new('RGB', (1400, 1000), '#101d3b')
        draw = ImageDraw.Draw(canvas)
        for cell, item in enumerate(selected[offset:offset+25]):
            x, y = (cell % 5) * 280, (cell // 5) * 200
            with Image.open(item['preview_source']) as image:
                thumb = ImageOps.contain(image.convert('RGB'), (264, 150))
                canvas.paste(thumb, (x + (280-thumb.width)//2, y+5))
            draw.text((x+8, y+158), f"{item['campaign_slot']:02d}. {item['name']}"[:32], fill='white', font=font)
            draw.text((x+8, y+178), item['id'][:32], fill='#70d9ff', font=font)
        canvas.save(previews / f'campaign-50-{offset//25+1:02d}.jpg', quality=92)
    lines = ['# Campaign: 50 source-track candidates', '', result['balance'], '', result['selection'], '',
             '**Not imported; NOT FINAL CAMPAIGN.** Original STORY campaign has21unique tracks, while the game has more modes/arenas.25/25allocation is withdrawn; final mode-balanced selection is pending. Licenses are detected labels, not a publication rights conclusion.', '',
             '| # | Source ID | Name | Type | MiB | License labels |', '|---:|---|---|---|---:|---|']
    for item in selected:
        lines.append(f"| {item['campaign_slot']} | `{item['id']}` | {item['name']} | race | {item['bytes']/1048576:.1f} | {', '.join(item['license_labels'])} |")
    lines += ['', 'Exact source URLs, authors, revisions, license paths, preview paths and SHA-256 values are in campaign-50-candidates.json.', '',
              'Contact sheets: previews/campaign-50-01.jpg and previews/campaign-50-02.jpg. Thumbnails are source previews, not new screenshots or proof of mobile rendering.']
    (out / 'campaign-50-candidates.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'taxonomy': counts, 'eligible': len(candidates), 'selected': len(selected), 'output': str(out)}))


if __name__ == '__main__':
    main()
