#!/usr/bin/env python3
"""Download the previously omitted arena manifest category; retain source reports."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

catalog = Path(__file__).resolve().parents[2] / '.codex-downloads/fluxara-addon-catalog'
spec = importlib.util.spec_from_file_location('catalog_download', catalog / 'download_addons.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
latest = {}
for node in ET.parse(catalog / 'online_assets.xml').getroot().findall('arena'):
    if node.get('id') not in latest or int(node.get('revision', 0)) > int(latest[node.get('id')].get('revision', 0)):
        latest[node.get('id')] = node
items = [{'type': 'arena', 'id': n.get('id'), 'name': n.get('name'), 'url': n.get('file'),
          'revision': int(n.get('revision', 0)), 'bytes': int(n.get('size', 0))} for n in latest.values()]
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(module.download, items):
        if result['result'] != 'failed':
            destination = catalog / 'extracted/arenas' / result['id']
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(result['path']) as archive:
                for entry in archive.infolist():
                    target = (destination / entry.filename).resolve()
                    if destination.resolve() not in target.parents:
                        raise ValueError('Unsafe archive path: ' + entry.filename)
                archive.extractall(destination)
            result['extracted'] = str(destination)
        results.append(result)
        print(f"{len(results)}/{len(items)} {result['id']}: {result['result']}", flush=True)
        (catalog / 'arena-download-report.json').write_text(json.dumps({'results': results}, indent=2))
raise SystemExit(1 if any(x['result'] == 'failed' for x in results) else 0)
