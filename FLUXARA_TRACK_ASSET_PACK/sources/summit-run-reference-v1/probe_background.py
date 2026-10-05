import bpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/ancient-summits_track.spm');vs=[];fs=[]
for i in [6,9]:
 b=d['buffers'][i];off=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']);fs.extend(tuple(off+j for j in b['indices'][a:a+3]) for a in range(0,len(b['indices']),3))
t=BVHTree.FromPolygons(vs,fs,all_triangles=True);rows=[]
for z in [55,70,90]:
 for x in [-120,-90,-60,-30,0,30,60,90]:
  p,n,_,_=t.ray_cast(Vector((x,z,300)),Vector((0,0,-1)),600)
  if p:rows.append({'x':x,'z':z,'height':round(p.z,2),'normal':list(n)})
(r/'background-probe.json').write_text(json.dumps(rows,indent=2));print(rows)
