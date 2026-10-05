from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil

r = Path(__file__).resolve().parent
w = r/'fidelity-v18'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
pack = repo/'FLUXARA_TRACK_ASSET_PACK'
sources = pack/'sources/volcano-remake-fidelity-v18'
sources.mkdir(exist_ok=True)
mod = pack/'models/volcano-remake-fidelity-v18'
canon = pack/'blender/FLUXARA_Track_Asset_Library.blend'
pf = repo/'FLUXARA_TRACK_ASSET_POOL.json'
a = json.loads((w/'asset-registration.json').read_text())
pool = json.loads(pf.read_text())
ledger = json.loads((r/'fidelity-v17/candidate-asset-ledger.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects'] == 1
assert json.loads((w/'final-blend-verification.json').read_text())['allPriorNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV17'] == 571
assert (w/'canonical-bindings-verification.json').is_file()
run = json.loads((w/'runtime-validation.json').read_text())
assert run['visualInspectionCompleted'] and run['naturalFinishObserved'] and run['finalProbeTrackCleanupVerified']
if not (w/'pool-before-v18.json').exists():
    shutil.copy2(pf, w/'pool-before-v18.json')

def info(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

for f in r.glob('*fidelity_v18*.py'):
    shutil.copy2(f, sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):
        shutil.copy2(f, sources/f.name)
for folder in ['candidate', 'native', 'screenshots', 'iterations']:
    shutil.copytree(w/folder, sources/folder, dirs_exist_ok=True)
pres = json.loads((w/'preservation-verification.json').read_text())
runtime_lib = Path(pres['adaptedLibrary'])
shutil.copytree(runtime_lib, sources/'runtime-library'/runtime_lib.name, dirs_exist_ok=True)
base = {'sourceMap': 'fluxara-user-volcano-remake', 'categories': ['grass', 'rock', 'lava'],
        'uses': [{'trackId': 'fluxara-user-volcano-remake', 'candidate': 'V18',
                  'status': '32 decorative coordinates, copied pooled hill geometry and vertex-green palette. Original donor and existing stone pixels/UVs unchanged. Not integrated.'}]}
new = []
deps = set()
for q in a['newPrototypes']:
    dd = [next(m['id'] for m in ledger['materials'] if m.get('name', m.get('displayName')) == n) for n in q['materials']] + [q['sourcePoolObjectId']]
    deps.update(dd)
    new.append({**base, **q, 'displayName': q['name'], 'kind': 'visual-object', 'reuseTier': 'adapt',
                'canonicalPackPath': str(canon)+'#Object/'+q['name'], 'physicalSourcePath': a['visualLibrary'],
                'file': info(Path(a['visualLibrary'])), 'dependencies': dd,
                'reason': 'Copied source positions, indices, normals, bounds and origin retained. UVs removed only in copied model; RGB derived from existing green palette. Donor model/texture unchanged.'})
stored = mod/'vr_v18_green_mound.spm'
source = Path(pres['adaptedModel'])
shutil.copy2(source, stored)
new.append({**base, 'id': 'volcano-fidelity-v18-runtime-green-mound', 'displayName': stored.name,
            'kind': 'shared-runtime-model', 'reuseTier': 'adapt', 'canonicalPackPath': str(stored),
            'physicalSourcePath': str(source), 'file': info(stored), 'dependencies': sorted(deps),
            'runtimePackagedPath': str(source), 'productionIntegrated': False,
            'newTextureFiles': 0, 'reason': 'One shared 360-triangle model for 32 coordinates. Existing vertex-color material reused. No protected course geometry or collision mesh changed.'})
assert len(new) == 2
for data in [pool, ledger]:
    data['objects'] = [q for q in data['objects'] if not q['id'].startswith('volcano-fidelity-v18-')] + new
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
ledger.update({'candidate': 'V18 additional green mounds with retained stone texture', 'status': a['status'],
               'finalBlend': a['finalBlend'], 'nativeSharedParts': len(a['nativeSharedInstances']),
               'preservation': pres, 'budget': pres, 'runtimeValidation': run,
               'deltaAssetCounts': {'objects': 2, 'materials': 0, 'textures': 0},
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
assert info(Path(pres['sourceModel']))['sha256'] == pres['sourceModelSha256']
audit = {'newObjects': 2, 'newNativePrototypes': 1, 'newMaterials': 0, 'newTextures': 0,
         'newRuntimeModels': 1, 'newRuntimeTextures': 0,
         'allPhysicalPathsAndFileHashesMatch': True, 'uniquePoolIds': len(ids),
         'totalLedgerAssetsIncludingHistoricalSources': len(ledger['assets']),
         'unresolvedDependencies': [], 'canonical': ci, 'productionIntegrated': False,
         'sourceDonorModelUnchanged': True, 'sharedCoordinatePlacements': 32}
pf.write_text(json.dumps(pool, ensure_ascii=False, indent=2)+'\n')
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n')
(w/'pool-audit.json').write_text(json.dumps(audit, indent=2))
for name in ['candidate-asset-ledger.json', 'pool-audit.json']:
    shutil.copy2(w/name, sources/name)
print('V18_SHARED_GREEN_MOUND_REGISTERED', audit, flush=True)
