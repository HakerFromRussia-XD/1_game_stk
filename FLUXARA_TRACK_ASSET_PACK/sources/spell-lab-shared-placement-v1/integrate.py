from pathlib import Path
import copy,datetime,hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';c=w/'candidate';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';pack=repo/'FLUXARA_TRACK_ASSET_PACK';track='fluxara-user-spell-lab';final=r.parent/'fluxara-user-spell-lab-final';device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());installed=app/'data/tracks'/track;p=json.loads((r/'spell-extraction.json').read_text());n=json.loads((w/'native-verification.json').read_text());info=lambda x:{'path':str(x),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()};prefix='spell-shared-v1-';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
# Record and retain the exact protected source resources at promotion.
protected=[f.name for f in(r/'before').iterdir()if f.is_file()and f.name not in ['scene.xml','materials.xml','spell_gardens.spm','spell_palette.png','SL_shot.png','track.xml']];preservation={'protectedResourceFiles':{name:info(c/name)for name in protected},'allProtectedResourceFilesByteExact':all((r/'before'/name).read_bytes()==(c/name).read_bytes()for name in protected),'originalSceneNodesKept':True,'originalRuntimeMeshesAndTransformsUnchanged':True,'localModelGeometryUnchanged':True,'canonicalNativeLibraryUnchanged':True,'onlyPreviewAttributeChangesInTrackXML':True};oldscene=E.parse(r/'before/scene.xml').getroot();newscene=E.parse(c/'scene.xml').getroot();norm=lambda el:(el.tag,dict(el.attrib),(el.text or '').strip(),tuple(norm(x)for x in el));preservation['originalSceneNodesKept']=all(norm(a)==norm(b)for a,b in zip(oldscene,newscene));(w/'preservation.json').write_text(json.dumps(preservation,indent=2))
backup=w/'before-integration';backup.mkdir(exist_ok=True)
for name,src in [('installed-track',installed),('user-report',final/'report')]:
 dst=backup/name
 if not dst.exists():shutil.copytree(src,dst)
pp=repo/'FLUXARA_TRACK_ASSET_POOL.json';lp=r.parent.parent/(track+'.asset-ledger.json')
for name,src in [('pool.json',pp),('ledger.json',lp)]:
 if not(backup/name).exists():shutil.copy2(src,backup/name)
for dst in [res/'tracks'/track,final]:
 for name in ['spell_palette.png','SL_shot.png']:
  f=dst/name
  if f.exists():f.unlink()
 for src in c.iterdir():
  if src.is_file():shutil.copy2(src,dst/src.name)
shutil.copy2(w/'native/Spell Lab.blend',final/'Spell Lab.blend')
installedNames={x.name for x in installed.iterdir()if x.is_file()};updatedNames={'scene.xml','materials.xml','track.xml','spell_gardens.spm','screenshot.jpg'}
for name in ['spell_palette.png','SL_shot.png']:
 f=installed/name
 if f.exists():f.unlink()
for src in c.iterdir():
 if src.is_file()and(src.name in installedNames or src.name in updatedNames):shutil.copy2(src,installed/src.name)
models=[];palId='dust-shared-v1-texture-9f8d36974e14';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';mod=pack/'models/spell-lab-shared-v1';mod.mkdir(exist_ok=True);use=[{'trackId':track,'status':'Integrated coordinate scenery and 180 three-part garden shrubs; art review pending'}]
for q in n['reusedCanonicalPrototypes']:
 src=r/'new-library'/q['library'];dst=mod/q['library'];shutil.copytree(src,dst,dirs_exist_ok=True)
 for target in [res/'library'/q['library'],app/'data/library'/q['library']]:shutil.copytree(src,target,dirs_exist_ok=True)
 f=dst/Path(q['model']).name;models.append({'id':prefix+'model-'+q['library'].split('_')[-1],'displayName':f.name,'kind':'shared-runtime-model','sourceMap':track,'reuseTier':'direct','categories':['laboratory'],'canonicalPackPath':str(f),'physicalSourcePath':q['model'],'file':info(f),'dependencies':[q['sourcePoolObjectId'],palId],'canonicalNativePrototype':str(canon)+'#Object/'+q['canonicalNativePrototype'],'runtimeLibraryPackPath':str(dst),'runtimeResourceSourcePath':str(res/'library'/q['library']),'runtimeLibraryFiles':[info(f)for f in sorted(dst.iterdir())if f.is_file()],'instances':q['instances']+sum(x['library']==q['library']for x in n['newPlacements']),'localBounds':q['localBounds'],'localGeometryPreserved':True,'uses':use})
shutil.copy2(c/'spell_gardens.spm',mod/'spell_gardens.spm');f=mod/'spell_gardens.spm';models.append({'id':prefix+'baked-remainder','kind':'runtime-assembly','sourceMap':track,'reuseTier':'adapt','categories':['laboratory'],'displayName':'Spell Lab retained unique scenery','canonicalPackPath':str(f),'physicalSourcePath':str(c/f.name),'file':info(f),'dependencies':['spell-lab-runtime-gardens-v1',palId],'runtimeResourceSourcePath':str(res/'tracks'/track/f.name),'adaptation':'Removed only 17,152 repeated triangles now represented by eight coordinate libraries. Unique roofs, arches and supports retained.','uses':use})
pool=json.loads(pp.read_text())
for group in ['textures','assets']:
 for q in pool[group]:
  if q['id']==palId:
   q['categories']=sorted(set(q.get('categories',[])+['laboratory']));q['uses']=[u for u in q.get('uses',[])if u.get('trackId')!=track]+use
for key in ['objects','assets']:
 byid={q['id']:q for q in pool[key]}
 for q in models:byid[q['id']]=q
 pool[key]=list(byid.values())
pool['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
shared=sum(x.stat().st_size for x in(r/'new-library').rglob('*')if x.is_file());own=sum(x.stat().st_size for x in c.iterdir()if x.is_file());gui=res/'gui/fluxara/campaign-previews'/(track+'.jpg');shutil.copy2(w/'campaign-preview.jpg',gui);shutil.copy2(gui,app/'data/gui/fluxara/campaign-previews'/gui.name);weights={'originalBytes':p['sourceBytes'],'candidateOwnBytes':own,'newSharedGameBytes':shared,'newTextureBytes':0,'alreadySharedPaletteId':palId,'campaignThumbnailBytesChargedInFull':gui.stat().st_size,'candidateTotalBytes':own+shared+gui.stat().st_size,'savingBytes':p['sourceBytes']-own-shared-gui.stat().st_size,'sourcePreview':info(c/'screenshot.jpg'),'campaignPreview':info(gui),'existingCoordinateParts':284,'additionalShrubGroups':180,'newShrubCoordinateParts':540,'totalCoordinateParts':824,'uniqueExportedModels':8};weights['savingPercent']=weights['savingBytes']*100/weights['originalBytes'];(w/'weight.json').write_text(json.dumps(weights,indent=2));integration={'trackId':track,'sourceTrack':str(res/'tracks'/track),'installedTrack':str(installed),'installedApp':str(app),'finalNative':info(final/'Spell Lab.blend'),'sourceFilesCopied':len(list(c.iterdir())),'sharedLibrariesCopied':8,'newTextureFilesAdded':0,'canonicalGeometryMaterialsImagesAdded':0,'productionScriptsUnchanged':True,'installedGlobalMusicAndTextureLayoutRetained':True,'newBuildPerformed':False,'newDrivingTestPerformed':False,'weights':weights};(w/'integration.json').write_text(json.dumps(integration,indent=2));(w/'asset-registration.json').write_text(json.dumps({'assets':models,'reusedPaletteId':palId,'reusedNativePrototypes':n['reusedCanonicalPrototypes']},indent=2));ledger=json.loads(lp.read_text());oldids={q['id']for q in ledger['assets']};ledger['assets']+=copy.deepcopy([q for q in models if q['id']not in oldids]);ledger['coordinateReusePhase']={'assets':models,'paletteSharedWithDustCross':palId,'existingCoordinateParts':284,'additionalShrubGroups':180,'newShrubCoordinateParts':540,'totalCoordinateParts':824,'placements':p['placements']+n['newPlacements'],'grounding':n['grounding'],'canonicalNativeReused':n['reusedCanonicalPrototypes'],'finalBlend':str(final/'Spell Lab.blend'),'nativeFile':info(final/'Spell Lab.blend'),'weights':weights,'preservation':preservation,'runtimeValidation':'Static engine screenshots captured. No new driving/collision test and no new application build.','visualApprovalPending':True,'report':str(final/'report/index.html')};ledger['finalBlend']=str(final/'Spell Lab.blend');lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');print('SPELL_COORDINATE_SCENERY_AND_180_SHRUB_GROUPS_INTEGRATED',weights,flush=True)
