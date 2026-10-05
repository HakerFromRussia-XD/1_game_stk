from pathlib import Path
import json,sys,hashlib,xml.etree.ElementTree as E,shutil
r=Path(__file__).resolve().parent;f=r/'candidate';src=r/'before';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
before=parse(src/'lap-catch_track.spm');after=parse(f/'lap-catch_track.spm');proof_path=r/'route-material-proof.json'
if proof_path.exists():
 proof=json.loads(proof_path.read_text())['outputBuffers'];reconstructed={i:[] for i in range(len(before['buffers']))};assert len(proof)==len(after['buffers'])
 for row,b in zip(proof,after['buffers']):
  original=before['buffers'][row['originalBuffer']];ids=row['originalVertexIds'];assert len(ids)==len(b['vertices'])
  for oi,v in zip(ids,b['vertices']):assert (v['position'],v['normal'])==(original['vertices'][oi]['position'],original['vertices'][oi]['normal'])
  for j in range(0,len(b['indices']),3):reconstructed[row['originalBuffer']].append(tuple(ids[k] for k in b['indices'][j:j+3]))
 for i,b in enumerate(before['buffers']):assert sorted(reconstructed[i])==sorted(tuple(b['indices'][j:j+3]) for j in range(0,len(b['indices']),3)),i
else:
 assert len(before['buffers'])==len(after['buffers'])
 for a,b in zip(before['buffers'],after['buffers']):
  assert a['indices']==b['indices'];assert [(v['position'],v['normal']) for v in a['vertices']]==[(v['position'],v['normal']) for v in b['vertices']]
for n in ['track.xml','graph.xml','quads.xml','bumper.spm','box.spm','zap.spm']:assert (src/n).read_bytes()==(f/n).read_bytes(),n
s=E.parse(src/'scene.xml').getroot();t=E.parse(f/'scene.xml').getroot();shared=json.loads((r/'shared-runtime.json').read_text());adapted=set(shared['adaptedOriginalPlacements'])
for a,b in zip(s,list(t)[:len(s)]):
 assert a.tag==b.tag
 if a.tag in ['sun','sky-box']:continue
 if a.get('id') in adapted:
  aa=dict(a.attrib);bb=dict(b.attrib);aa.pop('name');bb.pop('name');assert aa==bb;continue
 assert E.tostring(a)==E.tostring(b),(a.tag,a.get('id'))
# All effective physical attributes retained under each new visual material name.
oldmat={e.get('name'):e for e in E.parse(repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app/data/textures/materials.xml').getroot()};oldmat.update({e.get('name'):e for e in E.parse(src/'materials.xml').getroot()});newmat={e.get('name'):e for e in E.parse(f/'materials.xml').getroot()}
visual={'name','normal-map','gloss-map','shader','graphical-effect','color','backface-culling','disable-z-write','lightmap','alpha','mirror-axis','clampU','clampV'}
for row in json.loads((r/'material-remap.json').read_text()):
 old=oldmat.get(row['old'].replace('stk','fluxara_drift'),oldmat.get(row['old']))
 if old is None:continue
 new=newmat.get(row['new']);assert new is not None,row
 assert {k:v for k,v in old.attrib.items() if k not in visual}=={k:v for k,v in new.attrib.items() if k not in visual},row
 assert [E.tostring(e) for e in old]==[E.tostring(e) for e in new],row
# Every material partition retains the physical attributes of its original visual slot.
if proof_path.exists():
 for row in json.loads(proof_path.read_text())['outputBuffers']:
  old=newmat.get(row.get('sourceMaterial'));new=newmat.get(row.get('outputMaterial'))
  if old is None:old=E.Element('material')
  if new is None:new=E.Element('material')
  assert {k:v for k,v in old.attrib.items() if k not in visual}=={k:v for k,v in new.attrib.items() if k not in visual},row['outputBuffer']
  assert [E.tostring(e) for e in old]==[E.tostring(e) for e in new],row['outputBuffer']
# Archive only local visual files no longer referenced by runtime SPM, material XML or scene XML. Original music kept.
refs=set()
for p in f.glob('*.spm'):
 for pair in parse(p)['materials']:refs.update(pair)
for e in E.parse(f/'materials.xml').getroot():
 for k,v in e.attrib.items():
  if k in ['name','normal-map','gloss-map','lightmap']:refs.add(v)
for e in t.iter():
 for k,v in e.attrib.items():
  if k in ['texture','sh-texture','model']:refs.update(v.split())
refs.add('screenshot.png');archived=[];archive=r/'archived-unused';archive.mkdir(exist_ok=True)
for p in list(f.iterdir()):
 if p.suffix.lower() in ['.png','.jpg','.jpeg'] and p.name not in refs:shutil.move(p,archive/p.name);archived.append(p.name)
(r/'archived-unused.json').write_text(json.dumps(archived,indent=2))
# Count logical triangles using highest visual LOD per placement, recursively resolving shared wrappers.
def tris(name,visited=None):
 visited=set() if visited is None else visited;assert name not in visited,name;visited=visited|{name};folder=repo/'iosApp/FluxaraResources/library'/name;root=E.parse(folder/'node.xml').getroot();count=0;models=[e for e in root.findall('object') if e.get('model') and e.get('interaction')!='physicsonly']
 for g in root.findall('./lod/group'):
  if list(g):models.append(list(g)[0])
 for e in models:count+=sum(len(b['indices'])//3 for b in parse(folder/e.get('model'))['buffers'])
 for e in root.findall('library'):count+=tris(e.get('name'),visited)
 return count
orig=sum(len(b['indices'])//3 for b in before['buffers'])+sum(tris(e.get('name')) for e in s.findall('library'));new=sum(len(b['indices'])//3 for b in after['buffers'])+sum(tris(e.get('name')) for e in t.findall('library'))
origbytes=json.loads((r/'baseline.json').read_text())['originalBytes'];trackbytes=sum(p.stat().st_size for p in f.iterdir() if p.is_file());total=trackbytes+shared['newSharedBytes'];a={'originalBytes':origbytes,'trackFolderBytes':trackbytes,'newSharedBytes':shared['newSharedBytes'],'trackAndNewSharedBytes':total,'byteChangePercent':(total/origbytes-1)*100,'originalTrianglesIncludingSharedInstances':orig,'newTrianglesIncludingSharedInstances':new,'triangleChangePercent':(new/orig-1)*100,'newSharedPlacementCount':shared['newPlacementCount'],'protectedXmlExact':True,'allOriginalMeshPositionsNormalsIndicesExact':True,'allGameplaySceneNodesExact':True,'physicalMaterialPropertiesExact':True,'weightNotIncreased':total<=origbytes,'triangleBudgetPassed':abs(new/orig-1)<=.2}
(r/'preservation-audit.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2));assert a['weightNotIncreased'] and a['triangleBudgetPassed']
