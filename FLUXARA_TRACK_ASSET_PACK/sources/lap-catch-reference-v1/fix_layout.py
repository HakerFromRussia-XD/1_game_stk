import bpy,json,math,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));rows=json.loads((r/'placements.json').read_text());quads=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));q.append(quads[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 quads.append(q)
vs=[(p[0],p[2],0) for q in quads for p in q];faces=[tuple(i*4+k for k in range(4)) for i in range(len(quads))];road=BVHTree.FromPolygons(vs,faces)
def clear(o,dx=0,dy=0):
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if road.ray_cast(Vector((p.x+dx,p.y+dy,10)),Vector((0,0,-1)),20)[0]:return False
 return True
fixed=[]
for row in rows:
 o=bpy.data.objects[row['name']]
 if clear(o):continue
 found=False
 for dist in range(2,42,2):
  for i in range(16):
   a=i*math.tau/16;dx=math.cos(a)*dist;dy=math.sin(a)*dist
   if clear(o,dx,dy):
    o.location.x+=dx;o.location.y+=dy;row['xyz']=[o.location.x,o.location.z,o.location.y];fixed.append({'name':o.name,'delta':[dx,dy]});found=True;break
  if found:break
 assert found,o.name
(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'placement-corrections.json').write_text(json.dumps(fixed,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));print('PLACEMENTS_CORRECTED',len(fixed))
