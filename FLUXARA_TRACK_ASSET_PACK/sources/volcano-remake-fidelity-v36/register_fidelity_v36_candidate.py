from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v36';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';res=repo/'iosApp/FluxaraResources';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v35/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());pre=json.loads((w/'visual-batch-preflight.json').read_text());budget=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());native=json.loads((w/'final-blend-verification.json').read_text());canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';archive=pack/'sources/volcano-remake-fidelity-v36';archive.mkdir(exist_ok=True)
assert run['naturalFinishObserved']and run['temporaryCopiedResourcesCleanupVerified']and not native['canonicalPending'];assert 'V36_NATIVE_CANONICAL_PIPELINE_COMPLETE'in(w/'native-finalize.log').read_text()
def info(f):
 f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
if not(w/'pool-before-v36.json').exists():shutil.copy2(pf,w/'pool-before-v36.json')
storedtex=pack/'textures/volcano-remake-fidelity-v36';storedtex.mkdir(exist_ok=True);mod=pack/'models/volcano-remake-fidelity-v36';newtex=[];newmat=[];newobj=[]
def prior_texture(source):
 source=Path(source);sha=info(source)['sha256'];matches=[q for q in pool['textures']if q.get('file',{}).get('sha256')==sha];assert matches,source
 exact=[q for q in matches if q.get('canonicalPackPath','').split('#')[0]==str(source)];return (exact or matches)[0]['id']
uses=[{'trackId':'fluxara-user-volcano-remake','candidate':'V36','status':'Source/native/canonical and natural full lap verified working draft; full reference and production integration unfinished.'}]
for f in sorted((w/'shared-textures').iterdir()):
 target=storedtex/f.name;shutil.copy2(f,target);src=next((q['source']['path']for q in pre['reusedSkyTextureSources']if Path(q['alias']['path']).name==f.name),str(r/'fidelity-v35/candidate/blackrock_lava.jpg'))
 ident='volcano-fidelity-v36-texture-'+f.stem;row={'id':ident,'displayName':f.name,'kind':'texture','sourceMap':'fluxara-user-volcano-remake','reuseTier':'direct','canonicalPackPath':str(target),'physicalSourcePath':src,'file':info(target),'dependencies':[prior_texture(src)],'uses':copy.deepcopy(uses),'newImagePixels':False,'runtimePackagedPath':str(res/'textures'/f.name),'productionIntegrated':False};newtex.append(row)
 dst=res/'textures'/f.name
 if dst.exists():assert dst.read_bytes()==f.read_bytes()
 else:shutil.copy2(f,dst)
 a['textures'][f.name]['packPath']=str(target)
gloss=Path(pre['newMudGlossAlias']['path']);target=storedtex/gloss.name;shutil.copy2(gloss,target);source=Path(pre['mudSourceLibrary'])/'fluxara_drift_mudpot_a_gloss.png';newtex.append({'id':'volcano-fidelity-v36-mud-gloss-texture','displayName':gloss.name,'kind':'texture','sourceMap':'fluxara-user-volcano-remake','reuseTier':'direct','canonicalPackPath':str(target),'physicalSourcePath':str(source),'file':info(target),'dependencies':[prior_texture(source)],'uses':copy.deepcopy(uses),'newImagePixels':False,'runtimePackagedPath':str(res/'library/fluxara_driftlib_volcano_mudpot_v36'/gloss.name),'productionIntegrated':False})
texids={q['displayName']:q['id']for q in newtex};texids.update({q.get('displayName',Path(q['canonicalPackPath']).name):q['id']for q in ledger['textures']if q.get('displayName',Path(q['canonicalPackPath']).name)not in texids})
for row in a['newMaterialVariants']:
 source=next(q['id']for q in ledger['materials']if q.get('name',q.get('displayName'))==row['sourceMaterial']);newmat.append({**row,'displayName':row['name'],'kind':'material','sourceMap':'fluxara-user-volcano-remake','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(a['visualLibrary']),'dependencies':[source]+[texids[n]for n in row['textures']],'uses':copy.deepcopy(uses),'productionIntegrated':False})
matids={q['name']:q['id']for q in newmat};matids.update({q.get('name',q.get('displayName')):q['id']for q in ledger['materials']if q.get('name',q.get('displayName'))not in matids})
for row in a['newPrototypes']:
 newobj.append({**row,'displayName':row['name'],'kind':'visual-object','sourceMap':'fluxara-user-volcano-remake','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(a['visualLibrary']),'dependencies':[matids[n]for n in row['materials']]+([row['sourcePoolObjectId']]if row.get('sourcePoolObjectId')else ['volcano-fidelity-v15-castle-roof']),'uses':copy.deepcopy(uses),'productionIntegrated':False})
for lib in sorted((w/'shared-runtime').iterdir()):
 dst=res/'library'/lib.name
 if dst.exists():assert all((dst/f.name).read_bytes()==f.read_bytes()for f in lib.iterdir()if f.is_file())
 else:shutil.copytree(lib,dst)
 storage=mod/lib.name;shutil.copytree(lib,storage,dirs_exist_ok=True);ident='volcano-fidelity-v36-runtime-'+lib.name;models=list(storage.glob('*.spm'));deps=[q['id']for q in newobj if q.get('sourceModel')and Path(q['sourceModel']).parent.name==lib.name]+[texids[Path(pre['newMudTextureAlias']['path']).name],'volcano-fidelity-v36-mud-gloss-texture']if 'mudpot'in lib.name else [q['id']for q in newobj if q.get('sourceModel')and Path(q['sourceModel']).parent.name==lib.name]+[texids['fluxara_castle_brick_v15.jpg'],'volcano-fidelity-v15-castle-body']
 newobj.append({'id':ident,'displayName':lib.name,'kind':'runtime-library','sourceMap':'fluxara-user-volcano-remake','reuseTier':'adapt','canonicalPackPath':str(storage/'node.xml'),'physicalSourcePath':str(lib),'file':info(storage/'node.xml'),'runtimeLibraryFiles':[info(f)for f in sorted(dst.iterdir())if f.is_file()],'dependencies':deps,'uses':copy.deepcopy(uses),'productionIntegrated':False,'sourceModelAndUsedTextureWeightVerification':{'before':pre['mudModelsAndUsedTexturesBytesBefore'],'after':pre['mudModelsAndUsedTexturesBytesAfter']}if'mudpot'in lib.name else {'before':pre['sourceRoofModel']['bytes'],'after':pre['newRoofModel']['bytes'],'sameUsedTexture':'fluxara_castle_brick_v15.jpg'}})
newids={q['id']for q in newtex+newmat+newobj}
for target in [pool,ledger]:
 for key,new in [('textures',newtex),('materials',newmat),('objects',newobj)]:target[key]=[q for q in target[key]if q['id']not in newids]+copy.deepcopy(new)
 target['assets']=target['objects']+target['materials']+target['textures']
ci=info(canon)
def refresh(obj):
 if isinstance(obj,dict):
  if obj.get('path')==str(canon)and 'sha256'in obj:obj.update(ci)
  for value in obj.values():refresh(value)
 elif isinstance(obj,list):
  for value in obj:refresh(value)
refresh(pool);refresh(ledger);pool['physicalPack']['blenderLibrary']=ci;pool['updated']=datetime.now(timezone.utc).isoformat();ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids));assert all(d in ids for q in ledger['assets']for d in q.get('dependencies',[]))
for q in ledger['assets']:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeFiles','runtimeLibraryFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
ledger.update({'candidate':'V36 grounded plants, lava material and roof variants','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':len(a['nativeSharedInstances']),'preservation':budget,'budget':budget,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjectsAndRuntimeRecords':len(newobj),'newMaterials':len(newmat),'newTextureAliases':len(newtex),'newImagePixels':0,'newSharedRuntimeAllFilesBytes':budget['newSharedRuntimeAllFilesBytes'],'newSharedGlobalAliasesAllFilesBytes':budget['newSharedGlobalAliasesAllFilesBytes']},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False})
for folder in ['candidate','native','screenshots','shared-runtime','shared-textures']:shutil.copytree(w/folder,archive/folder,dirs_exist_ok=True)
ledger['mapRuntimeFiles']=[info(f)for f in sorted((archive/'candidate').iterdir())if f.is_file()]
audit={'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'newObjectsAndRuntimeRecords':len(newobj),'newMaterials':len(newmat),'newTextureAliases':len(newtex),'newImagePixels':0,'allPhysicalPathsHashesDependenciesVerified':True,'canonical':ci,'nativePrototypes':len(a['objects']),'nativeMaterialDefinitions':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'originalStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False,'allCandidateAndAcceptedHistoryBytes':budget['allCandidateAndAcceptedHistoryBytes']}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'asset-registration.json').write_text(json.dumps(a,indent=2));(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,archive/f.name)
for f in r.glob('*fidelity_v36*.py'):shutil.copy2(f,archive/f.name)
for f in w.glob('*.log'):shutil.copy2(f,archive/f.name)
ski=r.parent.parent/'fluxara-user-ski-dash.asset-ledger.json'
if ski.exists():
 old=json.loads(ski.read_text());new=copy.deepcopy(old);refresh(new)
 if old!=new:(w/'ski-dash-ledger-before-canonical-refresh.json').write_text(json.dumps(old,indent=2));ski.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
print('V36_CANDIDATE_POOL_REGISTERED',audit,flush=True)
