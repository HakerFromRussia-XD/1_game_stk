import bpy,json,math,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;quads=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));v=quads[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split()));q.append(v)
 quads.append(q)
rv=[(v[0],v[2],0) for q in quads for v in q];rf=[tuple(i*4+j for j in range(4)) for i in range(len(quads))];bvh=BVHTree.FromPolygons(rv,rf);bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));overlaps=[]
for row in json.loads((r/'placements.json').read_text()):
 o=bpy.data.objects[row['name']];hits=0
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if bvh.ray_cast(Vector((p.x,p.y,10)),Vector((0,0,-1)),20)[0]:hits+=1
 if hits:overlaps.append({'name':o.name,'hits':hits,'role':row['role']})
(r/'layout-verification.json').write_text(json.dumps({'protectedDrivingQuads':len(quads),'newInstancesChecked':len(json.loads((r/'placements.json').read_text())),'verticesProjectedOnDrivingCorridor':overlaps},indent=2));print('LAYOUT_CHECKED',len(overlaps),overlaps[:10])
