from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v36/candidate-asset-ledger.json').read_text());a=json.loads((w/'asset-registration.json').read_text());n=json.loads((w/'final-blend-verification.json').read_text());b=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());arc=pack/'sources/volcano-remake-fidelity-v37';arc.mkdir(exist_ok=True)
assert run['naturalFinishObserved']and run['temporaryCopiedResourcesCleanupVerified'];assert n['allPreviousNativeMeshGeometryUVNormalsColorsMaterialsExactV36']==726 and n['newModelsMaterialsTextures']==0;assert 'V37_NATIVE_REOPEN_AND_SHARED_GEOMETRY_VERIFIED'in(w/'native-finalize-corrected.log').read_text()
def info(f):
 f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';assert info(canon)['sha256']==n['canonicalByteHashExactV36'];assert pool['physicalPack']['blenderLibrary']==info(canon)
if not(w/'pool-before-v37.json').exists():shutil.copy2(pf,w/'pool-before-v37.json')
counts={'volcano-fidelity-v32-sealed-grasscap':82,'volcano-fidelity-v32-sealed-grasscap-runtime':82,'volcano-fidelity-v18-green-mound':52,'volcano-fidelity-v18-runtime-green-mound':52,'dp-v2-dpv2-dp-roundedtree-prototype':88}
for target in [pool,ledger]:
 for q in target['objects']:
  if q['id']in counts:
   uses=q.setdefault('uses',[]);uses[:]=[v for v in uses if not(isinstance(v,dict)and v.get('candidate')=='V37')];uses.append({'trackId':'fluxara-user-volcano-remake','candidate':'V37','instances':counts[q['id']],'status':'Existing physical source reused; grass/stone interface anchored at actual open boundary, existing vegetation lifted and64trees20mounds added by coordinates. Full source/native/natural-lap check; overall reference and production integration unfinished.'})
 target['assets']=target['objects']+target['materials']+target['textures']
ids=[q['id']for q in pool['assets']];assert len(ids)==len(set(ids))==4174
for q in ledger['assets']:
 assert q['id']in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(q['file']['path'])==q['file'],q['id']
 for field in ['runtimeFiles','runtimeLibraryFiles']:
  for f in q.get(field,[]):assert info(f['path'])==f,q['id']
for folder in ['candidate','native','screenshots','rejected-interface-draft']:shutil.copytree(w/folder,arc/folder,dirs_exist_ok=True)
ledger.update({'candidate':'V37 thicker shared grass rims and84background coordinate props','status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':514,'preservation':b,'budget':b,'runtimeValidation':run,'deltaAssetCounts':{'newPoolObjectRecords':0,'newNativePrototypes':0,'newMaterials':0,'newTextures':0,'newGameAssetPayloadBytes':0,'newCoordinateInstances':84},'productionIntegrated':False,'referenceAcceptance':False,'newImagePixels':False});ledger['mapRuntimeFiles']=[info(f)for f in sorted((arc/'candidate').iterdir())if f.is_file()];pool['updated']=datetime.now(timezone.utc).isoformat()
audit={'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),'newObjectsModelsTexturesMaterials':0,'newGameAssetPayloadBytes':0,'newCoordinateInstances':84,'allPhysicalPathsHashesDependenciesVerified':True,'canonicalHashUnchanged':info(canon),'nativePrototypes':46,'nativeMaterialDefinitions':99,'nativeSharedParts':514,'allCandidateAndAcceptedHistoryBytes':b['allCandidateAndAcceptedHistoryBytes'],'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for f in w.glob('*.json'):
 if not f.name.startswith('pool-before'):shutil.copy2(f,arc/f.name)
for f in r.glob('*fidelity_v37*.py'):shutil.copy2(f,arc/f.name)
for f in w.glob('*.log'):shutil.copy2(f,arc/f.name)
print('V37_SHARED_INSTANCE_REUSE_REGISTERED',audit,flush=True)
