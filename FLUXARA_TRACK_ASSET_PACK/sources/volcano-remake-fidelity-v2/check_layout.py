import bpy,json,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;a=json.load(open(r/'asset-registration.json'));bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for i in range(4):
  s=e.get('p'+str(i));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
vs=[(p[0],p[2],p[1]) for q in qs for p in q];road=BVHTree.FromPolygons(vs,[tuple(i*4+j for j in range(4)) for i in range(len(qs))]);bad=[];overhead=[];below=[];checked=0
for row in a['nativeSharedInstances']:
 o=bpy.data.objects[row['name']];hits=[];oh=0;bh=0;checked+=1
 for v in o.data.vertices:
  p=o.matrix_world@v.co;hit=road.ray_cast(Vector((p.x,p.y,300)),Vector((0,0,-1)),600)[0]
  if hit:
   delta=p.z-hit.z
   if -.05<=delta<3.5:hits.append(float(delta))
   elif delta>=3.5:oh+=1
   else:bh+=1
 if hits:bad.append({'instance':row['name'],'verticesInDrivingEnvelope':len(hits),'minClearance':min(hits),'maxClearance':max(hits)})
 if oh:overhead.append({'instance':row['name'],'verticesAbove3_5m':oh})
 if bh:below.append({'instance':row['name'],'verticesBelowRoad':bh})
(r/'layout-verification.json').write_text(json.dumps({'nativeMeshPartsChecked':checked,'verticesWithinDrivingEnvelope':bad,'overheadCrownProjection':overhead,'belowElevatedRoadProjection':below,'scope':'Placed runtime mesh vertex check against original drive quads; 13 footprint samples also used for new placements; not a continuous swept collision proof'},indent=2));print('LAYOUT_CHECKED',checked,'bad',bad)
assert not bad
