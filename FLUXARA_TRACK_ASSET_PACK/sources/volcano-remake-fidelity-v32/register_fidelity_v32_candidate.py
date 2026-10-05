from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';archive=pack/'sources/volcano-remake-fidelity-v32';archive.mkdir(exist_ok=True);pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v30/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());native=json.loads((w/'final-blend-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text())
assert run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']and native['allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV30']==651
assert 'V32_CANONICAL_MATCHED_SEAMS_AND_PREVIOUS_BINDINGS_VERIFIED'in(w/'canonical-verification.log').read_text()
budget.update({'canonicalNativePoolAndGameplayPending':False,'newNativePrototypesVerified':2,'naturalFullLapFinishObserved':True})
(w/'preservation-verification.json').write_text(json.dumps(budget,indent=2))
def info(path):
 path=Path(path);return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
if not(w/'pool-before-v32.json').exists():shutil.copy2(pf,w/'pool-before-v32.json')
for folder in ['candidate','native','screenshots','shared-runtime']:shutil.copytree(w/folder,archive/folder,dirs_exist_ok=True)
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,archive/f.name)
for f in r.glob('*fidelity_v32*.py'):shutil.copy2(f,archive/f.name)
shutil.copy2(r/'terrain_triangle_distance.py',archive/'terrain_triangle_distance.py')
new=[];canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';mod=pack/'models/volcano-remake-fidelity-v32'
for row in a['newPrototypes']:
 lib=Path(row['sourceModel']).parent;storedlib=mod/lib.name;stored=storedlib/Path(row['sourceModel']).name;assert stored.read_bytes()==Path(row['sourceModel']).read_bytes()
 resourceLib=repo/'iosApp/FluxaraResources/library'/lib.name
 if not resourceLib.exists():shutil.copytree(lib,resourceLib)
 assert all((resourceLib/f.name).read_bytes()==f.read_bytes()for f in lib.iterdir()if f.is_file())
 deps=[next(m['id']for m in ledger['materials']if m.get('name',m.get('displayName'))==name)for name in row['materials']]
 base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V32','instances':24,'status':'Matching copied grass/stone seam on24 added groups. Source pixels/local dimensions/UV/RGB/topology retained. Runtime/native/pool verified; isolated intermediate, production integration and full reference fidelity unfinished.'}]}
 new.append({**base,**row,'displayName':row['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(a['visualLibrary']),'dependencies':deps+[row['sourcePoolObjectId']],'reason':row['role']})
 new.append({**base,'id':row['id']+'-runtime','displayName':stored.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':row['sourceModel'],'file':info(stored),'dependencies':[row['id']],'runtimeLibraryPackPath':str(storedlib),'runtimeResourceSourcePath':str(resourceLib),'runtimeLibraryFiles':[info(f)for f in sorted(storedlib.iterdir())if f.is_file()],'newTexturePixels':False,'productionIntegrated':False,'reason':'One copied shared component referenced by24 instance coordinates. Matched boundary positions and adjacent normals; topology/UV/RGB/local bounds/source pixels unchanged. Source shared-resource copy prepared; no rebuilt main app integration claim.'})
newids={q['id']for q in new}
for target in [pool,ledger]:target['objects']=[q for q in target['objects']if q['id']not in newids]+copy.deepcopy(new)
ci=info(canon)
def refresh(obj):
 if isinstance(obj,dict):
  if obj.get('path')==str(canon)and'sha256'in obj:obj.update(ci)
  for v in obj.values():refresh(v)
 elif isinstance(obj,list):
  for v in obj:refresh(v)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures'];ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4152
ledger.update({'candidate':'V32 matched copied grass/stone boundaries','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':412,'preservation':budget,'budget':budget,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjectsAndRuntimeRecords':4,'newNativePrototypes':2,'newMaterials':0,'newTextures':0},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(q)for q in(archive/'candidate').iterdir()if q.is_file()]
for q in ledger['assets']:
 assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
 if q.get('physicalSourcePath'):assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
 assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeLibraryFiles','runtimeFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
audit={'newObjectAndRuntimeRecords':4,'newNativePrototypes':2,'newMaterials':0,'newTextures':0,'allPhysicalPathsAndFileHashesMatch':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'nativeSharedParts':412,'otherNativeGeometryExactV30':651,'otherNativeMatricesExactV30':651,'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for file in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/file,archive/file)
# Refresh only the explicitly stored current canonical metadata in the map2 ledger.
ski=r.parent.parent/'fluxara-user-ski-dash.asset-ledger.json'
if ski.exists():
 before=json.loads(ski.read_text());after=copy.deepcopy(before);refresh(after)
 if after!=before:(w/'ski-dash-ledger-before-canonical-metadata-refresh.json').write_text(json.dumps(before,ensure_ascii=False,indent=2));ski.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
print('V32_SHARED_SEAM_ASSETS_AND_LEDGER_VERIFIED',audit,flush=True)
