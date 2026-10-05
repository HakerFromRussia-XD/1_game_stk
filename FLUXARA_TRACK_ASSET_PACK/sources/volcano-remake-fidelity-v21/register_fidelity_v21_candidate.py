from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil

r = Path(__file__).resolve().parent
w = r/'fidelity-v21'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
pack = repo/'FLUXARA_TRACK_ASSET_PACK'
sources = pack/'sources/volcano-remake-fidelity-v21'
sources.mkdir(exist_ok=True)
mod = pack/'models/volcano-remake-fidelity-v21'
canon = pack/'blender/FLUXARA_Track_Asset_Library.blend'
pf = repo/'FLUXARA_TRACK_ASSET_POOL.json'
a = json.loads((w/'asset-registration.json').read_text())
pool = json.loads(pf.read_text())
ledger = json.loads((r/'fidelity-v20/candidate-asset-ledger.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects'] == 1
assert json.loads((w/'final-blend-verification.json').read_text())['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV20'] == 605
assert (w/'canonical-bindings-verification.json').is_file()
run = json.loads((w/'runtime-validation.json').read_text())
assert run['visualInspectionCompleted'] and run['naturalFinishObserved'] and run['finalProbeTrackCleanupVerified']
if not (w/'pool-before-v21.json').exists():
    shutil.copy2(pf, w/'pool-before-v21.json')

def info(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

for f in list(r.glob('*fidelity_v21*.py'))+[r/'terrain_triangle_distance.py']:
    shutil.copy2(f, sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):
        shutil.copy2(f, sources/f.name)
for folder in ['candidate', 'native', 'screenshots', 'iterations']:
    shutil.copytree(w/folder, sources/folder, dirs_exist_ok=True)
for filename in ['original-central-object-before.spm', 'retained-central-stone-component.spm']:
    shutil.copy2(w/filename, sources/filename)
pres = json.loads((w/'preservation-verification.json').read_text())
proof = json.loads((w/'crest-changes.json').read_text())
original_textures=sources/'original-source-textures';original_textures.mkdir(exist_ok=True)
for name in pres['originalSourceTextureNames']:shutil.copy2(r/'before'/name,original_textures/name)
lib = Path(proof['newSharedCrestLibrary'])
shutil.copytree(lib, sources/'runtime-library'/lib.name, dirs_exist_ok=True)
base = {'sourceMap': 'fluxara-user-volcano-remake', 'categories': ['lava'],
        'uses': [{'trackId':'fluxara-user-volcano-remake','candidate':'V21','status':'Rounded central crest follows the original rim, exact original collision and central object bounds retained. Existing stone and green pixels reused. Isolated candidate, not integrated.'}]}
new = []
for q in a['newPrototypes']:
    dd = [next(m['id'] for m in ledger['materials'] if m.get('name', m.get('displayName')) == n) for n in q['materials']] + [q['sourcePoolObjectId']]
    new.append({**base, **q, 'displayName':q['name'], 'kind':'visual-object', 'reuseTier':'adapt',
                'canonicalPackPath':str(canon)+'#Object/'+q['name'], 'physicalSourcePath':a['visualLibrary'],
                'file':info(Path(a['visualLibrary'])), 'dependencies':dd, 'reason':q['role'],
                'wholeCentralCliffObjectBoundsOriginAxesPreserved':True})
    source = Path(q['sourceModel'])
    stored = mod/source.name
    assert stored.read_bytes() == source.read_bytes()
    new.append({**base,'id':'volcano-fidelity-v21-runtime-rounded-central-crest','displayName':source.name,
                'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),
                'physicalSourcePath':str(source),'file':info(stored),'dependencies':[q['id']],
                'productionIntegrated':False,'reason':'Single ghost central crest model placed once at original world axes. Original eight collision faces retained separately in map; original stone side unchanged.'})
stored = mod/'volcano_track.spm'
assert stored.read_bytes() == (w/'candidate/volcano_track.spm').read_bytes()
new.append({**base,'id':'volcano-fidelity-v21-runtime-volcano-track','displayName':'Volcano track V21 with separate decorative central crest',
            'kind':'map-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),
            'physicalSourcePath':str(w/'candidate/volcano_track.spm'),'file':info(stored),
            'dependencies':['volcano-fidelity-v20-runtime-volcano-track','volcano-fidelity-v17-centralgreencrest'],
            'productionIntegrated':False,'reason':'Map-specific geometry: protected road and stone indexed attributes unchanged. Eight central crest faces removed only after retaining all source collision attributes in a dedicated exact mesh. Not a generic scenery pool object.'})
assert len(new) == 3
for data in [pool, ledger]:
    data['objects'] = [q for q in data['objects'] if not q['id'].startswith('volcano-fidelity-v21-')] + new
ci = info(canon)

def refresh(v):
    if isinstance(v, dict):
        if v.get('path') == str(canon) and 'sha256' in v:
            v.update(ci)
        for x in v.values(): refresh(x)
    elif isinstance(v, list):
        for x in v: refresh(x)

refresh(pool); refresh(ledger)
pool['physicalPack']['blenderLibrary'] = ci
pool['updated'] = datetime.now(timezone.utc).isoformat()
pool['assets'] = pool['objects'] + pool['materials'] + pool['textures']
ids = [q['id'] for q in pool['assets']]
assert len(ids) == len(set(ids))
ledger.update({'candidate':'V21 rounded central crest with retained stone texture', 'status':a['status'],
               'finalBlend':a['finalBlend'], 'nativeSharedParts':len(a['nativeSharedInstances']),
               'preservation':pres,'budget':pres,'runtimeValidation':run,
               'deltaAssetCounts':{'objects':3,'materials':0,'textures':0},
               'productionIntegrated':False,'newImagePixels':False,
               'protectedCentralCrestCollisionModel':info(mod/proof['sourceColliderModel'])})
ledger['assets'] = ledger['objects'] + ledger['materials'] + ledger['textures']
ledger['mapRuntimeFiles'] = [info(q) for q in (sources/'candidate').iterdir() if q.is_file()]
for q in ledger['assets']:
    assert q['id'] in ids
    assert Path(q['canonicalPackPath'].split('#')[0]).is_file(), q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists(), q['id']
    assert all(dep in ids for dep in q.get('dependencies', [])), q['id']
    if q.get('file'): assert info(Path(q['file']['path'])) == q['file'], q['id']
audit = {'newObjects':3,'newNativePrototypes':1,'newMaterials':0,'newTextures':0,'newImagePixels':False,
         'replacementMapModels':1,'newSharedCrestModels':1,'preservedPhysicsOnlyModels':1,'newRuntimeTextureFiles':0,
         'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),
         'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],
         'canonical':ci,'productionIntegrated':False,'nativeSharedParts':333,
         'otherV20MeshesUnchanged':True,'retainedCentralNativeFaceAttributesExact':True}
pf.write_text(json.dumps(pool, ensure_ascii=False, indent=2)+'\n')
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n')
(w/'pool-audit.json').write_text(json.dumps(audit, indent=2))
for name in ['candidate-asset-ledger.json', 'pool-audit.json']: shutil.copy2(w/name, sources/name)
print('V21_ROUNDED_CENTRAL_CREST_REGISTERED', audit, flush=True)
