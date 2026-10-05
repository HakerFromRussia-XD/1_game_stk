from pathlib import Path
import copy,datetime,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent;root=r.parents[2];repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';pack=repo/'FLUXARA_TRACK_ASSET_PACK';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container','3B2F19DC-4F76-4F61-9F8D-D5E914A6D123','io.fluxara.drift','app'],text=True).strip());p=json.loads((r/'candidate.json').read_text());native=json.loads((r/'native.json').read_text());pp=repo/'FLUXARA_TRACK_ASSET_POOL.json';lp=root/'fluxara-user-lap-catch.asset-ledger.json';pool=json.loads(pp.read_text());ledger=json.loads(lp.read_text());before=r/'before';before.mkdir(exist_ok=True)
for name,file in [('pool.json',pp),('ledger.json',lp)]:
 if not(before/name).exists():shutil.copy2(file,before/name)
info=lambda f:{'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};mod=pack/'models/lap-texture-weight-v1';mod.mkdir(exist_ok=True);models=[]
for source in(r/'new-library').iterdir():
 dest=mod/source.name;shutil.copytree(source,dest,dirs_exist_ok=True)
 for base in [res/'library',app/'data/library']:shutil.copytree(source,base/source.name,dirs_exist_ok=True)
 for model in dest.glob('*.spm'):
  models.append({'id':'lap-weight-v1-model-'+source.name,'kind':'shared-runtime-model','displayName':source.name,'sourceMap':'fluxara-user-lap-catch','reuseTier':'adapt','categories':['forest'],'canonicalPackPath':str(model),'physicalSourcePath':str(res/'library'/('fluxara_driftlib_round_bush_green_v2'if'bush'in source.name else 'fluxara_driftlib_round_tree_green_v2')/model.name),'file':info(model),'dependencies':['lap-weight-v1-leaf-72'],'runtimeLibraryFiles':[info(f)for f in dest.iterdir()if f.is_file()],'runtimeResourceSourcePath':str(res/'library'/source.name),'adaptation':'Same geometry, UV, normals, colours and indices; only the diffuse filename selects a reduced-resolution export.','uses':[{'trackId':'fluxara-user-lap-catch','status':'Integrated into three original low-byte object families'}]})
for source in(r/'wrappers').iterdir():
 old=res/'library'/source.name
 if not(before/source.name).exists():shutil.copytree(old,before/source.name)
 for base in [res/'library',app/'data/library']:shutil.copytree(source,base/source.name,dirs_exist_ok=True)
 for key in ['objects','assets']:
  for row in pool[key]:
   oldpath=row.get('runtimeResourceSourcePath','')
   if oldpath==str(old)and row.get('runtimeLibraryFiles'):
    row['runtimeLibraryFiles']=[info(f)for f in old.iterdir()if f.is_file()]
leaf=pack/'textures/lap-texture-weight-v1/fluxara_lc_leaf_72.png'
for base in [res/'textures',app/'data/textures']:shutil.copy2(leaf,base/leaf.name)
tex={'id':'lap-weight-v1-leaf-72','kind':'texture','displayName':leaf.name,'sourceMap':'fluxara-user-lap-catch','reuseTier':'adapt','categories':['forest'],'canonicalPackPath':str(leaf),'physicalSourcePath':str(res/'textures/fluxara_circuit_leaf_v2.png'),'file':info(leaf),'runtimeResourceSourcePath':str(res/'textures'/leaf.name),'resolution':[72,72],'adaptation':'Technical resize of existing foliage artwork for the strict original object-family byte budget. Higher-resolution source retained and used by other objects.','uses':[{'trackId':'fluxara-user-lap-catch','status':'Integrated once as one shared image for the three object families'}]}
parts=[]
for q in native['prototypes']:
 parents=[a['id']for a in pool['objects']if a.get('canonicalPackPath','').endswith('#Object/'+q['sourcePrototype'])];parts.append({'id':q['id'],'kind':'shared-native-part','displayName':q['name'],'sourceMap':'fluxara-user-lap-catch','reuseTier':'adapt','categories':['forest'],'canonicalPackPath':native['canonicalPath']+'#Object/'+q['name'],'physicalSourcePath':native['canonicalPath']+'#Object/'+q['sourcePrototype'],'dependencies':parents+['lap-weight-v1-leaf-72'],'localGeometryUVUnchanged':True,'shapeHash':q['shapeHash'],'runtimeLibrary':q['runtimeLibrary'],'uses':[{'trackId':'fluxara-user-lap-catch','status':'Integrated lightweight texture variant'}]})
for key,values in [('objects',models+parts),('textures',[tex]),('assets',models+parts+[tex])]:
 byid={q['id']:q for q in pool[key]}
 for q in values:byid[q['id']]=q
 pool[key]=list(byid.values())
pool['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();pool['canonicalAuthoringLibraryRevision']={'file':info(Path(native['canonicalPath'])),'addedNativeParts':3,'sourceAssetsPreserved':True};pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
ids={q['id']for q in ledger['assets']};ledger['assets']+=copy.deepcopy([q for q in models+parts+[tex]if q['id']not in ids]);newBytes=sum(f.stat().st_size for f in(r/'new-library').rglob('*')if f.is_file())+leaf.stat().st_size;proof={'status':'Integrated into source resources, installed simulator resources, final Blender and physical shared asset pack','candidateWeights':p['weights'],'newSharedGameBytes':newBytes,'newGeometryCreated':False,'newTextureFileCount':1,'changedNativeParts':native['changedNativeParts'],'native':native,'assets':models+parts+[tex],'mainSceneXMLUnchanged':True,'newRuntimeTestPerformed':False,'newBuildPerformed':False};ledger['textureWeightFix']=proof;lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(r/'integration.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print('LAP_LIGHTWEIGHT_EXPORTS_INTEGRATED',newBytes,native['changedNativeParts'],flush=True)
