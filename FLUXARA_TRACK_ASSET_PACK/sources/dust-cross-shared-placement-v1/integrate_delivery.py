from pathlib import Path
import copy,datetime,hashlib,json,shutil,subprocess,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';c=w/'candidate';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';pack=repo/'FLUXARA_TRACK_ASSET_PACK';track='fluxara-user-dust-cross-split-combat';final=r.parent/'fluxara-user-dust-cross-final';device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());installed=app/'data/tracks'/track;p=json.loads((r/'dust-extraction.json').read_text());n=json.loads((w/'native-verification.json').read_text());boundary=json.loads((w/'boundary-verification.json').read_text());info=lambda x:{'path':str(x),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()};prefix='dust-shared-v1-'
backup=w/'before-integration';backup.mkdir(exist_ok=True)
for name,src in [('installed-track',installed),('user-report',final/'report')]:
 dst=backup/name
 if not dst.exists():shutil.copytree(src,dst)
pp=repo/'FLUXARA_TRACK_ASSET_POOL.json';lp=r.parent.parent/(track+'.asset-ledger.json')
for name,src in [('pool.json',pp),('ledger.json',lp)]:
 if not(backup/name).exists():shutil.copy2(src,backup/name)
# The source baseline preserves the original files; only obsolete local copies
# superseded by shared aliases and the engine-generated preview are removed.
for dest in [res/'tracks'/track]:
 for name in [q['original']for q in p['textures']]+['screenshot.png']:
  f=dest/name
  if f.exists():f.unlink()
 for src in c.iterdir():
  if src.is_file():shutil.copy2(src,dest/src.name)
# Respect the installed resource packager's existing global music/texture layout.
installedNames={x.name for x in installed.iterdir()if x.is_file()};updatedNames={'scene.xml','materials.xml','track.xml','dust-cross_scenery.spm','dust-cross_boundary_closures_v1.spm','screenshot.jpg'}
for name in [q['original']for q in p['textures']]+['screenshot.png']:
 f=installed/name
 if f.exists():f.unlink()
for src in c.iterdir():
 if src.is_file()and(src.name in installedNames or src.name in updatedNames):shutil.copy2(src,installed/src.name)
for group,root in [('library',r/'new-library'),('textures',r/'new-textures')]:
 for src in root.iterdir():
  for target in [res/group/src.name,app/'data'/group/src.name]:
   target.parent.mkdir(parents=True,exist_ok=True)
   if src.is_dir():shutil.copytree(src,target,dirs_exist_ok=True)
   else:shutil.copy2(src,target)
shutil.copy2(w/'native/Dust Cross Split Combat.blend',final/'Dust Cross Split Combat.blend');shutil.copytree(c,final/'resources',dirs_exist_ok=True)
for name in [q['original']for q in p['textures']]+['screenshot.png']:
 f=final/'resources'/name
 if f.exists():f.unlink()
for name in ['dust-cross_scenery.spm','dust-cross_boundary_closures_v1.spm']:shutil.copy2(c/name,pack/'models/dust-cross-shared-v1'/name)
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';use=[{'trackId':track,'status':'Integrated coordinate scenery; appearance approved by user; collision traversal checks cancelled by user'}];textures=[]
oldTexture={'dust_cross_cliffs.png':'dust-cross-texture-dust-cross-cliffs','dust_cross_palette.png':'dust-cross-texture-dust-cross-palette'}
for q in p['textures']:
 f=pack/'textures/dust-cross-shared-v1'/q['alias'];textures.append({'id':prefix+'texture-'+q['alias'].split('_')[-1].split('.')[0],'displayName':q['alias'],'kind':'texture','sourceMap':track,'reuseTier':'direct','categories':['canyon'],'canonicalPackPath':str(f),'physicalSourcePath':str(r/'before'/q['original']),'file':info(f),'dependencies':[oldTexture[q['original']]],'runtimeResourceSourcePath':str(res/'textures'/q['alias']),'newImagePixels':False,'uses':use})
tids=[q['id']for q in textures];models=[]
for q in n['reusedCanonicalPrototypes']:
 folder=pack/'models/dust-cross-shared-v1'/q['library'];f=folder/Path(q['model']).name;instances=sum(x['library']==q['library']for x in n['newPlacements'])+q['instances'];models.append({'id':prefix+'model-'+q['library'].split('_')[-1],'displayName':f.name,'kind':'shared-runtime-model','sourceMap':track,'reuseTier':'direct','categories':['canyon'],'canonicalPackPath':str(f),'physicalSourcePath':q['model'],'file':info(f),'dependencies':[q['sourcePoolObjectId']]+tids,'canonicalNativePrototype':str(canon)+'#Object/'+q['canonicalNativePrototype'],'runtimeLibraryPackPath':str(folder),'runtimeResourceSourcePath':str(res/'library'/q['library']),'runtimeLibraryFiles':[info(x)for x in sorted(folder.iterdir())if x.is_file()],'instances':instances,'localBounds':q['localBounds'],'localGeometryPreserved':True,'uses':use})
f=pack/'models/dust-cross-shared-v1/dust-cross_scenery.spm';models.append({'id':prefix+'baked-remainder','kind':'runtime-assembly','sourceMap':track,'reuseTier':'adapt','categories':['canyon'],'displayName':'Dust Cross retained unique scenery','canonicalPackPath':str(f),'physicalSourcePath':str(c/f.name),'file':info(f),'dependencies':['dust-cross-runtime-scenery-v1']+tids,'runtimeResourceSourcePath':str(res/'tracks'/track/f.name),'adaptation':'Removed only repeated geometry extracted into six coordinate libraries; all retained vertex records unchanged.','uses':use})
f=pack/'models/dust-cross-shared-v1/dust-cross_boundary_closures_v1.spm';models.append({'id':'dust-cross-boundary-closures-v1','kind':'map-boundary-collision','sourceMap':track,'reuseTier':'authored','categories':['canyon'],'displayName':'Three missing arena boundary sections','canonicalPackPath':str(f),'physicalSourcePath':str(c/f.name),'nativePackPath':boundary['mapSpecificNativePackPath']+'#Object/DustCross_BoundaryClosures','file':info(f),'dependencies':['dust-cross-texture-metalgrid','dust-cross-surface-fddc2d81dfd9'],'runtimeResourceSourcePath':str(res/'tracks'/track/f.name),'interaction':'static','shape':'exact','mapSpecificGameplayBoundary':True,'triangles':36,'newTextures':False,'uses':use})
pool=json.loads(pp.read_text());assets=models+textures
for key,values in [('objects',models),('textures',textures),('assets',assets)]:
 byid={q['id']:q for q in pool[key]}
 for q in values:byid[q['id']]=q
 pool[key]=list(byid.values())
pool['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
ledger=json.loads(lp.read_text());oldids={q['id']for q in ledger['assets']};ledger['assets']+=copy.deepcopy([q for q in assets if q['id']not in oldids]);ledger['coordinateReusePhase']={'assets':assets,'existingCoordinateParts':572,'newTreeInstances':18,'newTreeCoordinateParts':108,'totalCoordinateParts':680,'placements':p['placements']+n['newPlacements'],'grounding':n['grounding'],'canonicalNativeReused':n['reusedCanonicalPrototypes'],'finalBlend':str(final/'Dust Cross Split Combat.blend'),'approvedStyle':'Rest of arena approved by user on 2026-10-02; frozen. Only perimeter gaps closed afterward.','boundaryCorrection':boundary,'runtimeValidationOwner':'user','assistantRuntimeCollisionChecksCancelled':True,'newBuildPerformed':False};ledger['finalBlend']=str(final/'Dust Cross Split Combat.blend');lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
shared=sum(x.stat().st_size for group in [r/'new-library',r/'new-textures']for x in group.rglob('*')if x.is_file());own=sum(x.stat().st_size for x in c.iterdir()if x.is_file());weights={'originalBytes':p['sourceBytes'],'candidateOwnBytes':own,'newSharedGameBytes':shared,'candidateTotalBytes':own+shared,'savingBytes':p['sourceBytes']-own-shared,'existingCoordinateParts':572,'additionalTrees':18,'newCoordinateParts':108,'totalNewPoolPlacements':680,'uniqueExportedModels':6,'boundaryNewModelBytes':1607,'boundaryNewTriangles':36,'newRasterPixels':False,'previewCampaignThumbnailPending':True};(w/'weight-verification.json').write_text(json.dumps(weights,indent=2));integration={'trackId':track,'sourceTrack':str(res/'tracks'/track),'installedTrack':str(installed),'installedApp':str(app),'sourceNative':str(final/'Dust Cross Split Combat.blend'),'native':info(final/'Dust Cross Split Combat.blend'),'sourceCopies':len(list(c.iterdir())),'sharedLibrariesCopied':6,'sharedTextureAliasesCopied':2,'boundary':boundary,'scriptedContactTestsCancelledByUser':True,'productionScriptingAsAdded':False,'newBuildPerformed':False,'installedPackagingGlobalMusicAndTextureLayoutRetained':True};(w/'integration.json').write_text(json.dumps(integration,indent=2));(w/'asset-registration.json').write_text(json.dumps({'assets':assets,'mapSpecificBoundaryNative':boundary['mapSpecificNativePackPath'],'canonicalNativeLibraryUnchanged':True},ensure_ascii=False,indent=2));print('DUST_SCENERY_AND_CLOSED_BOUNDARY_SAVED_SOURCE_SIMULATOR_FINAL',weights,flush=True)
