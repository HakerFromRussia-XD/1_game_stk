from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v9';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v9';mod=pack/'models/volcano-remake-fidelity-v9';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend'
a=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());ledger=json.loads((r/'fidelity-v8b/candidate-asset-ledger.json').read_text());assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==1;assert(w/'canonical-bindings-verification.json').is_file();assert(w/'final-blend-verification.json').is_file()
if not(w/'pool-before-v9.json').exists():shutil.copy2(pf,w/'pool-before-v9.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
sources.mkdir(exist_ok=True)
for name in ['build_fidelity_v8_castles.py','verify_fidelity_v8.py','audit_fidelity_v8_budget.py','finalize_fidelity_v8.py','capture_fidelity_v8_drive.py','capture_fidelity_v8_inspection.py','build_fidelity_v8b_castles.py','verify_fidelity_v8b.py','audit_fidelity_v8b_budget.py','finalize_fidelity_v9.py','verify_fidelity_v9_native.py','register_fidelity_v9_canonical.py','verify_fidelity_v9_canonical.py','capture_fidelity_v9_drive.py','capture_fidelity_v9_inspection.py','build_fidelity_v9_roofs.py','verify_fidelity_v9.py','audit_fidelity_v9_budget.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
    if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
for folder in ['screenshots','candidate','native']:
    if(w/folder).is_dir():shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)
# Preserve preceding V8 evidence without suggesting it is production.
prior=sources/'iterations/v8b';prior.mkdir(parents=True,exist_ok=True)
for name in ['castle-changes.json','budget.json','preservation.json','runtime-validation.json','drive-capture.json','asset-registration.json']:
    if(r/'fidelity-v8b'/name).is_file():shutil.copy2(r/'fidelity-v8b'/name,prior/name)
shutil.copytree(r/'fidelity-v8b/screenshots',prior/'screenshots',dirs_exist_ok=True)
usage=[{'trackId':'fluxara-user-volcano-remake','instances':2,'status':'V9 isolated gray tower variant candidate; castle walls, cliffs, lava and atmosphere unfinished. Production and preview unchanged'}];base={'sourceMap':'fluxara-user-volcano-remake','categories':['castle','lava'],'uses':usage}
row=a['newPrototypes'][0];mat=a['materials'][-1];skin=json.loads((w/'skin-changes.json').read_text());tid='volcano-fidelity-v9-castle-texture-alias';mid=mat['id'];library=Path(skin['library']);atlas=pack/'textures/volcano-remake-fidelity-v9'/skin['runtimeTextureAlias'];original=next(q for q in pool['objects']if q['id']=='lap-v1-f4c4d2b2153a47ef')
tex={**base,'id':tid,'displayName':atlas.name,'kind':'texture','reuseTier':'direct','canonicalPackPath':str(atlas),'physicalSourcePath':skin['paletteSource'],'file':info(atlas),'dependencies':['lap-v1-texture-3cef9b82dce3'],'reason':'Byte-identical tower palette under unique runtime filename. New alias bytes counted in game budget; no generated or recolored pixels.'}
material={**base,**mat,'kind':'material','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+mat['name'],'physicalSourcePath':a['visualLibrary'],'dependencies':[tid],'reason':'Existing tower material adapted to UV variant; donor material unchanged.'}
proto={**base,**row,'displayName':row['name'],'kind':'visual-object','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':a['visualLibrary'],'file':info(Path(a['visualLibrary'])),'dependencies':[mid],'reason':'Gray tower body retained from pooled model; top reshaped to sixteen-face red cone. Local bounds/origin/axes retained; original map collision exact.','adaptedFrom':original['id']}
model=mod/Path(skin['adaptedModel']).name;runtime={**base,'id':'volcano-fidelity-v9-castle-spm','displayName':model.name,'kind':'runtime-model','reuseTier':'adapt','canonicalPackPath':str(model),'physicalSourcePath':skin['sourceModel'],'file':info(model),'dependencies':[mid],'adaptationScript':str(sources/'build_fidelity_v8b_castles.py'),'adaptationProof':skin,'reason':'Actual runtime SPM variant; model plus palette weight decreased 9.596 percent.'}
xml=sources/'shared-runtime/materials.xml';xml.parent.mkdir(exist_ok=True);shutil.copy2(library/'materials.xml',xml);runtime_mat={**base,'id':'volcano-fidelity-v9-runtime-material','displayName':'V9 tower materials.xml','kind':'runtime-material-definition','reuseTier':'adapt','canonicalPackPath':str(xml),'physicalSourcePath':str(library/'materials.xml'),'file':info(xml),'dependencies':[tid,mid]}
for key,rows in [('objects',[proto,runtime]),('materials',[material,runtime_mat]),('textures',[tex])]:
    pool[key]=[q for q in pool[key]if not q['id'].startswith('volcano-fidelity-v9-')]+rows
    ledger[key]=[q for q in ledger[key]if not q['id'].startswith('volcano-fidelity-v9-')]+rows
ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon)and'sha256'in v:v.update(ci)
        for x in v.values():refresh(x)
    elif isinstance(v,list):
        for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id']for key in ['objects','materials','textures']for q in pool[key]];assert len(ids)==len(set(ids))
ledger.update({'candidate':'V9 gray towers with red conical roofs','status':'Isolated draft: two coordinate tower variants, upper old wood roof hidden while exact collision retained. Gray body and true red cone roofs; remaining scene fidelity unfinished.','finalBlend':a['finalBlend'],'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'deltaAssetCounts':{'objects':2,'materials':2,'textures':1},'productionIntegrated':False,'nativeSharedParts':len(a['nativeSharedInstances']),'mapOnlyProtectedCollision':[q['collider']for q in json.loads((w/'castle-changes.json').read_text())],'approval':'No final visual approval recorded'})
ledger['mapRuntimeFiles']=[info(p) for p in (sources/'candidate').iterdir() if p.is_file()];ledger['mapRuntimeFileScope']='Exact candidate resources, including map-specific main model and protected original collision meshes; these are not general decorative prototypes.';ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures'];ledger['reusedAssetIds']=[q['id']for q in ledger['assets']if not q['id'].startswith('volcano-fidelity-v9-')]
for q in ledger['assets']:
    assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id'];assert all(dep in ids for dep in q.get('dependencies',[])),q['id']
    if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
audit={'newObjects':2,'newMaterials':2,'newTextures':1,'newImagePixels':False,'newRuntimeTextureAliasBytes':atlas.stat().st_size,'retainedAuthoringAssets':len(ledger['assets']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False};pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V9_POOL_REGISTERED',audit)
