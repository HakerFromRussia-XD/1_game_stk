from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v16';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v16';mod=pack/'models/volcano-remake-fidelity-v16';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v15/candidate-asset-ledger.json').read_text());p=json.loads((w/'terrain-changes.json').read_text());pres=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==2;assert(w/'canonical-bindings-verification.json').is_file();assert run['visualInspectionCompleted']and run['resourceCleanupRuntimeVerified'];assert p['newCliffPlacements']==58
sources.mkdir(exist_ok=True)
if not(w/'pool-before-v16.json').exists():shutil.copy2(pf,w/'pool-before-v16.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for f in r.glob('*fidelity_v16*.py'):shutil.copy2(f,sources/f.name)
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,sources/f.name)
for folder in ['candidate','native','screenshots','iterations','removed-unused-images']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
lib=Path(p['adaptedSharedLibrary']);shutil.copytree(lib,sources/'runtime-libraries'/lib.name,dirs_exist_ok=True)
usage=[{'trackId':'fluxara-user-volcano-remake','candidate':'V16','status':'58 placements of one adapted pooled rounded stone cliff. Prior stone pixels and UVs retained. Isolated candidate, not integrated.'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['rounded-cliff','stone','grass'],'uses':usage};tid='volcano-fidelity-v16-stone-texture-alias';alias=a['runtimeTextureAliases']['fluxara_volcano_stone_shared_v16.jpg'];oldtex=next(q for q in ledger['textures']if q.get('displayName')=='Rock13_col.jpg')
tex={**base,'id':tid,'displayName':'fluxara_volcano_stone_shared_v16.jpg','kind':'texture','reuseTier':'direct','canonicalPackPath':alias['packPath'],'physicalSourcePath':oldtex['canonicalPackPath'],'file':info(Path(alias['packPath'])),'dependencies':[oldtex['id']],'runtimePackagedPath':alias['source'],'runtimeIntegrated':False,'nativeImageEquivalent':alias['originalNativeImage'],'nativeMaterialEquivalent':alias['existingNativeMaterial'],'reason':'One global runtime alias of the exact old stone image, used by four unchanged source models and one new shared cliff. Source pixels and old UVs retained; no new native image or pixel generation.'}
mats=[{**base,**q,'displayName':q['name'],'kind':'material','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+q['name'],'physicalSourcePath':a['visualLibrary'],'dependencies':[],'reason':q['adaptation']}for q in a['newMaterialVariants']]
matids={q.get('name',q.get('displayName')):q['id']for q in ledger['materials']+mats};obj=[]
for q in a['newPrototypes']:
 deps=[matids[n]for n in q['materials']]+[p['sourcePoolObjectId']];obj.append({**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':deps,'reason':q['role']})
source=Path(p['adaptedSharedModel']);stored=mod/source.name;assert stored.read_bytes()==source.read_bytes()
obj.append({**base,'id':'volcano-fidelity-v16-rounded-cliff-runtime','displayName':source.name,'kind':'runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(source),'file':info(stored),'dependencies':[matids['VRV16_GrassLipVertexColor'],matids['VRV4E_Rock13_col.jpg'],tid],'runtimePackagedPath':str(source),'runtimeIntegrated':False,'reason':'One combined two-buffer SPM for all 58 Ghost coordinate placements. Copied pooled source local bounds, axes and centre retained.'})
for name in p['existingStoneModelsAliasOnly']:
 source=w/'candidate'/name;stored=mod/name;stored.write_bytes(source.read_bytes());obj.append({**base,'id':'volcano-fidelity-v16-runtime-'+Path(name).stem,'displayName':name,'kind':'map-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(source),'file':info(stored),'dependencies':[tid],'runtimeIntegrated':False,'reason':'Texture table filename alias only. Every indexed geometry, original UV, normal, vertex color, material slot and bound retained; includes protected course or map-specific effects, not interchangeable scenery.'})
for key,items in {'objects':obj,'materials':mats,'textures':[tex]}.items():
 pool[key]=[q for q in pool[key]if not q['id'].startswith('volcano-fidelity-v16-')]+items;ledger[key]=[q for q in ledger[key]if not q['id'].startswith('volcano-fidelity-v16-')]+items
ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures'];ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids));ledger.update({'candidate':'V16 rounded stone and grass cliff from existing pooled shelf','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':len(a['nativeSharedInstances']),'preservation':pres,'budget':pres,'runtimeValidation':run,'deltaAssetCounts':{'objects':len(obj),'materials':len(mats),'textures':1},'productionIntegrated':False,'newImagePixels':False,'newCliffPlacements':58,'legacySkyCopiesRemovedOnlyInCandidate':p['removedUnusedSkyImages']});ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(sources/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
 assert q['id']in ids;assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':len(obj),'newNativePrototypes':2,'newRuntimeMeshFiles':1,'newAliasOnlyMapExports':4,'newMaterials':len(mats),'newTextureAliases':1,'newNativeImages':0,'newImagePixels':False,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'nativeSharedParts':len(a['nativeSharedInstances']),'productionIntegrated':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V16_POOL_ROUNDED_TERRAIN_REGISTERED',audit,flush=True)
