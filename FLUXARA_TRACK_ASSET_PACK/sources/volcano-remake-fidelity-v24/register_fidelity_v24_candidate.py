from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, shutil

r=Path(__file__).resolve().parent; w=r/'fidelity-v24'
repo=Path('/Users/motoricallc/Downloads/fluxara-drift'); pack=repo/'FLUXARA_TRACK_ASSET_PACK'
sources=pack/'sources/volcano-remake-fidelity-v24'; sources.mkdir(exist_ok=True)
mod=pack/'models/volcano-remake-fidelity-v24'; canon=pack/'blender/FLUXARA_Track_Asset_Library.blend'
pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
a=json.loads((w/'asset-registration.json').read_text()); pool=json.loads(pf.read_text())
ledger=json.loads((r/'fidelity-v23/candidate-asset-ledger.json').read_text())
pres=json.loads((w/'preservation-verification.json').read_text())
run=json.loads((w/'runtime-validation.json').read_text())
assert json.loads((w/'canonical-registration.json').read_text())['newObjects']==3
assert json.loads((w/'final-blend-verification.json').read_text())['allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV23']==609
assert (w/'canonical-bindings-verification.json').is_file()
assert 'V24_CANONICAL_WARM_SMOKE_AND_REUSED_TORCH_BINDINGS_VERIFIED' in (w/'canonical-verification.log').read_text()
assert run['visualInspectionCompleted'] and run['naturalFinishObserved'] and run['finalProbeTrackCleanupVerified']
if not(w/'pool-before-v24.json').exists(): shutil.copy2(pf,w/'pool-before-v24.json')
def info(p):
    p=Path(p); return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for f in r.glob('*fidelity_v24*.py'): shutil.copy2(f,sources/f.name)
for f in w.glob('*.json'):
    if not f.name.startswith('pool-before'): shutil.copy2(f,sources/f.name)
for folder in ['candidate','native','screenshots']: shutil.copytree(w/folder,sources/folder,dirs_exist_ok=True)

# Repair a pre-existing missing index for the already deployed emitter. No donor file changes.
emitter_id='shared-torch-warm-sparks-emitter-v1'
emitter_new=not any(q['id']==emitter_id for k in ['objects','materials','textures'] for q in pool[k])
emitter=repo/'iosApp/FluxaraResources/gfx/fluxara_torch_warm_sparks.xml'
stored_emitter=pack/'models/shared/fluxara_bronze_wall_torch_v1/fluxara_torch_warm_sparks.xml'
assert emitter.read_bytes()==stored_emitter.read_bytes()
group=next(q for q in pool['materials'] if q['id']=='shared-bronze-wall-torch-materials-v1')
for q in group['preservedExternalDependencies']: assert info(q['path'])==q
if emitter_new:
    pool['objects'].append({'id':emitter_id,'displayName':'Existing torch warm sparks emitter',
        'kind':'particle-definition','sourceMap':'shared-library','reuseTier':'direct',
        'canonicalPackPath':str(stored_emitter),'physicalSourcePath':str(emitter),'file':info(stored_emitter),
        'dependencies':[], 'preservedExternalDependencies':copy.deepcopy(group['preservedExternalDependencies']),
        'reason':'Missing index repaired for existing deployed donor emitter, no new runtime bytes or pixels.'})
base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],
      'uses':[{'trackId':'fluxara-user-volcano-remake','candidate':'V24',
      'status':'Warm underside smoke vertex colors and six direct pooled torch placements. Stone pixels/UVs, course, controls and existing collision retained. Not integrated.'}]}
new=[]
for q in a['newPrototypes']:
    deps=[next(m['id'] for m in ledger['materials'] if m.get('name',m.get('displayName'))==name) for name in q['materials']]+[q['sourcePoolObjectId']]
    new.append({**base,**q,'displayName':q['name'],'kind':'visual-object','reuseTier':'adapt',
        'canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':a['visualLibrary'],
        'file':info(a['visualLibrary']),'dependencies':deps,'reason':q['role']})
    src=Path(q['sourceModel']); stored=mod/src.name; assert stored.read_bytes()==src.read_bytes()
    new.append({**base,'id':'volcano-fidelity-v24-runtime-'+src.stem.lower(),'displayName':src.name,
        'kind':'map-runtime-model','reuseTier':'adapt','canonicalPackPath':str(stored),
        'physicalSourcePath':str(src),'file':info(stored),'dependencies':[q['id']],
        'productionIntegrated':False,'newTextureFiles':0,'reason':'Source geometry retained; RGB replaces unused texture UVs. Historical files retained and charged.'})
torch_native=Path(json.loads((w/'atmosphere-changes.json').read_text())['existingTorchPack'])/'Fluxara Bronze Wall Torch.blend'
for q in a['reusedMaterialVariants']:
    texture_ids=[next(t['id'] for t in pool['textures'] if t['id'] in group['textureRefs'] and Path(t.get('canonicalPackPath','')).name==name) for name in q['textures']]
    row={**base,**q,'displayName':q['name'],'kind':'material-binding-index',
         'canonicalPackPath':str(canon)+'#Material/'+q['name'],
         'physicalSourcePath':str(torch_native),'file':info(torch_native),
         'dependencies':[q['sourcePoolMaterialGroupId']]+texture_ids,
         'reason':'Index of an existing pooled material copied into target project. No newly authored material or pixels.'}
    pool['materials']=[m for m in pool['materials'] if m['id']!=q['id']]+[row]
    ledger['materials']=[m for m in ledger['materials'] if m['id']!=q['id']]+[copy.deepcopy(row)]
for d in [pool,ledger]: d['objects']=[q for q in d['objects'] if not q['id'].startswith('volcano-fidelity-v24-')]+copy.deepcopy(new)

# Resolve the direct torch and its existing dependencies into this candidate's ledger.
lookup={q['id']:(k,q) for k in ['objects','materials','textures'] for q in pool[k]}
def add_existing(asset_id):
    k,q=lookup[asset_id]
    if not any(v['id']==asset_id for v in ledger[k]):
        row=copy.deepcopy(q)
        row.setdefault('physicalSourcePath',row['canonicalPackPath'].split('#')[0])
        ledger[k].append(row)
    for dep in q.get('dependencies',[])+q.get('textureRefs',[]): add_existing(dep)
    if q.get('scopedEmitter'): add_existing(q['scopedEmitter'])
add_existing('shared-bronze-wall-torch-reference-v1')
ci=info(canon)
def refresh(v):
    if isinstance(v,dict):
        if v.get('path')==str(canon) and 'sha256' in v: v.update(ci)
        for x in v.values(): refresh(x)
    elif isinstance(v,list):
        for x in v: refresh(x)
refresh(pool); refresh(ledger)
pool['physicalPack']['blenderLibrary']=ci; pool['updated']=datetime.now(timezone.utc).isoformat()
pool['assets']=pool['objects']+pool['materials']+pool['textures']
ids=[q['id'] for q in pool['assets']]; assert len(ids)==len(set(ids))
ledger.update({'candidate':'V24 warm underside smoke and six direct reused torches',
    'status':a['status'],'finalBlend':a['finalBlend'],'nativeSharedParts':len(a['nativeSharedInstances']),
    'preservation':pres,'budget':pres,'runtimeValidation':run,
    'deltaAssetCounts':{'objects':6,'existingEmitterIndexRepaired':int(emitter_new),
                       'newAuthoredMaterials':0,'existingMaterialBindingIndices':4,'textures':0},
    'productionIntegrated':False,'newImagePixels':False})
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures']
ledger['mapRuntimeFiles']=[info(q) for q in (sources/'candidate').iterdir() if q.is_file()]
for q in ledger['assets']:
    assert q['id'] in ids and Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
    assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
    assert all(dep in ids for dep in q.get('dependencies',[])+q.get('textureRefs',[])),q['id']
    if q.get('scopedEmitter'): assert q['scopedEmitter'] in ids,q['id']
    if q.get('file'): assert info(q['file']['path'])==q['file'],q['id']
    for dep in q.get('preservedExternalDependencies',[]): assert info(dep['path'])==dep,q['id']
audit={'newObjects':6,'newNativePrototypes':3,'directReusedNativePrototypes':1,
    'newAuthoredMaterials':0,'existingMaterialBindingIndices':4,'existingEmitterMissingIndexRepaired':emitter_new,
    'newTextures':0,'newTorchRuntimeBytesAdded':0,'allPhysicalPathsAndFileHashesMatch':True,
    'uniquePoolIds':len(ids),'totalLedgerAssetsIncludingHistoricalSources':len(ledger['assets']),
    'unresolvedDependencies':[],'canonical':ci,'productionIntegrated':False,
    'nativeSharedParts':339,'allOriginalStonePixelsAndUVsRetained':True}
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']: shutil.copy2(w/name,sources/name)
print('V24_WARM_SMOKE_AND_DIRECT_TORCHES_REGISTERED',audit,flush=True)
