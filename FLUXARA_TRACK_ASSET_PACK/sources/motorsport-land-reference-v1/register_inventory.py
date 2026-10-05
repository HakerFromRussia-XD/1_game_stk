from pathlib import Path
import json,hashlib,shutil,collections
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pf.read_text());reg=json.loads((r/'asset-registration.json').read_text());track='fluxara-user-motorsport-land';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';mod=pack/'models/motorsport-land-reference-v1';sources=pack/'sources/motorsport-land-reference-v1'
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
if not (r/'pool-before-motorsport-land.json').exists():shutil.copy2(pf,r/'pool-before-motorsport-land.json')
textures=[]
variants={x['file']:x for x in json.loads((r/'texture-resolution-variants.json').read_text())};reuse={x['target']:x for x in json.loads((r/'reuse.json').read_text())}
for name,row in reg['textures'].items():
 p=Path(row['packPath']);before=r/'before'/name;direct=before.is_file() and info(before)['sha256']==row['sha256'];source=Path(row['source']);authored=name in ['screenshot.jpg','OBJ.png','CR1.png','CR2.png']
 tier='direct' if direct else 'authored' if authored else 'adapt' if name in variants or name.startswith(('ml_','dp_sky_')) else 'direct'
 reason='Actual game-engine screenshot, technically resized; no painted additions' if name=='screenshot.jpg' else 'Unmodified existing pooled or original texture' if tier=='direct' else 'Native vector atlas with spectators and stylized circuit surfaces' if authored else 'Pooled texture relinked to preserved physical surface; technical resolution variant when recorded'
 sourcepath=str(sources/'screenshots/preview-start.png') if name=='screenshot.jpg' else str(sources/(name+'.svg')) if authored else str(reuse[name]['source']) if name in reuse else row['source']
 textures.append({'id':'ml-v1-texture-'+hashlib.sha256(name.encode()).hexdigest()[:12],'displayName':name,'kind':'texture','sourceMap':track,'reuseTier':tier,'canonicalPackPath':str(p),'file':info(p),'physicalSourcePath':sourcepath,'categories':['race-track','forest','festival'],'reason':reason,'resolutionVariant':variants.get(name),'uses':[{'trackId':track,'status':'Integrated draft; visual acceptance pending'}]})
tmap={a['displayName']:a['id'] for a in textures};materials=[]
for row in reg['materials']:
 materials.append({**row,'displayName':row['name'],'kind':'material','sourceMap':track,'reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+row['name'],'physicalSourcePath':reg['visualLibrary'],'dependencies':[tmap[n] for n in row['textures']],'categories':['race-track','forest','festival'],'uses':[{'trackId':track,'status':'Integrated'}]})
mmap={a['name']:a['id'] for a in materials};objects=[];counts=collections.Counter(x['prototype'] for x in reg['nativeSharedInstances'])
for row in reg['objects']:
 authored='festival_balloon_v1' in row['sourceModel'];adapt=False
 objects.append({**row,'displayName':row['name'],'kind':'visual-object','sourceMap':track,'reuseTier':'authored' if authored else 'adapt' if adapt else 'direct','canonicalPackPath':str(canon)+'#Object/'+row['name'],'physicalSourcePath':reg['visualLibrary'],'file':info(Path(reg['visualLibrary'])),'dependencies':[mmap[n] for n in row['materials']],'source':row['sourceModel'],'reason':'Reference-driven low-poly hot-air balloon' if authored else 'Adapted shared scenery' if adapt else 'Unmodified shared runtime mesh, linked by coordinates','categories':['race-track','forest','festival'],'uses':[{'trackId':track,'instances':counts[row['name']],'status':'Integrated; visual acceptance pending'}]})
protected=mod/'motorsport-land_track.spm';shutil.copy2(r/'candidate/motorsport-land_track.spm',protected);objects.append({'id':'ml-v1-protected-track-assembly','displayName':'Motorsport Land protected course assembly','kind':'protected-track-assembly','sourceMap':track,'reuseTier':'adapt','canonicalPackPath':str(protected),'file':info(protected),'dependencies':[a['id'] for a in materials],'reason':'Retained original triangle corners, normals and topology; ground UVs changed; old billboard scenery removed; driving road and curbs remain exact; not a generic scenery prototype','uses':[{'trackId':track,'status':'Integrated'}]})
for key,rows in [('objects',objects),('materials',materials),('textures',textures)]:pool[key]=[a for a in pool[key] if not a['id'].startswith('ml-v1-')]+rows
ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon) and 'sha256' in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[a['id'] for k in ['objects','materials','textures'] for a in pool[k]];assert len(ids)==len(set(ids));assets=objects+materials+textures
for a in assets:assert Path(a['canonicalPackPath'].split('#')[0]).is_file();assert all(x in ids for x in a.get('dependencies',[]))
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');ledger={'trackId':track,'displayName':'Motorsport Land','campaignPosition':8,'visualTheme':'One racing-festival style with rounded forest scenery','reference':{'fileKey':'Pws4Hw0fwwTmTMf6OJvil8','nodeId':'390:124','local':str(r/'references/figma-eighth.png')},'objects':objects,'materials':materials,'textures':textures,'assets':assets,'finalBlend':reg['finalBlend'],'runtimeStorage':'Scene coordinate placements and shared mesh libraries; no per-instance baked mesh copies','placements':json.loads((r/'placements.json').read_text()),'preservation':json.loads((r/'preservation-audit.json').read_text()),'approval':'No final user visual acceptance recorded','runtimeValidation':'Timed lap-trial draft verification in progress; original baseline terminated naturally','report':None};(r.parent.parent/(track+'.asset-ledger.json')).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(r/'pool-audit.json').write_text(json.dumps({'usedAssets':len(assets),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci},indent=2));print('POOL_REGISTERED',len(assets),len(ids))
