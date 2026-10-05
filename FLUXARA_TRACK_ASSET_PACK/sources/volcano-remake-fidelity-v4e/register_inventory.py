from pathlib import Path
import json,hashlib,shutil,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';pf=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.load(open(pf));reg=json.load(open(r/'asset-registration.json'));track='fluxara-user-volcano-remake';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';mod=pack/'models/volcano-remake-reference-v1';sources=pack/'sources/volcano-remake-reference-v1'
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
if not (r/'pool-before-volcano-remake.json').exists():shutil.copy2(pf,r/'pool-before-volcano-remake.json')
reuse={x['target']:x for x in json.load(open(r/'reuse.json'))};textures=[]
for name,row in reg['textures'].items():
 p=Path(row['packPath']);source=Path(row['source']);alias=source.name;svg=sources/(alias+'.svg');variant=reuse.get(alias,reuse.get(name));tier='authored' if name=='screenshot.jpg' and (r/'preview-update.json').exists() or svg.is_file() or variant and variant.get('reuseTier')=='authored' else 'adapt' if variant and variant.get('reuseTier')=='adapt' else 'direct'
 sp=Path(variant['source']) if variant else source
 if name=='screenshot.jpg':sp=sources/'screenshots/preview-castle-wide.png' if (r/'preview-update.json').exists() else sources/'original-runtime/screenshot.jpg'
 elif svg.is_file():sp=svg
 elif (sources/sp.name).exists() and sp.parent==r:sp=sources/sp.name
 elif (sources/'generated'/sp.name).exists():sp=sources/'generated'/sp.name
 elif (sources/'original-runtime'/sp.name).exists() and sp.parent==r/'before':sp=sources/'original-runtime'/sp.name
 reason='Actual game-engine screenshot; technical centered crop/resize only' if name=='screenshot.jpg' and (r/'preview-update.json').exists() else 'Native editable SVG material palette derived from the reference' if svg.is_file() else variant.get('adaptation','Original or pooled texture') if variant else 'Original or approved pooled image retained; renderer aliases resolved explicitly'
 textures.append({'id':'volcano-v1-texture-'+hashlib.sha256(name.encode()).hexdigest()[:12],'displayName':name,'kind':'texture','sourceMap':track,'reuseTier':tier,'canonicalPackPath':str(p),'physicalSourcePath':str(sp),'file':info(p),'sourceRelationship':variant,'categories':['lava'],'reason':reason,'uses':[{'trackId':track,'status':'Integrated; final visual acceptance pending'}]})
tmap={q['displayName']:q['id'] for q in textures};materials=[]
for q in reg['materials']:materials.append({**q,'displayName':q['name'],'kind':'material','sourceMap':track,'reuseTier':'adapt','canonicalPackPath':str(canon)+'#Material/'+q['name'],'physicalSourcePath':reg['visualLibrary'],'dependencies':[tmap[n] for n in q['textures']],'categories':['lava'],'uses':[{'trackId':track,'status':'Integrated'}]})
mmap={q['name']:q['id'] for q in materials};counts=collections.Counter(q['prototype'] for q in reg['nativeSharedInstances']);objects=[]
for q in reg['objects']:
 objects.append({**q,'displayName':q['name'],'kind':'visual-object','sourceMap':track,'reuseTier':'direct','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':reg['visualLibrary'],'file':info(Path(reg['visualLibrary'])),'dependencies':[mmap[n] for n in q['materials']],'reason':'Existing shared runtime model reused unchanged; linked instances retain coordinate transforms','categories':['lava'],'uses':[{'trackId':track,'instances':counts[q['name']],'status':'Integrated; visual acceptance pending'}]})
changed={'volcano_track.spm','vulcan_01.spm','vulcan_02.spm','vulcan_03.spm'}|{q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))}
for src in sorted((r/'candidate').glob('*.spm')):
 p=mod/src.name;shutil.copy2(src,p);objects.append({'id':'volcano-v1-model-'+hashlib.sha256(src.name.encode()).hexdigest()[:12],'displayName':src.name,'kind':'protected-track-assembly' if src.name=='volcano_track.spm' else 'authored-smoke-volume' if src.name in {q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))} else 'retained-original-model','sourceMap':track,'reuseTier':'authored' if src.name in {q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))} else 'adapt' if src.name in changed else 'direct','canonicalPackPath':str(p),'physicalSourcePath':str(sources/'Volcanic Smoke Volumes.blend') if src.name in {q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))} else str(sources/'original-runtime'/src.name),'file':info(p),'dependencies':[q['id'] for q in materials],'reason':('New rounded smoke mesh; local bounds, bounding center, origin and scene animation retained; triangle count within 20 percent' if src.name in {q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))} else 'Original positions, normals, indices, bounds, origin and transforms retained; rock UV/colors changed to two-cell moss palette') if src.name in changed else 'Original model retained byte-for-byte; smoke, lava, ramps and animations preserved separately in scene XML','uses':[{'trackId':track,'status':'Integrated'}]})
# Material XML defines additional support maps even in the renderer compatibility configuration.
for m in E.parse(r/'candidate/materials.xml').getroot():
 deps=[tmap[n] for k,n in m.attrib.items() if k in ['name','normal-map','gloss-map'] and n in tmap]
 materials.append({'id':'volcano-v1-runtime-material-'+hashlib.sha256(E.tostring(m)).hexdigest()[:12],'displayName':'Runtime '+m.get('name'),'kind':'runtime-material-definition','sourceMap':track,'reuseTier':'adapt' if m.get('name','').startswith('smoke') else 'direct','canonicalPackPath':str(sources/'materials.xml'),'physicalSourcePath':str(sources/'original-runtime/materials.xml'),'dependencies':deps,'sourceXml':E.tostring(m,encoding='unicode'),'categories':['lava'],'uses':[{'trackId':track,'status':'Integrated'}]})
# Duplicate original gridA material rows describe one identical definition.
materials=list({q['id']:q for q in materials}.values())
for key,values in [('objects',objects),('materials',materials),('textures',textures)]:pool[key]=[q for q in pool[key] if not q['id'].startswith('volcano-v1-')]+values
shutil.copy2(r/'candidate/materials.xml',sources/'materials.xml');ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon) and 'sha256' in v:v.update(ci)
  for x in v.values():refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id'] for k in ['objects','materials','textures'] for q in pool[k]];assert len(ids)==len(set(ids));assets=objects+materials+textures
for q in assets:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id']
 assert Path(q['physicalSourcePath'].split('#')[0]).exists(),(q['id'],q['physicalSourcePath'])
 assert all(n in ids for n in q.get('dependencies',[])),q['id']
pf.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');ledger={'trackId':track,'displayName':'Volcano Remake','campaignPosition':10,'visualTheme':'One volcanic castle style','reference':{'fileKey':'Pws4Hw0fwwTmTMf6OJvil8','nodeId':'378:39','local':str(r/'references/figma-tenth.png')},'objects':objects,'materials':materials,'textures':textures,'assets':assets,'finalBlend':reg['finalBlend'],'runtimeStorage':'62 shared scenery placements reference five existing runtime libraries; original castle/course and dynamic volcanic effects preserved separately','placements':json.load(open(r/'placements.json')),'preservation':json.load(open(r/'preservation-audit.json')),'approval':'No final user visual acceptance recorded','runtimeValidation':'Final runtime checks in progress','report':None};(r.parent.parent/(track+'.asset-ledger.json')).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(r/'pool-audit.json').write_text(json.dumps({'usedAssets':len(assets),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci},indent=2));print('POOL_REGISTERED',len(assets),len(ids))
