from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v7b';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v7b';mod=pack/'models/volcano-remake-fidelity-v7b';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend'
a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v5-alpha/candidate-asset-ledger.json').read_text());assert len(a['newPrototypes'])==3;assert len(json.loads((w/'final-blend-verification.json').read_text())['threeVolumetricPlumesAboveRoad'])==3;assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==3;assert(w/'canonical-bindings-verification.json').is_file()
if not(w/'pool-before-v7b.json').exists():shutil.copy2(pf,w/'pool-before-v7b.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
sources.mkdir(exist_ok=True)
for name in ['build_fidelity_v7b_smoke.py','weld_fidelity_v7b_smoke.py','verify_fidelity_v7b.py','audit_fidelity_v7b_budget.py','finalize_fidelity_v7b.py','verify_fidelity_v7b_native.py','register_fidelity_v7b_canonical.py','verify_fidelity_v7b_canonical.py','capture_fidelity_v7b_drive.py','capture_fidelity_v7b_inspection.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
for folder in ['screenshots','candidate','native','iterations']:
    if(w/folder).is_dir():shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
shutil.copy2(w/'Smoke Billow Sources.blend',sources/'Smoke Billow Sources.blend')
usage=[{'trackId':'fluxara-user-volcano-remake','status':'V7B isolated volumetric smoke candidate; production and preview unchanged'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':usage};models={q['model']for q in json.loads((w/'smoke-changes.json').read_text())};old_ids={'volcano-fidelity-v5a-cloud-'+Path(n).stem.lower()for n in models};objects=[q for q in ledger['objects']if q['id']not in old_ids and q.get('displayName')not in models];new_objects=[]
for row in a['newPrototypes']:
    dependencies=[next(q['id']for q in ledger['materials']if q.get('name')==name)for name in row['materials']]
    q={**base,**row,'displayName':row['name'],'kind':'visual-object','reuseTier':'authored','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':dependencies,'reason':'New low-poly volumetric billows, compensated for per-map scale so individual puffs remain round. Original local bounds/origin/axes retained.'};objects.append(q);new_objects.append(q)
for row in json.loads((w/'smoke-changes.json').read_text()):
    native=next(q for q in a['newPrototypes']if Path(q['sourceModel']).name==row['model']);material=next(q['id']for q in ledger['materials']if q.get('name')==native['materials'][0]);p=mod/row['model'];original=pack/'sources/volcano-remake-reference-v1/original-runtime'/row['model'];assert original.is_file()
    q={**base,'id':'volcano-fidelity-v7b-model-'+hashlib.sha256(row['model'].encode()).hexdigest()[:12],'displayName':row['model'],'kind':'authored-volumetric-smoke','reuseTier':'authored','canonicalPackPath':str(p),'physicalSourcePath':str(original),'file':info(p),'dependencies':[material],'adaptationScript':str(sources/'build_fidelity_v7b_smoke.py'),'adaptationProof':row,'reason':'Spherical billows with unchanged source local bounds, mesh byte/triangle change within twenty percent; existing pooled palette reused.'};objects.append(q);new_objects.append(q)
pool['objects']=[q for q in pool['objects']if not q['id'].startswith('volcano-fidelity-v7b-')]+new_objects;ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id']for key in ['objects','materials','textures']for q in pool[key]];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V7B volumetric smoke','status':'Isolated draft; three spherical volumetric plumes replace eleven former smoke placements. Castle, cliffs, lava and atmosphere composition still unfinished.','objects':objects,'finalBlend':a['finalBlend'],'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'deltaAssetCounts':{'objects':6,'materials':0,'textures':0},'productionIntegrated':False,'approval':'No final visual approval recorded'})
ledger['assets']=objects+ledger['materials']+ledger['textures'];ledger['reusedAssetIds']=[q['id']for q in ledger['assets']if not q['id'].startswith('volcano-fidelity-v7b-')]
for q in ledger['assets']:
    q['uses']=usage
    assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':6,'newMaterials':0,'newTextures':0,'retainedAuthoringAssets':len(ledger['assets']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V7B_POOL_REGISTERED',audit)
