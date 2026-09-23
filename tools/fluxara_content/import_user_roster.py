#!/usr/bin/env python3
"""Import the reviewed mode roster without changing geometry or driving data.

Only new track.xml group attributes are normalized. Existing Canyon/Summit are
never written. Every copied source file except track.xml is SHA-256 verified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from inventory import inspect


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--audit-only', action='store_true', help='Refresh manifest for existing imports without repeating copy/hash verification')
    parser.add_argument('--roster', type=Path, default=Path('docs/fluxara-content/user-mode-candidates.json'))
    parser.add_argument('--shared', type=Path, default=Path('../fluxara_drift-assets'))
    args = parser.parse_args()
    roster = json.loads(args.roster.read_text())
    destination = Path('iosApp/FluxaraResources/tracks')
    pins = {'high-in-the-sky': 'fluxara-canyon', 'ancient-summits': 'fluxara-summit-run'}
    engine_modes = {'normal': 'MINOR_MODE_NORMAL_RACE', 'time_trial': 'MINOR_MODE_TIME_TRIAL',
                    'ghost_geometry': 'MINOR_MODE_TIME_TRIAL', 'follow_leader': 'MINOR_MODE_FOLLOW_LEADER',
                    'lap_trial': 'MINOR_MODE_LAP_TRIAL', 'three_strikes': 'MINOR_MODE_3_STRIKES',
                    'free_for_all': 'MINOR_MODE_FREE_FOR_ALL', 'soccer': 'MINOR_MODE_SOCCER',
                    'capture_the_flag': 'MINOR_MODE_CAPTURE_THE_FLAG', 'egg_hunt': 'MINOR_MODE_EASTER_EGG'}
    items, seen = [], set()
    source_baseline = {p.name.lower() for name in ('textures', 'models', 'music', 'sfx', 'library', 'particles')
                       for p in (args.shared / name).rglob('*') if p.is_file()}
    library_root = args.shared / 'library'
    for mode, selected in roster['mode_samples'].items():
        if mode == 'grand_prix_geometry':
            continue
        for item in selected:
            if item['id'] in seen:
                raise ValueError('Duplicate selected source ID: ' + item['id'])
            seen.add(item['id'])
            source = Path(item['descriptor']).parent
            runtime_id = pins.get(item['id'], 'fluxara-user-' + item['id'])
            target = destination / runtime_id
            if item['id'] not in pins and args.apply and not args.audit_only:
                if target.exists():
                    # A repeat must not overwrite unknown/user-edited content.
                    for file in source.rglob('*'):
                        if file.is_file() and file.name != 'track.xml':
                            existing = target / file.relative_to(source)
                            if not existing.is_file() or digest(file) != digest(existing):
                                raise ValueError('Existing content differs: ' + str(existing))
                else:
                    shutil.copytree(source, target)
                    xml = ET.parse(target / 'track.xml')
                    xml.getroot().set('groups', 'Fluxara')
                    xml.write(target / 'track.xml', encoding='utf-8', xml_declaration=True)
                for file in source.rglob('*'):
                    if file.is_file() and file.name != 'track.xml':
                        assert digest(file) == digest(target / file.relative_to(source)), str(file)
            active = target if target.exists() else source
            audit = inspect(active, source_baseline)
            library_refs = set()
            for file in active.rglob('*.xml'):
                try:
                    node = ET.parse(file).getroot()
                except ET.ParseError:
                    continue
                for child in node.iter('library'):
                    if child.get('name'):
                        library_refs.add(child.get('name'))
            missing_libraries = [name for name in sorted(library_refs) if not (library_root / name).is_dir() and not (active / 'library' / name).is_dir()]
            items.append({'event_id': 'main-' + mode + '-' + item['id'], 'mode': mode, 'source_id': item['id'],
                          'runtime_track_id': runtime_id, 'engine_minor_mode': engine_modes[mode], 'source': str(source), 'destination': str(target),
                          'name': item['name'], 'source_url': item['source_url'], 'revision': item['revision'],
                          'license_files': audit['licenses'], 'bytes': audit['bytes'], 'file_count': audit['files'],
                          'preserved_approved_asset': item['id'] in pins,
                          'geometry_ai_checkpoint_physics_files': 'existing approved package untouched' if item['id'] in pins else 'all source files except track.xml byte-verified',
                          'imported': target.exists(), 'audit': audit, 'library_refs': sorted(library_refs),
                          'missing_libraries': missing_libraries, 'runtime_verified': False,
                          'limitations': ['matching replay required'] if mode == 'ghost_geometry' else ['offline campaign AI not established'] if mode == 'capture_the_flag' else []})
    report = {'schema_version': 1, 'campaign_id': 'fluxara-main', 'status': 'imported_static_only' if args.apply else 'dry_run',
              'selected_count': len(items), 'shared_asset_baseline': str(args.shared), 'source_roster': str(args.roster),
              'extra_existing_tracks_not_in_roster': sorted(p.name for p in destination.iterdir() if p.is_dir() and p.name not in {x['runtime_track_id'] for x in items}),
              'total_bytes': sum(x['bytes'] for x in items), 'entries': items,
              'notes': ['Ghost and CTF limitations are not resolved by importing assets.', 'GP is a wrapper and requires a separate stage definition.',
                        'No runtime, visual, AI or rights acceptance follows from this static report.']}
    if args.apply:
        Path('docs/fluxara-content/runtime-roster-v1.json').write_text(json.dumps(report, indent=2)+'\n')
        campaign = ET.Element('campaign', {'version': '1', 'id': 'fluxara-main'})
        for item in items:
            attributes = {'id': item['event_id'], 'mode': item['mode'], 'track': item['runtime_track_id']}
            if item['mode'] == 'ghost_geometry': attributes['requires-replay'] = 'true'
            if item['mode'] == 'capture_the_flag': attributes['requires-offline-ctf'] = 'true'
            ET.SubElement(campaign, 'event', attributes)
        ET.indent(campaign, space='  ')
        ET.ElementTree(campaign).write('iosApp/FluxaraResources/fluxara-campaign.xml', encoding='utf-8', xml_declaration=True)
    print(json.dumps({'count': len(items), 'total_bytes': report['total_bytes'], 'extra_existing': report['extra_existing_tracks_not_in_roster'],
                      'missing': [{'id': i['runtime_track_id'], 'xml': i['audit']['unresolved_xml_references'],
                                   'spm': i['audit']['unresolved_spm_textures'], 'libraries': i['missing_libraries']}
                                  for i in items if i['audit']['unresolved_xml_references'] or i['audit']['unresolved_spm_textures'] or i['missing_libraries']]}, indent=2))


if __name__ == '__main__':
    main()
