from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v28';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK'
sources=pack/'sources/volcano-remake-fidelity-v28';sources.mkdir(exist_ok=True);canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v24/candidate-asset-ledger.json').read_text());a26=json.loads((r/'fidelity-v26/asset-registration.json').read_text());a=json.loads((w/'asset-registration.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());parts=json.loads((r/'fidelity-v27/column-changes.json').read_text())['parts']
assert run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']
assert json.loads((w/'final-blend-verification.json').read_text())['allNativeMeshGeometryUVsNormalsColorsAndMaterialsExactV26']==625
assert 'V26_CANONICAL_ROUNDED_CENTRAL_STONE_BINDINGS_VERIFIED'in(r/'fidelity-v26/canonical-verification.log').read_text()
assert json.loads((r/'fidelity-v26/canonical-registration.json').read_text())['newObjects']==1
if not(w/'pool-before-v28.json').exists():shutil.copy2(pf,w/'pool-before-v28.json')
def info(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ['fidelity-v26','fidelity-v27','fidelity-v28']:
    target=sources/name;target.mkdir(exist_ok=True)
    for f in(r/name).glob('*.json'):
        if not f.name.startswith('pool-before'):shutil.copy2(f,target/f.name)
for number in [25,26,27,28]:
    for f in r.glob(f'*fidelity_v{number}*.py'):shutil.copy2(f,sources/f.name)
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
for number in [26,27]:
    shutil.copytree(r/f'fidelity-v{number}'/'screenshots',sources/f'fidelity-v{number}'/'screenshots',dirs_exist_ok=True)
shutil.copy2(r/'fidelity-v25/rejected-candidate.json',sources/'rejected-v25.json')
shutil.copy2(r/'terrain_triangle_distance.py',sources/'terrain_triangle_distance.py')
base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V28','status':'One rounded central stone copy, original source collision retained; source grass/stone components split and58 stone parts taller,47 copied groups moved outward. Stone pixels retained. Candidate, not integrated.'}]}
q=a26['newPrototypes'][0];material_ids=[next(m['id']for m in ledger['materials']if m.get('name',m.get('displayName'))==name)for name in q['materials']]
new=[{**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],
    'physicalSourcePath':a26['visualLibrary'],'file':info(a26['visualLibrary']),'dependencies':material_ids+[q['sourcePoolObjectId']],'reason':q['role']}]
mod26=pack/'models/volcano-remake-fidelity-v26'
for key,path,kind,deps in [
    ('rounded-central-stone',Path(q['sourceModel']),'shared-runtime-model',[q['id']]),
    ('original-central-stone-collider',r/'fidelity-v26/candidate/vr_v26_original_stone_walls_collision.spm','map-physics-preservation-model',[q['id']]),
    ('volcano-track',w/'candidate/volcano_track.spm','map-runtime-model',material_ids)]:
    stored=mod26/path.name;assert stored.read_bytes()==path.read_bytes()
    new.append({**base,'id':'volcano-fidelity-v26-runtime-'+key,'displayName':path.name,'kind':kind,'reuseTier':'adapt',
        'canonicalPackPath':str(stored),'physicalSourcePath':str(path),'file':info(stored),'dependencies':deps,
        'productionIntegrated':False,'reason':'V26 central visual geometry separated from its exact original collision; original route/controls retained. Collider is map-specific preservation data, not general interchangeable scenery.'})
mod27=pack/'models/volcano-remake-fidelity-v27'
for part in parts:
    lib=Path(part['library']);stored_lib=mod27/lib.name;shutil.copytree(lib,stored_lib,dirs_exist_ok=True)
    path=Path(part['model']);stored=stored_lib/path.name;assert stored.read_bytes()==path.read_bytes()
    source_id='volcano-fidelity-v22-'+('grasslip'if part['part']=='grass_cap'else'stonebody')
    new.append({**base,'id':'volcano-fidelity-v27-runtime-'+part['part'].replace('_','-'),'displayName':path.name,
        'kind':'shared-runtime-component-export','reuseTier':'direct','canonicalPackPath':str(stored),'physicalSourcePath':str(path),
        'file':info(stored),'dependencies':[source_id],'runtimeLibraryPackPath':str(stored_lib),
        'runtimeLibraryFiles':[info(f)for f in sorted(stored_lib.iterdir())if f.is_file()],
        'newAuthoredGeometry':False,'newTexturePixels':False,'productionIntegrated':False,
        'reason':'Exact source pooled component positions/indices/normals/RGB/UV/local bounds. Split export permits independent grass/stone instance coordinates without duplicating model per placement.'})
ids_to_add={v['id']for v in new}
for d in [pool,ledger]:d['objects']=[q for q in d['objects']if q['id']not in ids_to_add]+copy.deepcopy(new)
ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V28 central support and visible tall coordinate cliffs','status':a['status'],'finalBlend':a['finalBlend'],
    'nativeSharedParts':340,'preservation':budget,'budget':budget,'runtimeValidation':run,
    'deltaAssetCounts':{'objects':6,'materials':0,'textures':0,'newNativePrototypes':1,'directReusedRuntimeComponentExports':2},
    'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(sources/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
    assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
    assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
    for f in q.get('runtimeLibraryFiles',[]):assert info(f['path'])==f,q['id']
audit={'newObjectRecords':6,'newNativePrototypes':1,'directReusedNativePartPrototypes':2,'newAuthoredMaterials':0,'newTextures':0,
    'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),
    'unresolvedDependencies':[],'canonical':ci,'nativeSharedParts':340,'sourceMeshesBeforeCoordinateChanges':'V26625nativeMeshesExact',
    'rejectedV25ExcludedFromAppResources':True,'productionIntegrated':False,'referenceAcceptance':False}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V28_CENTRAL_SUPPORT_AND_COORDINATE_CLIFFS_REGISTERED',audit,flush=True)
