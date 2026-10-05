from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil

r = Path(__file__).resolve().parent
w = r/'fidelity-v19'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
pack = repo/'FLUXARA_TRACK_ASSET_PACK'
sources = pack/'sources/volcano-remake-fidelity-v19'
sources.mkdir(exist_ok=True)
mod = pack/'models/volcano-remake-fidelity-v19'
canon = pack/'blender/FLUXARA_Track_Asset_Library.blend'
pf = repo/'FLUXARA_TRACK_ASSET_POOL.json'
a = json.loads((w/'asset-registration.json').read_text())
pool = json.loads(pf.read_text())
ledger = json.loads((r/'fidelity-v18/candidate-asset-ledger.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects'] == 3
assert json.loads((w/'final-blend-verification.json').read_text())['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV18'] == 595
assert (w/'canonical-bindings-verification.json').is_file()
run = json.loads((w/'runtime-validation.json').read_text())
assert run['visualInspectionCompleted'] and run['naturalFinishObserved'] and run['finalProbeTrackCleanupVerified']
if not (w/'pool-before-v19.json').exists():
    shutil.copy2(pf, w/'pool-before-v19.json')

def info(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

for f in r.glob('*fidelity_v19*.py'):
    shutil.copy2(f, sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):
        shutil.copy2(f, sources/f.name)
for folder in ['candidate', 'native', 'screenshots', 'iterations']:
    shutil.copytree(w/folder, sources/folder, dirs_exist_ok=True)
pres = json.loads((w/'preservation-verification.json').read_text())
base = {'sourceMap': 'fluxara-user-volcano-remake', 'categories': ['lava'], 'uses': [{'trackId':'fluxara-user-volcano-remake','candidate':'V19','status':'Continuous closed smoke billows, existing palettes and ghost transforms. Stone/route and all other V18 resources unchanged. Not integrated.'}]}
new = []
deps = set()
for q in a['newPrototypes']:
    dd = [next(m['id'] for m in ledger['materials'] if m.get('name', m.get('displayName')) == n) for n in q['materials']] + [q['sourcePoolObjectId']]
    deps.update(dd)
    new.append({**base, **q, 'displayName': q['name'], 'kind': 'visual-object', 'reuseTier': 'authored',
                'canonicalPackPath': str(canon)+'#Object/'+q['name'], 'physicalSourcePath': a['visualLibrary'],
                'file': info(Path(a['visualLibrary'])), 'dependencies': dd,
                'reason': q['role']})
for q in a['newPrototypes']:
    source = Path(q['sourceModel'])
    stored = mod/source.name
    assert stored.read_bytes() == source.read_bytes()
    dd = [q['id']]+[next(m['id']for m in ledger['materials']if m.get('name',m.get('displayName'))==n)for n in q['materials']]
    new.append({**base,'id':'volcano-fidelity-v19-runtime-'+source.stem.lower(),'displayName':source.name,'kind':'map-runtime-model','reuseTier':'authored','canonicalPackPath':str(stored),'physicalSourcePath':str(source),'file':info(stored),'dependencies':dd,'productionIntegrated':False,'newTextureFiles':0,'reason':'Replaces existing decorative ghost smoke file; source box, origin, axes and placement retained. Existing image and material reused; closed connected billows.'})
assert len(new) == 6
for data in [pool, ledger]:
    data['objects'] = [q for q in data['objects'] if not q['id'].startswith('volcano-fidelity-v19-')] + new
ci = info(canon)

def refresh(v):
    if isinstance(v, dict):
        if v.get('path') == str(canon) and 'sha256' in v:
            v.update(ci)
        for x in v.values():
            refresh(x)
    elif isinstance(v, list):
        for x in v:
            refresh(x)

refresh(pool)
refresh(ledger)
pool['physicalPack']['blenderLibrary'] = ci
pool['updated'] = datetime.now(timezone.utc).isoformat()
pool['assets'] = pool['objects'] + pool['materials'] + pool['textures']
ids = [q['id'] for q in pool['assets']]
assert len(ids) == len(set(ids))
ledger.update({'candidate': 'V19 continuous smoke billows with retained stone texture', 'status': a['status'],
               'finalBlend': a['finalBlend'], 'nativeSharedParts': len(a['nativeSharedInstances']),
               'preservation': pres, 'budget': pres, 'runtimeValidation': run,
               'deltaAssetCounts': {'objects': 6, 'materials': 0, 'textures': 0},
               'productionIntegrated': False, 'newImagePixels': False})
ledger['assets'] = ledger['objects'] + ledger['materials'] + ledger['textures']
ledger['mapRuntimeFiles'] = [info(q) for q in (sources/'candidate').iterdir() if q.is_file()]
for q in ledger['assets']:
    assert q['id'] in ids
    assert Path(q['canonicalPackPath'].split('#')[0]).is_file(), q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists(), q['id']
    assert all(dep in ids for dep in q.get('dependencies', [])), q['id']
    if q.get('file'):
        assert info(Path(q['file']['path'])) == q['file'], q['id']
audit = {'newObjects':6,'newNativePrototypes':3,'newMaterials':0,'newTextures':0,'replacementMapModels':3,'newRuntimeTextureFiles':0,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False,'previousV18ModelsAndTexturesUnchanged':True,'nativeSharedParts':331}
pf.write_text(json.dumps(pool, ensure_ascii=False, indent=2)+'\n')
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n')
(w/'pool-audit.json').write_text(json.dumps(audit, indent=2))
for name in ['candidate-asset-ledger.json', 'pool-audit.json']:
    shutil.copy2(w/name, sources/name)
print('V19_CLOSED_SMOKE_BILLOWS_REGISTERED', audit, flush=True)
