from pathlib import Path
import json,hashlib,shutil,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';poolp=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.load(open(poolp));reg=json.load(open(r/'asset-registration.json'));proof=json.load(open(r/'canyon-extraction.json'));track='fluxara-canyon';prefix='canyon-shared-v1-';canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';src=pack/'sources/canyon-shared-placement-v1';mod=pack/'models/canyon-shared-placement-v1'
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
textures=[]
for name,row in reg['textures'].items():
 p=Path(row['packPath']);textures.append({'id':prefix+'texture-'+hashlib.sha256(name.encode()).hexdigest()[:12],'displayName':name,'kind':'texture','sourceMap':track,'reuseTier':'authored' if name=='sshot-canyon-v1.png' and (r/'preview-update.json').exists() else 'direct','canonicalPackPath':str(p),'physicalSourcePath':row['source'],'file':info(p),'reason':'Actual engine screenshot, centered crop and resize only' if name=='sshot-canyon-v1.png' and (r/'preview-update.json').exists() else 'Original integrated pixels retained; copied to physical shared pack','categories':['canyon'],'uses':[{'trackId':track,'status':'Coordinate-reuse phase, runtime validation pending'}]})
tmap={q['displayName']:q['id'] for q in textures};materials=[]
for q in reg['materials']:materials.append({**q,'displayName':q['name'],'kind':'material','sourceMap':track,'reuseTier':'direct','canonicalPackPath':str(canon)+'#Material/'+q['name'],'physicalSourcePath':reg['visualLibrary'],'dependencies':[tmap[n] for n in q['textures']],'categories':['canyon'],'uses':[{'trackId':track,'status':'Coordinate-reuse phase'}]})
mmap={q['name']:q['id'] for q in materials};objects=[]
for q in reg['objects']:
 source=Path(q['sourceModel']);physical=mod/'runtime-library'/source.parent.name;physical.mkdir(parents=True,exist_ok=True)
 for f in source.parent.iterdir():
  if f.is_file():shutil.copy2(f,physical/f.name)
 objects.append({**q,'displayName':q['name'],'kind':'reusable-visual-object','sourceMap':track,'reuseTier':'adapt' if q['sourceModel'].startswith(str(r/'new-library')) else 'direct','canonicalPackPath':str(canon)+'#Object/'+q['name'],'physicalSourcePath':str(physical/source.name),'file':info(physical/source.name),'dependencies':[mmap[n] for n in q['materials']],'reason':'Previously baked scenery extracted into one local mesh with coordinate instances; local transform undo introduces only bounded sub-millimeter position and packed-normal quantization error' if q['sourceModel'].startswith(str(r/'new-library')) else 'Existing runtime library unchanged','categories':['canyon'],'uses':[{'trackId':track,'status':'Coordinate-reuse phase'}]})
for f in (r/'candidate'/track).glob('*.spm'):
 p=mod/f.name;shutil.copy2(f,p);objects.append({'id':prefix+'model-'+hashlib.sha256(f.name.encode()).hexdigest()[:12],'displayName':f.name,'kind':'protected-course-assembly' if f.name=='highinsky_track.spm' else 'retained-scenery-assembly','sourceMap':track,'reuseTier':'adapt' if f.name=='fluxara_canyon_decor.spm' else 'direct','canonicalPackPath':str(p),'physicalSourcePath':str(src/'original-runtime'/f.name),'file':info(p),'dependencies':[q['id'] for q in materials],'reason':'Remaining original scenery vertex records and triangle order byte-exact; repeated instances removed into reusable libraries' if f.name=='fluxara_canyon_decor.spm' else 'Original model byte-exact','uses':[{'trackId':track,'status':'Coordinate-reuse phase'}]})
shutil.copy2(r/'candidate'/track/'materials.xml',src/'materials.xml')
for i,e in enumerate(E.parse(src/'materials.xml').getroot()):materials.append({'id':prefix+'runtime-material-'+hashlib.sha256(E.tostring(e)).hexdigest()[:12],'displayName':'Runtime '+e.get('name'),'kind':'runtime-material-definition','sourceMap':track,'reuseTier':'direct','canonicalPackPath':str(src/'materials.xml'),'physicalSourcePath':str(src/'original-runtime/materials.xml'),'dependencies':[tmap[n] for k,n in e.attrib.items() if k in ['name','normal-map','gloss-map'] and n in tmap],'sourceXml':E.tostring(e,encoding='unicode'),'categories':['canyon'],'uses':[{'trackId':track,'status':'Coordinate-reuse phase'}]})
materials=list({q['id']:q for q in materials}.values())
for k,values in [('objects',objects),('materials',materials),('textures',textures)]:pool[k]=[q for q in pool[k] if not q['id'].startswith(prefix)]+values
ci=info(canon)
def refresh(v):
 if isinstance(v,dict):
  if v.get('path')==str(canon) and 'sha256' in v:v.update(ci)
  for x in list(v.values()):refresh(x)
 elif isinstance(v,list):
  for x in v:refresh(x)
refresh(pool);pool['physicalPack']['blenderLibrary']=ci;ids=[q['id'] for k in ['objects','materials','textures'] for q in pool[k]];assert len(ids)==len(set(ids));assets=objects+materials+textures
for q in assets:
 assert Path(q['canonicalPackPath'].split('#')[0]).is_file(),q['id'];assert Path(q['physicalSourcePath'].split('#')[0]).is_file(),q['id'];assert all(n in ids for n in q.get('dependencies',[])),q['id']
if not (r/'pool-before-canyon-shared.json').exists():shutil.copy2(poolp,r/'pool-before-canyon-shared.json')
poolp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');ledger={'trackId':track,'displayName':'Fluxara Canyon','campaignPosition':1,'biome':'canyon','finalBlend':reg['finalBlend'],'assets':assets,'placements':proof['placements']+proof.get('extraCoordinatePlacements',[]),'runtimeStorage':'295 formerly baked instances reference 47 reusable models; five new shrubs reuse an existing runtime library; original runtime libraries remain unchanged','preservation':proof,'approval':'Original art retained; coordinate-storage conversion has no new user visual approval recorded','runtimeValidation':'Pending','report':None};(r.parent.parent/'fluxara-canyon.asset-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(r/'pool-audit.json').write_text(json.dumps({'usedAssets':len(assets),'uniquePoolIds':len(ids),'allPhysicalPathsExist':True,'unresolvedDependencies':[],'canonical':ci},indent=2));print('POOL_REGISTERED',len(assets),len(ids))
