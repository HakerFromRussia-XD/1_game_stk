"""Index V4E delta without duplicating unchanged runtime models and texture files."""
from pathlib import Path
import json,hashlib,shutil,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v4e';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sources=pack/'sources/volcano-remake-fidelity-v4e';mod=pack/'models/volcano-remake-fidelity-v4e';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json'
reg=json.loads((w/'asset-registration.json').read_text());pool=json.loads(pf.read_text());assert len(reg['objects'])==15
assert json.loads((w/'canonical-registration.json').read_text())['objects']==15
assert json.loads((w/'final-blend-verification.json').read_text())['registeredPrototypes']==15
assert (w/'canonical-bindings-verification.json').is_file()
if not (w/'pool-before-fidelity-v4e.json').exists():shutil.copy2(pf,w/'pool-before-fidelity-v4e.json')
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
sources.mkdir(exist_ok=True);(sources/'generated').mkdir(exist_ok=True)
shutil.copy2(w/'volcanic-smoke-source.png',sources/'generated/volcanic-smoke-source.png');shutil.copy2(w/'imagegen-prompt.txt',sources/'imagegen-prompt.txt')
for name in ['fidelity_v4e.py','fidelity_v4d.py','finalize_fidelity_v4e.py','add_fidelity_v4e_effects.py','verify_fidelity_v4e.py','verify_fidelity_v4e_blend.py','capture_fidelity_v4e_drive.py',Path(__file__).name]:shutil.copy2(r/name,sources/name)
for p in w.glob('*.json'):
 if not p.name.startswith('pool-before'):shutil.copy2(p,sources/p.name)
shutil.copytree(w/'screenshots',sources/'screenshots',dirs_exist_ok=True);shutil.copy2(w/'candidate/materials.xml',sources/'materials.xml')
uses=[{'trackId':'fluxara-user-volcano-remake','status':'Candidate V4E; production integration pending'}]
base={'sourceMap':'fluxara-user-volcano-remake','categories':['lava'],'uses':uses}
new={'objects':[],'materials':[],'textures':[]};textures=[]
for name,row in reg['textures'].items():
 p=Path(row['packPath']);assert info(p)['sha256']==row['sha256']
 if name=='vr_volcanic_smoke.png':
  q={**base,'id':'volcano-fidelity-v4e-texture-smoke','displayName':name,'kind':'texture','reuseTier':'authored','canonicalPackPath':str(p),'physicalSourcePath':str(sources/'generated/volcanic-smoke-source.png'),'file':info(p),'reason':'Built-in imagegen transparent rounded plume; technical resize to 256x256 true RGBA. Prompt archived; no donor image altered.'};new['textures'].append(q)
 else:
  q=next(q for q in pool['textures'] if q['id'].startswith('volcano-fidelity-v3-') and q['displayName']==name and q['file']['sha256']==row['sha256'])
  row['packPath']=q['canonicalPackPath']
 textures.append(q)
(w/'asset-registration.json').write_text(json.dumps(reg,indent=2))
tmap={q['displayName']:q['id'] for q in textures};materials=[]
for row in reg['materials']:
 q={**base,**row,'displayName':row['name'],'kind':'material','reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+row['name'],'physicalSourcePath':reg['visualLibrary'],'dependencies':[tmap[n] for n in row['textures']],'reason':'Separate editable V4E material binding; unchanged image files reused from V3.'};materials.append(q);new['materials'].append(q)
mmap={q['name']:q['id'] for q in materials};counts=collections.Counter(q['prototype'] for q in reg['nativeSharedInstances']);objects=[]
for row in reg['objects']:
 authored='-effect-' in row['id'];q={**base,**row,'displayName':row['name'],'kind':'visual-object','reuseTier':'authored' if authored else 'direct','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':reg['visualLibrary'],'file':info(Path(reg['visualLibrary'])),'dependencies':[mmap[n] for n in row['materials']],'reason':'New overlapping double-sided billow cards; original bounds, origin and triangle count retained; UV uses entire transparent sprite.' if authored else 'Existing V3 portal or shared scenery geometry reused unchanged in the editable candidate.','uses':[{**uses[0],'instances':counts[row['name']]}]};objects.append(q);new['objects'].append(q)
changed={'AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm'}
for src in sorted((w/'candidate').glob('*.spm')):
 if src.name in changed:
  p=mod/src.name;shutil.copy2(src,p);q={**base,'id':'volcano-fidelity-v4e-model-'+hashlib.sha256(src.name.encode()).hexdigest()[:12],'displayName':src.name,'kind':'authored-smoke-cards','reuseTier':'authored','canonicalPackPath':str(p),'physicalSourcePath':str(sources/'fidelity_v4e.py'),'file':info(p),'dependencies':[tmap['vr_volcanic_smoke.png']],'reason':'Full-sprite overlapping transparent cards; local vertex extrema and original triangle count independently verified. Only ghost decorations changed.'};new['objects'].append(q)
 else:
  q=next(q for q in pool['objects'] if q['id'].startswith('volcano-fidelity-v3-model-') and q['displayName']==src.name and q['file']['sha256']==info(src)['sha256'])
 objects.append(q)
for material in E.parse(w/'candidate/materials.xml').getroot():
 xml=E.tostring(material,encoding='unicode');old=next((q for q in pool['materials'] if q['id'].startswith('volcano-fidelity-v3-runtime-material-') and q.get('sourceXml')==xml),None)
 if old:q=old
 else:
  assert material.get('name')=='vr_volcanic_smoke.png'
  q={**base,'id':'volcano-fidelity-v4e-runtime-material-smoke','displayName':'Runtime vr_volcanic_smoke.png','kind':'runtime-material-definition','reuseTier':'authored','canonicalPackPath':str(sources/'materials.xml'),'physicalSourcePath':str(sources/'materials.xml'),'dependencies':[tmap['vr_volcanic_smoke.png']],'sourceXml':xml,'reason':'Lit alpha-test smoke material; other physical parameters unchanged.'};new['materials'].append(q)
 materials.append(q)
materials=list({q['id']:q for q in materials}.values())
for key,values in new.items():pool[key]=[q for q in pool[key] if not q['id'].startswith('volcano-fidelity-v4e-')]+values
ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon) and 'sha256' in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci
ids=[q['id'] for key in new for q in pool[key]];assert len(ids)==len(set(ids))
assets=objects+materials+textures
for q in assets:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
 assert Path(q['physicalSourcePath'].split('#')[0]).exists(),q['id']
 assert all(d in ids for d in q.get('dependencies',[])),q['id']
 if q.get('file'):assert info(Path(q['file']['path']))==q['file'],q['id']
ledger={'trackId':'fluxara-user-volcano-remake','campaignPosition':10,'candidate':'V4E','status':'Isolated candidate; production source, preview and final project unchanged','objects':objects,'materials':materials,'textures':textures,'assets':assets,'finalBlend':reg['finalBlend'],'runtimeStorage':'62 scenery placements reference five existing libraries; five smoke effects have new reusable cards, without additional runtime library files.','nativeSharedParts':len(reg['nativeSharedInstances']),'preservation':json.loads((w/'preservation.json').read_text()),'budget':json.loads((w/'budget.json').read_text()),'runtimeValidation':json.loads((w/'runtime-validation.json').read_text()),'approval':'No final visual acceptance recorded','productionIntegrated':False,'deltaAssetCounts':{k:len(v) for k,v in new.items()},'reusedAssetIds':[q['id'] for q in assets if not q['id'].startswith('volcano-fidelity-v4e-')],'report':str(r.parent/'fluxara-user-volcano-remake-final/report/index.html')}
(w/'candidate-asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');audit={'usedAssets':len(assets),'newAssets':sum(map(len,new.values())),'deltaAssetCounts':ledger['deltaAssetCounts'],'reusedAssets':len(ledger['reusedAssetIds']),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci};(w/'pool-audit.json').write_text(json.dumps(audit,indent=2))
for name in ['candidate-asset-ledger.json','pool-audit.json']:shutil.copy2(w/name,sources/name)
print('V4E_DELTA_POOL_REGISTERED',audit)
