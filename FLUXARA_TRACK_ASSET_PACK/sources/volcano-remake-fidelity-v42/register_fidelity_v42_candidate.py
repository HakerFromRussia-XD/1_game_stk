from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil,subprocess,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v42';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';res=repo/'iosApp/FluxaraResources';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v41/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());n=json.loads((w/'final-blend-verification.json').read_text());b=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());cp=json.loads((w/'canonical-registration.json').read_text());assert run['visualInspectionCompleted']and run['temporaryCopiedResourcesCleanupVerified']and not n['canonicalPending'];assert'V42_NATIVE_STONE_UV_AND_ALL_POSES_REOPEN_VERIFIED'in(r/'fidelity-v42-native-main-and-far-stone.log').read_text();arc=pack/'sources/volcano-remake-fidelity-v42';arc.mkdir(exist_ok=True);mod=pack/'models/volcano-remake-fidelity-v42';mod.mkdir(exist_ok=True)
def info(f):
 f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';assert info(canon)['sha256']==cp['sha256']
if not(w/'pool-before-v42.json').exists():shutil.copy2(pf,w/'pool-before-v42.json')
visual=mod/Path(a['visualLibrary']).name;shutil.copy2(a['visualLibrary'],visual);rows=[];roles={'Terrain':('fluxara_driftlib_volcano_closed_terrain_v42',1)}
for q in a['newPrototypes']:
 role=q['name'].split('_')[-1];lib,count=roles[role];source=w/'shared-runtime'/lib;dst=mod/lib;runtime=res/'library'/lib
 assert not dst.exists()and not runtime.exists();shutil.copytree(source,dst);shutil.copytree(source,runtime);uses=[{'trackId':'fluxara-user-volcano-remake','candidate':'V42','instances':count,'status':'Working draft source/native/full natural lap verified; production and complete reference acceptance pending.'}];native=copy.deepcopy(q);native.update({'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':str(visual),'file':info(visual),'dependencies':[q['sourcePoolObjectId']]+[x['id']for x in ledger['materials']if x.get('name')in q['materials']],'reason':'Copied source variant. Local active/header dimensions,origin,axes retained; no raster changes. Logical model plus used textures within+20%.'});rows.append(native)
 f=dst/Path(q['sourceModel']).name;rows.append({'id':q['id']+'-runtime','sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses,'displayName':f.name,'kind':'shared-runtime-model','reuseTier':'adapt','canonicalPackPath':str(f),'physicalSourcePath':q['sourceModel'],'file':info(f),'dependencies':[q['id']],'runtimeLibraryPackPath':str(dst),'runtimeResourceSourcePath':str(runtime),'runtimeLibraryFiles':[info(p)for p in sorted(dst.iterdir())if p.is_file()],'newTexturePixels':False,'productionIntegrated':False,'reason':'One physical model plus coordinates; no per-placement geometry export. All new and prioraccepted game payload counted.'})
 for p in source.iterdir():assert info(dst/p.name)['sha256']==info(p)['sha256']==info(runtime/p.name)['sha256']
for target in [pool,ledger]:
 assert not({q['id']for q in target['objects']}&{q['id']for q in rows});target['objects']+=copy.deepcopy(rows);target['assets']=target['objects']+target['materials']+target['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4194
for q in ledger['assets']:
 assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeFiles','runtimeLibraryFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
def archive_clone(src,dst):
 dst=Path(dst)
 if dst.exists():
  if Path(src).read_bytes()==dst.read_bytes():return str(dst)
  dst.unlink()
 subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True);return str(dst)
for folder in ['candidate','native','screenshots','shared-runtime']:shutil.copytree(w/folder,arc/folder,dirs_exist_ok=True,copy_function=archive_clone)
ledger.update({'candidate':'V42 source stone pixels retained, distant texture scale enlarged, reference near cliffs unchanged','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':n['nativeSharedParts'],'preservation':b,'budget':b,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjectRecords':2,'newNativePrototypes':1,'newMaterials':0,'newTextures':0,'newGameAssetPayloadBytes':b['newSharedRuntimeAllFilesBytes'],'newCoordinateInstances':0},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});ledger['mapRuntimeFiles']=[info(f)for f in sorted((arc/'candidate').iterdir())if f.is_file()];pool['updated']=datetime.now(timezone.utc).isoformat();pool['physicalPack']['blenderLibrary']=info(canon)
audit={'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'newNativePrototypes':1,'newMaterialDefinitions':0,'newTexturePixels':False,'newSharedRuntimeBytes':b['newSharedRuntimeAllFilesBytes'],'reusedTerrainCoordinateInstances':1,'allPhysicalPathsHashesDependenciesVerified':True,'canonical':info(canon),'nativePrototypes':n['nativePrototypeCount'],'nativeMaterialDefinitions':n['nativeMaterialDefinitionCount'],'nativeSharedParts':n['nativeSharedParts'],'allCandidateAndAcceptedHistoryBytes':b['allCandidateAndAcceptedHistoryBytes'],'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,arc/f.name)
for f in r.glob('*fidelity_v39*.py'):shutil.copy2(f,arc/f.name)
for f in r.glob('fidelity-v42*.log'):shutil.copy2(f,arc/f.name)
print('V42_SHARED_SOURCE_NATIVE_RUNTIME_POOL_REGISTERED',audit,flush=True)
