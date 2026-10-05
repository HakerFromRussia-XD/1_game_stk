from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent;w=r/'fidelity-v41';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v40/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());n=json.loads((w/'final-blend-verification.json').read_text());b=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());cp=json.loads((w/'canonical-registration.json').read_text())
assert run['naturalFinishObserved']and run['temporaryCopiedResourcesCleanupVerified']and not n['canonicalPending']
assert 'V41_NATIVE_REOPEN_STONE_SMOKE_AND_MATRICES_VERIFIED'in(r/'fidelity-v41-native-reopen-corrected.log').read_text()
arc=pack/'sources/volcano-remake-fidelity-v41';arc.mkdir(exist_ok=True);mod=pack/'models/volcano-remake-fidelity-v41';mod.mkdir(exist_ok=True);texdir=pack/'textures/volcano-remake-fidelity-v41';texdir.mkdir(exist_ok=True)
def info(f):
 f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';assert info(canon)['sha256']==cp['sha256']
if not(w/'pool-before-v41.json').exists():shutil.copy2(pf,w/'pool-before-v41.json')
visual=mod/Path(a['visualLibrary']).name;shutil.copy2(a['visualLibrary'],visual)
uses=[{'trackId':'fluxara-user-volcano-remake','candidate':'V41','status':'Source/native/natural lap verified; production integration and reference acceptance pending.'}];rows=[]
texture=next((k,v)for k,v in a['textures'].items()if k=='fluxara_volcano_smoke_palette_v41.png');alias=texdir/texture[0];shutil.copy2(texture[1]['source'],alias)
texrow={'id':texture[1]['poolId'],'kind':'texture','sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'reuseTier':'direct','displayName':alias.name,'canonicalPackPath':str(alias),'physicalSourcePath':texture[1]['source'],'file':info(alias),'dependencies':[texture[1]['reusedPixelsPoolId']],'reusedPixelsPoolId':texture[1]['reusedPixelsPoolId'],'newImagePixels':False,'uses':uses}
matrow=copy.deepcopy(a['newMaterialVariants'][0]);matrow.update({'kind':'material','sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'reuseTier':'adapt','displayName':matrow['name'],'canonicalPackPath':str(canon)+'#Material/'+matrow['name'],'physicalSourcePath':str(visual),'file':info(visual),'dependencies':[texrow['id']],'uses':uses})
for q in a['newPrototypes']:
 native=copy.deepcopy(q);native.update({'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':str(visual),'file':info(visual),'dependencies':[q['sourcePoolObjectId'],matrow['id']],'reason':'Copy with exact source local geometry/normals/bounds/origin/axes. Only UV and baked lighting changed; logical model plus used texture under+20%.'});rows.append(native)
 model=mod/Path(q['sourceModel']).name;shutil.copy2(q['sourceModel'],model)
 rows.append({'id':q['id']+'-runtime','kind':'map-runtime-model','sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'reuseTier':'adapt','displayName':model.name,'canonicalPackPath':str(model),'physicalSourcePath':q['sourceModel'],'file':info(model),'dependencies':[q['id'],matrow['id']],'uses':uses,'newImagePixels':False,'productionIntegrated':False,'runtimePackaging':'Map-owned model referenced by existing scene coordinates; reusable pack source is separate from installed app payload.'})
for target in [pool,ledger]:
 for field,newrows in [('objects',rows),('materials',[matrow]),('textures',[texrow])]:
  assert not({q['id']for q in target[field]}&{q['id']for q in newrows});target[field]+=copy.deepcopy(newrows)
 target['assets']=target['objects']+target['materials']+target['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4192
for q in ledger['assets']:
 assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeFiles','runtimeLibraryFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
def clone(src,dst):
 dst=Path(dst)
 if dst.exists():
  if Path(src).read_bytes()==dst.read_bytes():return str(dst)
  dst.unlink()
 subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True);return str(dst)
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,arc/folder,dirs_exist_ok=True,copy_function=clone)
ledger.update({'candidate':'V41 stone retained, red/white low roadside blocks, warm unlit smoke','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':n['nativeSharedParts'],'preservation':b,'budget':b,'runtimeValidation':run,'deltaAssetCounts':{'newPoolRecords':8,'newNativePrototypes':3,'newMaterials':1,'newTextureAliases':1,'newRasterPixels':False,'newCoordinateInstances':0},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});ledger['mapRuntimeFiles']=[info(f)for f in sorted((arc/'candidate').iterdir())if f.is_file()]
pool['updated']=datetime.now(timezone.utc).isoformat();pool['physicalPack']['blenderLibrary']=info(canon)
audit={'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'newNativePrototypes':3,'newMaterialDefinitions':1,'newTextureAliasBytes':158,'newTexturePixels':False,'allPhysicalPathsHashesDependenciesVerified':True,'canonical':info(canon),'nativePrototypes':n['nativePrototypeCount'],'nativeMaterialDefinitions':n['nativeMaterialDefinitionCount'],'nativeSharedParts':n['nativeSharedParts'],'allCandidateAndAcceptedHistoryBytes':b['allCandidateAndAcceptedHistoryBytes'],'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,arc/f.name)
for f in r.glob('*fidelity_v41*.py'):shutil.copy2(f,arc/f.name)
for f in r.glob('fidelity-v41*.log'):shutil.copy2(f,arc/f.name)
print('V41_PHYSICAL_POOL_REGISTERED',audit,flush=True)
