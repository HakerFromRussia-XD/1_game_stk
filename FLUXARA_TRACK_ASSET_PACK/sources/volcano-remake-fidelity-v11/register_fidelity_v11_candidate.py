from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v11';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');sources=pack/'sources/volcano-remake-fidelity-v11';sources.mkdir(exist_ok=True);a=json.loads((w/'asset-registration.json').read_text());ledger=json.loads((r/'fidelity-v10b/candidate-asset-ledger.json').read_text());proof=json.loads((w/'final-blend-verification.json').read_text());assert proof['all23PrototypeGeometryUvsNormalsMatchV10B'];assert len(proof['threeSmokeMatricesMatchXml'])==3
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ['build_fidelity_v11_smoke_placements.py','finalize_fidelity_v11.py','verify_fidelity_v11_native.py','capture_fidelity_v11_drive.py','capture_fidelity_v11_inspection.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):shutil.copy2(p,sources/p.name)
for folder in ['candidate','native','screenshots']:shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
pool=json.loads(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_POOL.json').read_text());ids={q['id']for key in ['objects','materials','textures']for q in pool[key]}
for q in ledger['assets']:
 assert q['id']in ids
 assert all(dep in ids for dep in q.get('dependencies',[]))
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file()
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
ledger.update({'candidate':'V11 smaller smoke plumes at original volcano vents; V10B stone retained','finalBlend':a['finalBlend'],'status':'Current isolated candidate. Three decorative atmosphere transforms changed; protected course, original dynamic hazards, all model and texture bytes retained. Overall visual fidelity still unfinished.','budget':json.loads((w/'budget.json').read_text()),'preservation':json.loads((w/'preservation.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'mapRuntimeFiles':[info(p)for p in(sources/'candidate').iterdir()if p.is_file()],'deltaAssetCounts':{'objects':0,'materials':0,'textures':0},'productionIntegrated':False});(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
audit={'allExistingAssetPathsAndHashesVerified':True,'newPoolAssets':0,'all23PrototypeMeshesUnchanged':True,'newTextures':0,'newSharedGameFiles':0,'reusedAssets':len(ledger['assets']),'coordinateSmokePlacementCount':3,'productionIntegrated':False};(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V11_REUSE_ARCHIVED',audit,flush=True)
