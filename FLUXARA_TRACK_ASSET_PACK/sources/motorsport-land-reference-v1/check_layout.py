import bpy,json,math,sys,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/motorsport-land_track.spm');b=d['buffers'][10];vs=[(v['position'][0],v['position'][2],0) for v in b['vertices']];fs=[tuple(b['indices'][i:i+3]) for i in range(0,len(b['indices']),3)];road=BVHTree.FromPolygons(vs,fs,all_triangles=True);cache={};bad=[]
for row in json.load(open(r/'placements.json')):
 n=row['library'];folder=repo/'iosApp/FluxaraResources/library'/n
 if n not in cache:
  root=E.parse(folder/'node.xml').getroot();cache[n]=[]
  for e in root.findall('object'):
   if not e.get('model'):continue
   assert e.get('xyz','0 0 0')=='0 0 0' and e.get('hpr','0 0 0')=='0 0 0' and e.get('scale','1 1 1')=='1 1 1'
   for b in parse(folder/e.get('model'))['buffers']:cache[n].extend(v['position'] for v in b['vertices'])
 angle=row['rotationZRadians'];ca,sa=math.cos(angle),math.sin(angle);hits=0
 for p in cache[n]:
  x=p[0]*row['scale'][0];z=p[2]*row['scale'][2];xx=row['xyz'][0]+x*ca-z*sa;zz=row['xyz'][2]+x*sa+z*ca
  if road.ray_cast(Vector((xx,zz,10)),Vector((0,0,-1)),20)[0]:hits+=1
 if hits:bad.append({'instance':row['name'],'role':row['role'],'projectedVertices':hits})
(r/'layout-verification.json').write_text(json.dumps({'newInstancesChecked':len(json.load(open(r/'placements.json'))),'runtimeMeshVerticesProjectedOnRoad':bad,'scope':'Runtime mesh vertex projection; placement routine also samples object perimeter'},indent=2));print('LAYOUT_CHECKED',len(bad),bad[:10]);assert not bad
