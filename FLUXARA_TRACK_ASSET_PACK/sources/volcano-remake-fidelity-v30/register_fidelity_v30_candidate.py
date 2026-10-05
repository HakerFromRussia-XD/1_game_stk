from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v30';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v30';sources.mkdir(exist_ok=True)
pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v29/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());p=json.loads((w/'facade-placements.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());native=json.loads((w/'final-blend-verification.json').read_text())
assert run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']and native['allOtherNativeMeshesAndMatricesExactV29']==626
assert 'V30_CANONICAL_DIRECT_TREE_AND_ALL_PREVIOUS_BINDINGS_VERIFIED'in(w/'canonical-verification.log').read_text()
if not(w/'pool-before-v30.json').exists():shutil.copy2(pf,w/'pool-before-v30.json')
def info(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):shutil.copy2(f,sources/f.name)
for f in r.glob('*fidelity_v30*.py'):shutil.copy2(f,sources/f.name)
shutil.copy2(r/'terrain_triangle_distance.py',sources/'terrain_triangle_distance.py')
index={q['id']:q for key in ['objects','materials','textures']for q in pool[key]};usage={'trackId':'fluxara-user-volcano-remake','candidate':'V30','instances':len(p['placements']),'status':'Directly reused in temporary runtime-validated candidate; source native and game files unchanged. Production integration/final/reference match unfinished.'}
add={a['reusedPrototypes'][0]['id']};todo=list(add)
while todo:
    current=todo.pop()
    for dep in index[current].get('dependencies',[]):
        if dep not in add:add.add(dep);todo.append(dep)
used=add|{'volcano-fidelity-v29-grounded-stonebody','volcano-fidelity-v22-grasslip'}
for key in ['objects','materials','textures']:
    existing={q['id']for q in ledger[key]}
    for q in pool[key]:
        if q['id']in used:
            q.setdefault('uses',[]);q['uses']=[x for x in q['uses']if x.get('trackId')!=usage['trackId']or x.get('candidate')!='V30']+[usage]
        if q['id']in add and q['id']not in existing:ledger[key].append(copy.deepcopy(q))
    for q in ledger[key]:
        if q['id']in used:q['uses']=copy.deepcopy(index[q['id']]['uses'])
pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures'];ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4148
ledger.update({'candidate':'V30 large coordinate cliff facades and direct pooled leaf trees','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':len(a['nativeSharedInstances']),'preservation':budget,'budget':budget,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjects':0,'newPoolMaterials':0,'newPoolTextures':0,'reusedTreeObjects':1,'reusedTreeMaterials':2,'reusedTreeTextures':2,'newAuthoredGeometry':0},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(sources/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
    assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
    if q.get('physicalSourcePath'):assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
    assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
    for field in ['runtimeLibraryFiles','runtimeFiles']:
        for f in q.get(field,[]):assert info(f['path'])==f,q['id']
ci=info(pack/'blender/FLUXARA_Track_Asset_Library.blend');assert ci==pool['physicalPack']['blenderLibrary']==json.loads((r/'fidelity-v29/pool-audit.json').read_text())['canonical']
audit={'newPoolAssets':0,'directReusedTreeAssetClosure':sorted(add),'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'canonicalUnmodifiedV29':True,'nativeSharedParts':len(a['nativeSharedInstances']),'newCoordinateParts':len(p['placements'])*3,'allOtherNativeMeshesAndMatricesExactV29':626,'newGameAssetPayloadBytes':0,'newModels':0,'newTextures':0,'newAuthoredMaterials':0,'productionIntegrated':False,'referenceAcceptance':False}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V30_DIRECT_POOLED_FACADES_AND_TREES_REGISTERED',audit,flush=True)
