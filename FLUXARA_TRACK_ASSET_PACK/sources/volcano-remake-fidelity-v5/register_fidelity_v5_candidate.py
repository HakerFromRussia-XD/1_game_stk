from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v5';mod=pack/'models/volcano-remake-fidelity-v5';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend'
a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v4e/candidate-asset-ledger.json').read_text());assert len(a['objects'])==18;assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==3;assert (w/'canonical-bindings-verification.json').is_file();assert len(json.loads((w/'final-blend-verification.json').read_text())['newCloudPrototypes'])==3
if not (w/'pool-before-v5.json').exists():shutil.copy2(pf,w/'pool-before-v5.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ['fidelity_v5_smoke.py','weld_v5_smoke.py','finalize_fidelity_v5.py','verify_fidelity_v5.py','verify_fidelity_v5_native.py','register_fidelity_v5_canonical.py','verify_fidelity_v5_canonical.py','capture_fidelity_v5_drive.py','capture_fidelity_v5_inspection.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
 if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
shutil.copytree(w/'screenshots',sources/'screenshots',dirs_exist_ok=True)
usage=[{'trackId':'fluxara-user-volcano-remake','status':'Rejected opaque V5; no production integration'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':usage};mmap={q['name']:q['id']for q in ledger['materials']if q.get('name')};new=[];objects=ledger['objects'];names={q['model']for q in json.loads((w/'smoke-changes.json').read_text())};objects=[q for q in objects if not (q.get('displayName') in names and q.get('kind')!='visual-object')]
for row in a['newPrototypes']:
 q={**base,**row,'displayName':row['name'],'kind':'visual-object','reuseTier':'authored','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':[mmap[n]for n in row['materials']],'reason':'Overlapping nearly spherical billows without stretching entire shape to old bounds; native topology/UV/positions match SPM.'};new.append(q);objects.append(q)
for row in json.loads((w/'smoke-changes.json').read_text()):
 p=mod/row['model'];q={**base,'id':'volcano-fidelity-v5-model-'+hashlib.sha256(row['model'].encode()).hexdigest()[:12],'displayName':row['model'],'kind':'authored-smoke-volume','reuseTier':'authored','canonicalPackPath':str(p),'physicalSourcePath':str(sources/'Smoke Billow Sources.blend'),'file':info(p),'dependencies':[mmap[n]for proto in a['newPrototypes']if Path(proto['sourceModel']).name==row['model']for n in proto['materials']],'reason':'Near-spherical overlapping billows; whole local bounds and origin preserved within 0.0001; original scene transforms and motion curves unchanged. Mesh bytes and triangle count within 20 percent original. Palette reused from V3; texture weights are recorded separately.','adaptationProof':row};new.append(q);objects.append(q)
pool['objects']=[q for q in pool['objects']if not q['id'].startswith('volcano-fidelity-v5-')]+new;ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon)and 'sha256'in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id']for key in ['objects','materials','textures']for q in pool[key]];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V5','status':'Rejected: opaque volumes obscure the road. Original alpha geometry is being tested separately; production unchanged.','objects':objects,'finalBlend':a['finalBlend'],'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'deltaAssetCounts':{'objects':6,'materials':0,'textures':0},'approval':'No final visual acceptance recorded','productionIntegrated':False,'visualPreservationPassed':False});ledger['assets']=objects+ledger['materials']+ledger['textures'];ledger['reusedAssetIds']=[q['id']for q in ledger['assets']if not q['id'].startswith('volcano-fidelity-v5-')]
for q in ledger['assets']:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');audit={'newObjects':6,'newMaterials':0,'newTextures':0,'usedAssets':len(ledger['assets']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci};(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V5_DELTA_POOL_REGISTERED',audit)
