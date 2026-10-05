from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v10';mod=pack/'models/volcano-remake-fidelity-v10';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v9/candidate-asset-ledger.json').read_text());assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==4;assert len(json.loads((w/'final-blend-verification.json').read_text())['newCliffPrototypes'])==4;assert(w/'canonical-bindings-verification.json').is_file()
if not(w/'pool-before-v10.json').exists():shutil.copy2(pf,w/'pool-before-v10.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
sources.mkdir(exist_ok=True)
for name in ['build_fidelity_v10_cliffs.py','verify_fidelity_v10.py','audit_fidelity_v10_budget.py','finalize_fidelity_v10.py','verify_fidelity_v10_native.py','register_fidelity_v10_canonical.py','verify_fidelity_v10_canonical.py','capture_fidelity_v10_drive.py','capture_fidelity_v10_inspection.py','update_fidelity_v10_native_material_text.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
 if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
for folder in ['screenshots','candidate','native','iterations']:
 if(w/folder).is_dir():shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
usage=[{'trackId':'fluxara-user-volcano-remake','status':'V10 rejected by user: stone texture preferred. Historical palette experiment only; restored textured variant V10B is current. Production unchanged'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['rock','lava'],'uses':usage};mat=next(q for q in a['materials']if q['id']=='volcano-fidelity-v10-cliff-material');texture=next(q for q in ledger['textures']if q.get('displayName')=='vr_moss_palette.jpg'and Path(q['canonicalPackPath']).read_bytes()==(w/'candidate/vr_moss_palette.jpg').read_bytes());mid=mat['id'];material={**base,**mat,'kind':'material','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+mat['name'],'physicalSourcePath':a['visualLibrary'],'dependencies':[texture['id']],'reason':'Existing stone cell of moss palette used as cliff surface; no new pixel or runtime texture files.'};new=[]
for q in a['newPrototypes']:
 obj={**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':[mid],'reason':'Extracted decorative cliff buffer with original local vertex positions, indices, bounds and axes; UV and normals adapted.'};new.append(obj)
 source=Path(q['sourceModel']);stored=mod/source.name;runtime={**base,'id':'volcano-fidelity-v10-runtime-'+source.stem,'displayName':source.name,'kind':'map-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(r/'fidelity-v9/candidate'/source.name),'file':info(stored),'dependencies':[mid],'sourceBuffer':q['sourceBuffer'],'protectedGeometryScope':'Full map model includes immutable course or original volcano collision; reusable canonical prototype contains only the decorative cliff buffer.','adaptationScript':str(sources/'build_fidelity_v10_cliffs.py')};new.append(runtime)
pool['objects']=[q for q in pool['objects']if not q['id'].startswith('volcano-fidelity-v10-')]+new;pool['materials']=[q for q in pool['materials']if not q['id'].startswith('volcano-fidelity-v10-')]+[material];ledger['objects']+=new;ledger['materials'].append(material);ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id']for key in ['objects','materials','textures']for q in pool[key]];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V10 smoother palette cliffs and V9 red roof towers','status':'Rejected by user: stone texture preferred; palette experiment retained only in history. V10B restores texture.','finalBlend':a['finalBlend'],'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'deltaAssetCounts':{'objects':8,'materials':1,'textures':0},'productionIntegrated':False,'nativeSharedParts':len(a['nativeSharedInstances']),'approval':'Rejected by user on 2026-10-01: С текстурой камня было лучше'})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(p)for p in(sources/'candidate').iterdir()if p.is_file()];ledger['reusedAssetIds']=[q['id']for q in ledger['assets']if not q['id'].startswith('volcano-fidelity-v10-')]
for q in ledger['assets']:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':8,'newNativePrototypes':4,'newMaterials':1,'newTextures':0,'newImagePixels':False,'retainedAuthoringAssets':len(ledger['assets']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V10_POOL_REGISTERED',audit)
