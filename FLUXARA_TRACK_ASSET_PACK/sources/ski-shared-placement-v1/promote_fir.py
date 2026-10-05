from pathlib import Path
import json,sys,shutil,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
out=r/'candidate';before=r/'before';p=r/'ski-extraction.json';a=json.load(open(p));name='fluxara_driftlib_ski_branchless_fir_v12';folder=r/'new-library'/name;folder.mkdir(exist_ok=True);model=before/'ski-dash-branchless-fir-v12.spm';d=parse(model);aliases={}
for pair in d['materials']:
 for n in pair:
  if not n:continue
  src=before/n;sha=hashlib.sha256(src.read_bytes()).hexdigest();alias='fluxara_pool_'+sha[:12]+src.suffix;dst=r/'new-textures'/alias;shutil.copy2(src,dst);aliases[n]=alias
  a['textures'].append({'original':n,'alias':alias,'source':str(src),'path':str(dst),'bytes':dst.stat().st_size,'sha256':sha,'previouslyPackaged':False,'previouslyPackagedPath':None})
  local=out/n
  if local.exists():shutil.move(str(local),str(r/'unused-candidate-textures'/n))
(folder/model.name).write_bytes(rewrite_texture_names(d,[[aliases.get(n,n) for n in pair] for pair in d['materials']]))
# The baked trees in retained scenery use the same original images. Update only
# texture string tables; geometry records and index streams are unchanged.
scenery=out/'ski-dash_winter_scenery.spm';dd=parse(scenery);scenery.write_bytes(rewrite_texture_names(dd,[[aliases.get(n,n) for n in pair] for pair in dd['materials']]))
node=E.Element('scene');E.SubElement(node,'object',id='branchless_fir',type='animation',model=model.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'});E.ElementTree(node).write(folder/'node.xml',encoding='unicode')
root=E.parse(out/'scene.xml');rows=[]
for q in list(root.getroot()):
 if q.tag=='object' and q.get('model')==model.name:
  old=E.tostring(q,encoding='unicode');attrib={k:q.get(k) for k in ['id','xyz','hpr','scale']};attrib['name']=name;idx=list(root.getroot()).index(q);root.getroot().remove(q);root.getroot().insert(idx,E.Element('library',attrib));rows.append({'id':q.get('id'),'library':name,'xyz':list(map(float,q.get('xyz').split())),'hpr':list(map(float,q.get('hpr').split())),'scale':list(map(float,q.get('scale').split())),'originalXml':old,'existingCoordinateInstance':True})
assert len(rows)==71
root.write(out/'scene.xml',encoding='utf-8',xml_declaration=True)
# Original local material parameters remain effective under the new texture name.
mats=E.parse(out/'materials.xml')
for q in mats.getroot():
 if q.get('name') in aliases:q.set('name',aliases[q.get('name')])
E.ElementTree(mats.getroot()).write(out/'materials.xml',encoding='utf-8',xml_declaration=True)
shutil.move(str(out/model.name),str(r/'unused-candidate-textures'/model.name))
a['prototypes'].append({'library':name,'sourceObject':'Existing 71 coordinate trees','instances':71,'triangles':sum(len(b['indices'])//3 for b in d['buffers']),'localBounds':d['bounds'],'model':str(folder/model.name),'geometryVertexIndexBytesExact':True,'texturePixelsExact':True})
a['placements']+=rows;a['coordinateInstances']=len(a['placements']);a['uniqueModels']=len(a['prototypes']);a['previousCoordinateInstancesPromotedToRuntimePool']=71;a['originalSceneNodesUnchanged']=False;a['decorativeFirTagChangesOnly']=True
for q in a['prototypes']:
 own=E.Element('materials')
 for m in mats.getroot():
  if m.get('name') in {n for pair in parse(q['model'])['materials'] for n in pair}:own.append(E.fromstring(E.tostring(m)))
 E.ElementTree(own).write(Path(q['model']).parent/'materials.xml',encoding='unicode')
a['candidateTrackBytes']=sum(f.stat().st_size for f in out.iterdir() if f.is_file());a['allNewSharedBytes']=sum(f.stat().st_size for f in (r/'new-library').rglob('*') if f.is_file())+sum(q['bytes'] for q in a['textures'] if not q['previouslyPackaged']);a['totalCandidateBytes']=a['candidateTrackBytes']+a['allNewSharedBytes'];a['weightNotIncreased']=a['totalCandidateBytes']<=a['sourceBytes'];assert a['weightNotIncreased'];p.write_text(json.dumps(a,indent=2));print('FIR_PROMOTED',len(rows),a['sourceBytes']-a['totalCandidateBytes'])
