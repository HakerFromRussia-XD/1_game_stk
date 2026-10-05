from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent;p=Path('/Users/motoricallc/Downloads/fluxara-drift');pool=json.load(open(p/'FLUXARA_TRACK_ASSET_POOL.json'));ledger=json.load(open(r.parent.parent/'fluxara-user-motorsport-land.asset-ledger.json'));index={a['id']:a for k in ['objects','materials','textures'] for a in pool[k]};sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for a in ledger['assets']:
 assert a['id'] in index;f=Path(a['canonicalPackPath'].split('#')[0]);assert f.is_file()
 if a.get('file'):
  f=Path(a['file']['path']);assert f.stat().st_size==a['file']['bytes'] and sha(f)==a['file']['sha256'],a['id']
 assert all(n in index for n in a.get('dependencies',[])),a['id']
f=r.parent/'fluxara-user-motorsport-land-final';manifest=lambda root:{q.name:sha(q) for q in root.iterdir() if q.is_file() and q.suffix!='.blend'};assert manifest(f)==manifest(r/'candidate');result={'physicalPackUsedAssetsVerified':len(ledger['assets']),'finalRuntimeManifestExact':True,'oneFinalBlend':len(list(f.glob('*.blend')))==1,'blender':json.loads((r/'final-blend-verification.json').read_text()),'live':json.loads((r/'live-verification.json').read_text()),'preservation':json.loads((r/'preservation-audit.json').read_text())};(r/'delivery-verification.json').write_text(json.dumps(result,indent=2));print('DELIVERY_VERIFIED',len(ledger['assets']))
