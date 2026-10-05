# Assign the existing road triangles a consistent surface; no new road mesh or geometry.
import bpy,sys,json,math,struct,xml.etree.ElementTree as E,copy,shutil,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(f/'lap-catch_track.spm');quads=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));q.append(quads[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 quads.append(q)
verts=[p for q in quads for p in q];faces=[tuple(i*4+j for j in range(4)) for i in range(len(quads))];bvh=BVHTree.FromPolygons(verts,faces)
root=E.parse(f/'materials.xml').getroot();mats={e.get('name'):e for e in root};materials=[p[:] for p in d['materials']];groups={};buffers=[];proof=[];count=0
excluded={5,11,13,16,21,23,24,30,31,33,36,38,39,40,42,49,51,55,57,66,72,73,74,75}
for bi,b in enumerate(d['buffers']):
 buckets={False:[],True:[]}
 for j in range(0,len(b['indices']),3):
  ids=b['indices'][j:j+3];p=[Vector(b['vertices'][i]['position']) for i in ids];c=sum(p,Vector())/3;n=(p[1]-p[0]).cross(p[2]-p[0]);n.normalize();hit,normal,index,dist=bvh.find_nearest(c)
  road=bi not in excluded and hit is not None and dist<.75 and abs(n.dot(normal))>.7 and max((p[a]-p[z]).length for a,z in [(0,1),(1,2),(2,0)])<15 and all(bvh.find_nearest(v)[3]<3 for v in p)
  buckets[road].extend(ids)
 for isroad,ids in buckets.items():
  if not ids:continue
  mi=b['material']
  if isroad:
   old=mats.get(materials[mi][0],E.Element('material'));attrs={k:v for k,v in old.attrib.items() if k not in ['name','normal-map','gloss-map','shader','graphical-effect']};key=(json.dumps(attrs,sort_keys=True),str([E.tostring(q) for q in old]))
   if key not in groups:
    name='lc_route_'+str(len(groups))+'.jpg';shutil.copy2(f/'lc_road.jpg',f/name);new=copy.deepcopy(old);new.attrib=attrs|{'name':name};root.append(new);groups[key]=len(materials);materials.append([name,''])
   mi=groups[key];count+=len(ids)//3
  unique={};newvs=[];newids=[];originalids=[]
  for index in ids:
   if index not in unique:
    unique[index]=len(newvs);v=dict(b['vertices'][index])
    if isroad:
     p=v['position'];pn=v['normal'];n=[(pn>>(k*10))&1023 for k in range(3)];n=[q-1024 if q>511 else q for q in n];axis=max(range(3),key=lambda k:abs(n[k]));axes=[k for k in range(3) if k!=axis];v['uv']=(p[axes[0]]/6,p[axes[1]]/6);v['color']=(155,161,165)
    newvs.append(v);originalids.append(index)
   newids.append(unique[index])
  proof.append({'outputBuffer':len(buffers),'originalBuffer':bi,'originalVertexIds':originalids,'roadMaterialOnly':isroad});buffers.append({'vertices':newvs,'indices':newids,'material':mi})
raw=bytearray(d['raw'][:28]);raw+=struct.pack('<H',len(materials))
for pair in materials:
 for n in pair:e=n.encode();raw+=struct.pack('B',len(e))+e
raw+=struct.pack('<HH',1,len(buffers))
for b in buffers:
 raw+=struct.pack('<IIH',len(b['vertices']),len(b['indices']),b['material'])
 for v in b['vertices']:
  raw+=struct.pack('<3fI',*v['position'],v['normal']);raw+=b'\xff'+bytes(v['color'])
  if materials[b['material']][0]:raw+=struct.pack('<2e',*v['uv'])
  if materials[b['material']][1]:raw+=struct.pack('<2e',*v['uv2'])
 raw+=struct.pack('<'+str(len(b['indices']))+('I' if len(b['vertices'])>65535 else 'H' if len(b['vertices'])>255 else 'B'),*b['indices'])
(f/'lap-catch_track.spm').write_bytes(raw);E.ElementTree(root).write(f/'materials.xml',encoding='unicode');(r/'route-material-proof.json').write_text(json.dumps({'roadTrianglesStyled':count,'outputBuffers':proof,'newRoadMaterialCount':len(groups)},indent=2));print('ROUTE_STYLED_WITH_IDENTICAL_GEOMETRY',count,len(buffers))
