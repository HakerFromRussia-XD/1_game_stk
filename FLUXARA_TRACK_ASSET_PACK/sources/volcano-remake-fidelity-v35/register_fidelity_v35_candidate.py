from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v35';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';archive=pack/'sources/volcano-remake-fidelity-v35';archive.mkdir(exist_ok=True);pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v32/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());native=json.loads((w/'final-blend-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text())
assert run['naturalFinishObserved']and run['finalProbeTrackCleanupVerified']and native['allOtherNativeGeometryUVNormalsColorsMaterialsExactV32']==584
assert 'V35_NATIVE_CANONICAL_PIPELINE_COMPLETE'in(w/'native-canonical-verification-repaired.log').read_text()
def info(path):
 path=Path(path);return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
source=pack/'models/volcano-remake-fidelity-v3/Lavafield.spm';current=w/'candidate/Lavafield.spm';x=parse(source);y=parse(current)
def strip(buf):return {'vertices':[{k:v for k,v in p.items()if not k.endswith('offset')}for p in buf['vertices']],'indices':buf['indices'],'material':buf['material']}
assert x['bounds']==y['bounds']and x['flags']==y['flags']and [strip(q)for q in x['buffers']]==[strip(q)for q in y['buffers']]
if not(w/'pool-before-v35.json').exists():shutil.copy2(pf,w/'pool-before-v35.json')
mod=pack/'models/volcano-remake-fidelity-v35';stored=mod/'Lavafield.spm';shutil.copy2(current,stored);assert stored.read_bytes()==current.read_bytes()
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';new=[]
for row in a['newPrototypes']:
 deps=[next(q['id']for q in ledger['materials']if q.get('name',q.get('displayName'))==name)for name in row['materials']]
 new.append({**row,'displayName':row['name'],'kind':'visual-object','sourceMap':'fluxara-user-volcano-remake','reuseTier':'direct','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(a['visualLibrary']),'categories':['lava'],'dependencies':deps+[row['sourcePoolObjectId']],'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V35','instances':1,'status':'Reused existing current Lavafield buffer below the road. Native/source/runtime checked; overall reference fidelity and production integration unfinished.'}],'reason':row['role']})
new.append({'id':'volcano-fidelity-v35-reused-lava-valley-runtime','displayName':'Lavafield.spm reused valley','kind':'map-local-runtime-model','sourceMap':'fluxara-user-volcano-remake','reuseTier':'adapt','categories':['lava'],'canonicalPackPath':str(stored),'physicalSourcePath':str(current),'file':info(stored),'dependencies':[q['id']for q in a['newPrototypes']],'runtimeResourceCandidatePath':str(current),'newGameAssetPayloadBytes':0,'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V35','instances':2,'status':'Original field placement plus one new valley coordinate. One existing file, no per-placement mesh duplication.'}],'sourcePoolObjectId':'volcano-fidelity-v3-model-e45f7ddeca7c','adaptation':'Mesh bounds, indexed positions, normals and UVs exactly match original pooled model. Existing V13 shared lava texture filename alias retained from V32, with current V32 material/image variants reused unchanged. No new pixels in V35. Native source-part order2/1/0 explicitly mapped to runtime buffers0/1/2.','productionIntegrated':False})
newids={q['id']for q in new}
for target in [pool,ledger]:
 target['objects']=[q for q in target['objects']if q['id']not in newids]+copy.deepcopy(new)
 for q in target['objects']:
  if q['id']in ['volcano-fidelity-v32-sealed-stonebody','volcano-fidelity-v32-sealed-stonebody-runtime','volcano-fidelity-v32-sealed-grasscap','volcano-fidelity-v32-sealed-grasscap-runtime']:
   count=97 if 'stonebody'in q['id']else 82;uses=q.setdefault('uses',[]);uses[:]=[x for x in uses if x.get('candidate')!='V35'];uses.append({'trackId':'fluxara-user-volcano-remake','candidate':'V35','instances':count,'status':'Existing accepted paired models reused,82cliff groups and15stone castle supports. Geometry/pixels reused; protected road/control nodes unchanged.'})
ci=info(canon)
def refresh(obj):
 if isinstance(obj,dict):
  if obj.get('path')==str(canon)and'sha256'in obj:obj.update(ci)
  for v in obj.values():refresh(v)
 elif isinstance(obj,list):
  for v in obj:refresh(v)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();pool['assets']=pool['objects']+pool['materials']+pool['textures'];ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4156
budget.update({'nativeCanonicalPoolAndGameplayPending':False,'naturalFullLapFinishObserved':True});(w/'preservation-verification.json').write_text(json.dumps(budget,indent=2))
ledger.update({'candidate':'V35 reused matched82cliff groups and lava valley','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':430,'preservation':budget,'budget':budget,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjectsAndRuntimeRecords':4,'newNativePrototypes':3,'newMaterials':0,'newTextures':0,'newGameAssetPayloadBytes':0},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures']
for q in ledger['assets']:
 assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
 if q.get('physicalSourcePath'):assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
 assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeLibraryFiles','runtimeFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,archive/folder,dirs_exist_ok=True)
ledger['mapRuntimeFiles']=[info(q)for q in(archive/'candidate').iterdir()if q.is_file()]
audit={'newNativePrototypeRecords':3,'newMapLocalRuntimeRecord':1,'newMaterials':0,'newTextures':0,'newGameAssetPayloadBytes':0,'allPhysicalPathsAndFileHashesMatch':True,'sourceLavafieldIndexedGeometryBoundsNormalsUVsExactOriginalPool':True,'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'unresolvedDependencies':[],'canonical':ci,'nativeSharedParts':430,'otherNativeGeometryExactV32':584,'otherNativeMatricesExactV32':561,'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,archive/f.name)
for f in r.glob('*fidelity_v35*.py'):shutil.copy2(f,archive/f.name)
shutil.copy2(r/'terrain_triangle_distance.py',archive/'terrain_triangle_distance.py')
for version,names in [('v33',['mass-replacement-preflight.json','visual-rejection.json']),('v34',['valley-preflight.json','preservation-verification.json','cliff-clearance-verification.json','castle-supports.json','visual-rejection.json'])]:
 dest=archive/'prior-experiments'/version;dest.mkdir(parents=True,exist_ok=True)
 for name in names:shutil.copy2(r/('fidelity-'+version)/name,dest/name)
ski=r.parent.parent/'fluxara-user-ski-dash.asset-ledger.json'
if ski.exists():
 before=json.loads(ski.read_text());after=copy.deepcopy(before);refresh(after)
 if after!=before:(w/'ski-dash-ledger-before-canonical-metadata-refresh.json').write_text(json.dumps(before,ensure_ascii=False,indent=2));ski.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
print('V35_REUSED_VALLEY_AND_POOLED_SUPPORTS_REGISTERED',audit,flush=True)
