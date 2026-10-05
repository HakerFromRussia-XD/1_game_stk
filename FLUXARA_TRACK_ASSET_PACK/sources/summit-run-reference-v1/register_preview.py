from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
name='screenshot.png';p=pack/'textures/summit-run-reference-v1'/name
raw=pack/'sources/summit-run-reference-v1/screenshots/preview-ice.png'
raw.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/'screenshots/preview-ice.png',raw)
a=json.loads((r/'asset-registration.json').read_text())
a['textures'][name]={'source':str(raw),'packPath':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(r/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('PREVIEW_SOURCE_REGISTERED')
