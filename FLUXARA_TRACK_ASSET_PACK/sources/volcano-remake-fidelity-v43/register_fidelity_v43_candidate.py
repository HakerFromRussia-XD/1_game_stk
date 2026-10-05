from pathlib import Path
import copy,hashlib,json,shutil,subprocess
from datetime import datetime,timezone
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';res=repo/'iosApp/FluxaraResources';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
a=json.loads((w/'asset-registration.json').read_text());n=json.loads((w/'final-blend-verification.json').read_text());b=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());cp=json.loads((w/'canonical-registration.json').read_text());assert not n['canonicalPending']and run['naturalFinishObserved']
pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v42/candidate-asset-ledger.json').read_text());mod=pack/'models/volcano-remake-fidelity-v43';arc=pack/'sources/volcano-remake-fidelity-v43';arc.mkdir(exist_ok=True);shutil.copy2(pf,w/'pool-before-v43.json')
def info(f):
 f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
def clone(src,dst):
 dst=Path(dst)
 if dst.exists():
  if Path(src).read_bytes()==dst.read_bytes():return str(dst)
  dst.unlink()
 subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True);return str(dst)
visual=mod/Path(a['visualLibrary']).name;clone(a['visualLibrary'],visual);reference=mod/'source-v14-volcano_track.spm';clone(r/'fidelity-v14/candidate/volcano_track.spm',reference)
q=a['newPrototypes'][0];source=Path(q['sourceModel']).parent;dst=mod/source.name;runtime=res/'library'/source.name;assert not runtime.exists();shutil.copytree(source,runtime)
assert all((dst/f.name).read_bytes()==f.read_bytes()==(runtime/f.name).read_bytes()for f in source.iterdir())
uses=[{'trackId':'fluxara-user-volcano-remake','candidate':'V43','instances':1,'status':'Continuous landscape draft, ordinary natural lap verified; visual approval pending.'}]
native=copy.deepcopy(q);native.update({'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':cp['path']+'#Object/'+q['name'],'physicalSourcePath':str(visual),'file':info(visual),'dependencies':['volcano-fidelity-v10b-cliff-volcano_track','volcano-fidelity-v14-central-rock']+[z['id']for z in ledger['materials']if z.get('name')in q['materials']],'sourceReferenceFile':info(reference),'reason':'Restore the V14 contiguous source landscape. Geometry copied from source; source main retained and collision unchanged. No raster pixels or materials authored.'})
model=dst/Path(q['sourceModel']).name;export={'id':q['id']+'-runtime','sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses,'displayName':model.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(model),'physicalSourcePath':q['sourceModel'],'file':info(model),'dependencies':[q['id']],'runtimeLibraryPackPath':str(dst),'runtimeResourceSourcePath':str(runtime),'runtimeLibraryFiles':[info(f)for f in sorted(dst.iterdir())if f.is_file()],'productionIntegrated':False,'newTexturePixels':False}
rows=[native,export]
for target in [pool,ledger]:
 assert not({q['id']for q in target['objects']}&{q['id']for q in rows});target['objects']+=copy.deepcopy(rows);target['assets']=target['objects']+target['materials']+target['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))
for q in ledger['assets']:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeFiles','runtimeLibraryFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
ledger.update({'candidate':'V43 continuous source landscape restoration','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':n['nativeSharedParts'],'preservation':b,'budget':b,'runtimeValidation':run,'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});pool['physicalPack']['blenderLibrary']={k:v for k,v in cp.items()if k in ['path','bytes','sha256']};pool['updated']=datetime.now(timezone.utc).isoformat();pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
audit={'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'allPhysicalPathsHashesDependenciesVerified':True,'canonical':pool['physicalPack']['blenderLibrary'],'nativeSharedParts':n['nativeSharedParts'],'nativePrototypes':n['nativePrototypeCount'],'newMaterials':0,'newTexturePixels':False,'productionIntegrated':False};(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for folder in ['candidate','native','screenshots','shared-runtime']:shutil.copytree(w/folder,arc/folder,dirs_exist_ok=True,copy_function=clone)
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,arc/f.name)
print('V43_NATIVE_RUNTIME_CANONICAL_POOL_REGISTERED',audit,flush=True)
