from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v10b';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v10b';mod=pack/'models/volcano-remake-fidelity-v10b';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v9/candidate-asset-ledger.json').read_text());assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==4;assert len(json.loads((w/'final-blend-verification.json').read_text())['newCliffPrototypes'])==4;assert(w/'canonical-bindings-verification.json').is_file()
if not(w/'pool-before-v10b.json').exists():shutil.copy2(pf,w/'pool-before-v10b.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
sources.mkdir(exist_ok=True)
for name in ['restore_fidelity_v10b_stone.py','verify_fidelity_v10b.py','audit_fidelity_v10b_budget.py','finalize_fidelity_v10b.py','verify_fidelity_v10b_native.py','register_fidelity_v10b_canonical.py','verify_fidelity_v10b_canonical.py','capture_fidelity_v10b_drive.py','capture_fidelity_v10b_inspection.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
 if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
for folder in ['screenshots','candidate','native']:
 if(w/folder).is_dir():shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
usage=[{'trackId':'fluxara-user-volcano-remake','status':'V10B textured cliffs restored on user request; smoother decorative normals, red roofs retained. Course and collision exact. Overall fidelity unfinished. Production and preview unchanged'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['rock','lava'],'uses':usage};new=[]
for q in a['newPrototypes']:
 deps=[next(m['id']for m in ledger['materials']if m.get('name')==name)for name in q['materials']]
 obj={**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':deps,'reason':'Decorative cliff buffer with original stone UVs/texture restored; smoother packed normals retained. Original vertex positions, indices, bounds and axes.'};new.append(obj)
 source=Path(q['sourceModel']);stored=mod/source.name;runtime={**base,'id':'volcano-fidelity-v10b-runtime-'+source.stem,'displayName':source.name,'kind':'map-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),'physicalSourcePath':str(r/'fidelity-v9/candidate'/source.name),'file':info(stored),'dependencies':deps,'sourceBuffer':q['sourceBuffer'],'protectedGeometryScope':'Full map model includes immutable original course/collision; canonical reusable prototype contains only the decorative cliff buffer.','adaptationScript':str(sources/'restore_fidelity_v10b_stone.py')};new.append(runtime)
pool['objects']=[q for q in pool['objects']if not q['id'].startswith('volcano-fidelity-v10b-')]+new;ledger['objects']+=new;ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id']for key in ['objects','materials','textures']for q in pool[key]];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V10B textured cliffs and V9 red roof towers','status':'Current isolated candidate. Stone texture restored on user request, smooth decorative normals retained; vertex positions and collision exact. Castle walls, silhouettes, lava and smoke unfinished.','finalBlend':a['finalBlend'],'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'deltaAssetCounts':{'objects':8,'materials':0,'textures':0},'productionIntegrated':False,'nativeSharedParts':len(a['nativeSharedInstances']),'approval':'User preferred textured stone; no final approval for whole map'})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['mapRuntimeFiles']=[info(p)for p in(sources/'candidate').iterdir()if p.is_file()];ledger['reusedAssetIds']=[q['id']for q in ledger['assets']if not q['id'].startswith('volcano-fidelity-v10b-')]
for q in ledger['assets']:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':8,'newNativePrototypes':4,'newMaterials':0,'newTextures':0,'newImagePixels':False,'retainedAuthoringAssets':len(ledger['assets']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V10B_POOL_REGISTERED',audit)
