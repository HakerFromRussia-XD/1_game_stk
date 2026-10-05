from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v23';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK'
sources=pack/'sources/volcano-remake-fidelity-v23';sources.mkdir(exist_ok=True);mod=pack/'models/volcano-remake-fidelity-v23'
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v22/candidate-asset-ledger.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==1
assert json.loads((w/'final-blend-verification.json').read_text())['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV22']==610
assert (w/'canonical-bindings-verification.json').is_file()
run=json.loads((w/'runtime-validation.json').read_text());assert run['visualInspectionCompleted']and run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']
if not(w/'pool-before-v23.json').exists():shutil.copy2(pf,w/'pool-before-v23.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for f in r.glob('*fidelity_v23*.py'):shutil.copy2(f,sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'):shutil.copy2(f,sources/f.name)
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
shutil.copytree(r/'backdrop-v22-comparison',sources/'backdrop-v22-comparison',dirs_exist_ok=True)
shutil.copy2(r/'capture_backdrop_v22_comparison.py',sources/'capture_backdrop_v22_comparison.py')
p=json.loads((w/'backdrop-changes.json').read_text());pres=json.loads((w/'preservation-verification.json').read_text())
shutil.copytree(Path(p['newSharedTerrainLibrary']),sources/'runtime-library',dirs_exist_ok=True);shutil.copy2(r/'terrain_triangle_distance.py',sources/'terrain_triangle_distance.py')
base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V23','status':'Two broad distant green caps rounded in copied shared terrain. All other V20 terrain indexed attributes retained. Whole model local bounds/axes/origin and instance transform retained. Source V22 geometry, physics, controls and stone pixels/UVs unchanged. Not integrated.'}]}
q=a['newPrototypes'][0];deps=[next(m['id']for m in ledger['materials']if m.get('name',m.get('displayName'))==name)for name in q['materials']]+[q['sourcePoolObjectId']]
new=[{**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':deps,'reason':q['role']}]
source=Path(q['sourceModel']);stored=mod/source.name;assert stored.read_bytes()==source.read_bytes()
new.append({**base,'id':'volcano-fidelity-v23-runtime-backdrop-terrain','displayName':source.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(source),'file':info(stored),'dependencies':[q['id']],'productionIntegrated':False,'newTextureFiles':0,'reason':'One shared ghost terrain model replaces V20 library reference; original source collider is byte-exact. Source library retained and charged in total bytes.'})
for d in [pool,ledger]:d['objects']=[q for q in d['objects']if not q['id'].startswith('volcano-fidelity-v23-')]+new
ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon)and 'sha256'in v:v.update(ci)
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V23 rounded distant terrain caps','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':len(a['nativeSharedInstances']),'preservation':pres,'budget':pres,'runtimeValidation':run,'deltaAssetCounts':{'objects':2,'materials':0,'textures':0},'productionIntegrated':False,'newImagePixels':False})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(sources/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
    assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
    assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':2,'newNativePrototypes':1,'newMaterials':0,'newTextures':0,'newSharedTerrainModels':1,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False,'previousV22ModelsAndTexturesUnchanged':True,'nativeSharedParts':333}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V23_SHARED_BACKDROP_REGISTERED',audit,flush=True)
