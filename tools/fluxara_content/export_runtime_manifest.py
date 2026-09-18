#!/usr/bin/env python3
"""Export the small runtime contract from the audited import roster."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

roster = json.loads(Path('docs/fluxara-content/runtime-roster-v1.json').read_text())
root = ET.Element('campaign', {'version': '1', 'id': 'fluxara-main'})
for item in roster['entries']:
    attrs = {'id': item['event_id'], 'mode': item['mode'], 'track': item['runtime_track_id']}
    if item['mode'] == 'ghost_geometry': attrs['requires-replay'] = 'true'
    if item['mode'] == 'capture_the_flag': attrs['requires-offline-ctf'] = 'true'
    ET.SubElement(root, 'event', attrs)
ET.indent(root, space='  ')
ET.ElementTree(root).write('iosApp/FluxaraResources/fluxara-campaign.xml', encoding='utf-8', xml_declaration=True)
print('Exported', len(root), 'events')
