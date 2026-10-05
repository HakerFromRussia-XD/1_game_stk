from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v29';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v29';sources.mkdir(exist_ok=True)
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v28/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());p=json.loads((w/'stone-foot-changes.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());native=json.loads((w/'final-blend-verification.json').read_text())
assert run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']and native['allOtherNativeMeshGeometryUVsNormalsColorsAndMaterialsExactV28']==567
assert 'V29_CANONICAL_GROUNDED_STONE_BODY_BINDINGS_VERIFIED'in(w/'canonical-verification.log').read_text()
if not(w/'pool-before-v29.json').exists():shutil.copy2(pf,w/'pool-before-v29.json')
def info(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):shutil.copy2(f,sources/f.name)
for f in r.glob('*fidelity_v29*.py'):shutil.copy2(f,sources/f.name)
shutil.copy2(r/'terrain_triangle_distance.py',sources/'terrain_triangle_distance.py')
base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V29','status':'58 coordinate instances of one adapted stone body. Source pixels/local bounds/poses retained; lower geometry broadened. Candidate, not integrated.'}]}
q=a['newPrototypes'][0];materialids=[next(m['id']for m in ledger['materials']if m.get('name',m.get('displayName'))==name)for name in q['materials']]
mod=pack/'models/volcano-remake-fidelity-v29';lib=Path(p['newSharedLibrary']);storedlib=mod/lib.name;stored=storedlib/Path(p['newSharedModel']).name
assert stored.read_bytes()==Path(p['newSharedModel']).read_bytes()
new=[{**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],'file':info(a['visualLibrary']),'dependencies':materialids+[q['sourcePoolObjectId']],'reason':q['role']},
     {**base,'id':'volcano-fidelity-v29-runtime-grounded-stonebody','displayName':stored.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':p['newSharedModel'],'file':info(stored),'dependencies':[q['id']],'runtimeLibraryPackPath':str(storedlib),'runtimeLibraryFiles':[info(f)for f in sorted(storedlib.iterdir())if f.is_file()],'newTexturePixels':False,'productionIntegrated':False,'reason':'One shared model for58 existing placements. Broader lower body; exact source topology/UV/RGB/local bounds, upper half and instance transforms retained. Original pooled source preserved.'}]
newids={v['id']for v in new}
for d in [pool,ledger]:d['objects']=[q for q in d['objects']if q['id']not in newids]+copy.deepcopy(new)
ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures'];ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V29 stone texture and broader lower cliff bodies','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':340,'preservation':budget,'budget':budget,'runtimeValidation':run,'deltaAssetCounts':{'objects':2,'materials':0,'textures':0,'newNativePrototypes':1},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(sources/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
    assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists()and all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
    for f in q.get('runtimeLibraryFiles',[]):assert info(f['path'])==f,q['id']
audit={'newObjectRecords':2,'newNativePrototypes':1,'newAuthoredMaterials':0,'newTextures':0,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'nativeSharedParts':340,'allOtherNativeMeshesExactV28':567,'allPreviousObjectMatricesExactV28':625,'productionIntegrated':False,'referenceAcceptance':False}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V29_GROUNDED_STONE_BODY_REGISTERED',audit,flush=True)
