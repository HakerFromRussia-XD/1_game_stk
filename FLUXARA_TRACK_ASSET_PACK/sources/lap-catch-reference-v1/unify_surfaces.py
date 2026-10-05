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
cumulative=[];distance=0
for q in quads:
 cumulative.append(distance);distance+=(Vector(q[2])+Vector(q[3])-Vector(q[0])-Vector(q[1])).length/2

def road_uv(p):
 _,_,qi,_=bvh.find_nearest(Vector(p));q=[Vector(v) for v in quads[qi]];a=(q[0]+q[1])/2;b=(q[2]+q[3])/2;forward=b-a;along=max(0,min(1,(Vector(p)-a).dot(forward)/max(forward.length_squared,1e-9)));left=q[0].lerp(q[3],along);right=q[1].lerp(q[2],along);cross=right-left;u=(Vector(p)-left).dot(cross)/max(cross.length_squared,1e-9);return (u,(cumulative[qi]+along*forward.length)/12)

root=E.parse(f/'materials.xml').getroot();mats={e.get('name'):e for e in root};materials=[p[:] for p in d['materials']];groups={};buffers=[];proof=[];count=0
terrain={50,0,2,6,9,10,14,17,18,19,20,22,32,34,35,37,41,43,44,45,46,47,52,54,55,56,61,62,65,67,68,70,71}
for bi,b in enumerate(d['buffers']):
 buckets={'original':[],'road':[],'grass':[],'rock':[]}
 for j in range(0,len(b['indices']),3):
  ids=b['indices'][j:j+3];p=[Vector(b['vertices'][i]['position']) for i in ids];c=sum(p,Vector())/3;n=(p[1]-p[0]).cross(p[2]-p[0]);n.normalize();hit,normal,index,dist=bvh.find_nearest(c)
  road=bi in {2,14,17,22,53,56,62,68,70,71} or bi in terrain and hit is not None and dist<.55 and abs(n.dot(normal))>.75 and abs(n.y)>.45 and all(bvh.find_nearest(v)[3]<1.4 for v in p)
  role='road' if road else ('grass' if abs(n.y)>.68 else 'rock') if bi in terrain else 'original'
  buckets[role].extend(ids)
 for role,ids in buckets.items():
  isroad=role=='road'
  if not ids:continue
  mi=b['material']
  if role!='original':
   old=mats.get(materials[mi][0],E.Element('material'));attrs={k:v for k,v in old.attrib.items() if k not in ['name','normal-map','gloss-map','shader','graphical-effect']};key=(role,json.dumps(attrs,sort_keys=True),str([E.tostring(q) for q in old]))
   if key not in groups:
    ext='.jpg' if role=='road' else '.png';name='lc_unified_'+str(len(groups))+ext;shutil.copy2(f/({'road':'lc_road.jpg','grass':'lc_reference_grass.png','rock':'lc_rock.png'}[role]),f/name);new=copy.deepcopy(old);new.attrib=attrs|{'name':name};root.append(new);groups[key]=len(materials);materials.append([name,''])
   mi=groups[key];count+=len(ids)//3 if isroad else 0
  unique={};newvs=[];newids=[];originalids=[]
  for index in ids:
   if index not in unique:
    unique[index]=len(newvs);v=dict(b['vertices'][index])
    if role!='original':
     p=v['position'];pn=v['normal'];n=[(pn>>(k*10))&1023 for k in range(3)];n=[q-1024 if q>511 else q for q in n];axis=max(range(3),key=lambda k:abs(n[k]));axes=([2,1] if abs(n[0])>abs(n[2]) else [0,1]) if role=='rock' else [k for k in range(3) if k!=axis];tile=8 if role=='road' else 12;v['uv']=(p[axes[0]]/tile,p[axes[1]]/tile);v['color']={'road':(155,161,165),'grass':(185,195,180),'rock':(210,195,188)}[role]
    newvs.append(v);originalids.append(index)
   newids.append(unique[index])
  proof.append({'outputBuffer':len(buffers),'originalBuffer':bi,'originalVertexIds':originalids,'roadMaterialOnly':isroad,'visualRole':role,'sourceMaterial':d['materials'][b['material']][0],'outputMaterial':materials[mi][0]});buffers.append({'vertices':newvs,'indices':newids,'material':mi})
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
