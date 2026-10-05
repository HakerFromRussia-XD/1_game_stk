from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pp=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.load(open(pp));proof=json.load(open(r/'runtime-materials.json'));blends=json.load(open(r/'blend-update.json'));changed={q['path']:q for q in blends};names={'fluxara_cottage_windows.png','fluxara_chalet_window.png'};ids=[]
for m in pool['materials']:
 if any(n in str(m) for n in names) or m['id']=='shared-chalet-fluxara_chalet_window-v1-material':
  m['runtimeShader']='unlit';m['sharedWindowLighting']='Self luminous on every map that reuses this model; explicitly requested by user';m['windowFixEvidence']=str(r/'runtime-materials.json');ids.append(m['id'])
  if m.get('attributes',{}).get('name') in names:m['attributes']['shader']='unlit'
def update(v):
 if isinstance(v,dict):
  if v.get('path') in changed and 'sha256' in v:
   q=changed[v['path']];v.update({k:q[k] for k in ['path','bytes','sha256']})
  for n in list(v.values()):update(n)
 elif isinstance(v,list):
  for n in v:update(n)
update(pool)
for o in pool['objects']:
 if o.get('physicalSourcePath') in changed:
  q=changed[o['physicalSourcePath']];o['sourceFile']={k:q[k] for k in ['path','bytes','sha256']};o['sharedWindowLighting']='unlit; geometry, UVs, collider and model transforms retained'
pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');proof['sharedPoolMaterialIds']=ids;proof['blenderSourcesUpdated']=blends;(r/'runtime-materials.json').write_text(json.dumps(proof,indent=2))
# The current map ledger carries the shared material correction, preserving prior evidence.
for lp in [r.parent.parent.parent/'fluxara-user-ski-dash.asset-ledger.json',r.parent.parent.parent/'fluxara-user-lap-catch.asset-ledger.json']:
 ledger=json.load(open(lp));ledger['sharedWindowMaterialCorrection']={'shader':'unlit','materials':ids,'evidence':str(r/'runtime-materials.json'),'geometryAndTexturesUnchanged':True,'userAuthorizedGlobalReuse':True};lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
print('WINDOW_POOL_UPDATED',len(ids),len(blends))
