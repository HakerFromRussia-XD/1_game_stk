from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil

r = Path(__file__).resolve().parent
w = r/'fidelity-v22'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
pack = repo/'FLUXARA_TRACK_ASSET_PACK'
sources = pack/'sources/volcano-remake-fidelity-v22'
sources.mkdir(exist_ok=True)
mod = pack/'models/volcano-remake-fidelity-v22'
canon = pack/'blender/FLUXARA_Track_Asset_Library.blend'
pf = repo/'FLUXARA_TRACK_ASSET_POOL.json'
a = json.loads((w/'asset-registration.json').read_text())
pool = json.loads(pf.read_text())
ledger = json.loads((r/'fidelity-v21/candidate-asset-ledger.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects'] == 2
assert json.loads((w/'final-blend-verification.json').read_text())['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV21'] == 493
assert (w/'canonical-bindings-verification.json').is_file()
run = json.loads((w/'runtime-validation.json').read_text())
assert run['visualInspectionCompleted'] and run['naturalFinishObserved'] and run['finalProbeTrackCleanupVerified']
if not (w/'pool-before-v22.json').exists():
    shutil.copy2(pf, w/'pool-before-v22.json')

def info(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

for f in r.glob('*fidelity_v22*.py'):
    shutil.copy2(f, sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):
        shutil.copy2(f, sources/f.name)
for folder in ['candidate', 'native', 'screenshots', 'iterations']:
    shutil.copytree(w/folder, sources/folder, dirs_exist_ok=True)
pres = json.loads((w/'preservation-verification.json').read_text())
proof=json.loads((w/'cliff-changes.json').read_text());shutil.copytree(Path(proof['newSharedCliffLibrary']),sources/'runtime-library',dirs_exist_ok=True)
shutil.copytree(r/'ai-v1-comparison',sources/'ai-v1-comparison',dirs_exist_ok=True)
shutil.copy2(r/'capture_ai_v1_comparison.py',sources/'capture_ai_v1_comparison.py')
shutil.copy2(r/'terrain_triangle_distance.py',sources/'terrain_triangle_distance.py')
base = {'sourceMap': 'fluxara-user-volcano-remake', 'categories': ['lava'], 'uses': [{'trackId':'fluxara-user-volcano-remake','candidate':'V22','status':'Organic grass/stone cliff copy for 58 wider and shorter newly added ghost instances; source local bounds/axes/origin retained. All V21 model/texture/control/physics files unchanged; scene.xml changes only these 58 decorations. Existing grass colors and stone pixels/UVs reused. Not integrated.'}]}
new = []
deps = set()
for q in a['newPrototypes']:
    dd = [next(m['id'] for m in ledger['materials'] if m.get('name', m.get('displayName')) == n) for n in q['materials']] + [q['sourcePoolObjectId']]
    deps.update(dd)
    new.append({**base, **q, 'displayName': q['name'], 'kind': 'visual-object', 'reuseTier': 'adapt',
                'canonicalPackPath': str(canon)+'#Object/'+q['name'], 'physicalSourcePath': a['visualLibrary'],
                'file': info(Path(a['visualLibrary'])), 'dependencies': dd,
                'reason': q['role']})
source=Path(a['newPrototypes'][0]['sourceModel']);stored=mod/source.name;assert stored.read_bytes()==source.read_bytes()
new.append({**base,'id':'volcano-fidelity-v22-runtime-organic-cliff','displayName':source.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(source),'file':info(stored),'dependencies':[q['id']for q in a['newPrototypes']],'productionIntegrated':False,'newTextureFiles':0,'reason':'One shared two-buffer cliff model for all 58 library placements. Existing source V16 model remains unchanged. New shape keeps whole original model bounds; new instance scale changes recorded separately.'})
assert len(new)==3
for data in [pool, ledger]:
    data['objects'] = [q for q in data['objects'] if not q['id'].startswith('volcano-fidelity-v22-')] + new
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
ledger.update({'candidate': 'V22 organic cliffs with retained stone texture', 'status': a['status'],
               'finalBlend': a['finalBlend'], 'nativeSharedParts': len(a['nativeSharedInstances']),
               'preservation': pres, 'budget': pres, 'runtimeValidation': run,
               'deltaAssetCounts': {'objects': 3, 'materials': 0, 'textures': 0},
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
audit = {'newObjects':3,'newNativePrototypes':2,'newMaterials':0,'newTextures':0,'replacementMapModels':0,'newSharedCliffModels':1,'newRuntimeTextureFiles':0,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False,'previousV21ModelsAndTexturesUnchanged':True,'nativeSharedParts':333}
pf.write_text(json.dumps(pool, ensure_ascii=False, indent=2)+'\n')
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n')
(w/'pool-audit.json').write_text(json.dumps(audit, indent=2))
for name in ['candidate-asset-ledger.json', 'pool-audit.json']:
    shutil.copy2(w/name, sources/name)
print('V22_ORGANIC_SHARED_CLIFFS_REGISTERED', audit, flush=True)
