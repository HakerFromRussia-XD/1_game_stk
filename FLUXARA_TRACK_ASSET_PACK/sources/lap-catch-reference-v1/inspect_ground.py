import sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/lap-catch_track.spm')
for x,z in [(-180,-280),(-155,-285),(-220,-310),(-235,-240),(-215,-260),(-230,-280),(515,450)]:
 hits=[]
 for i,b in enumerate(d['buffers']):
  vs=[tuple(v['position']) for v in b['vertices']];faces=[tuple(b['indices'][j:j+3]) for j in range(0,len(b['indices']),3)];h=BVHTree.FromPolygons(vs,faces,all_triangles=True).ray_cast(Vector((x,220,z)),Vector((0,-1,0)),400)
  if h[0]:hits.append((i,d['materials'][b['material']][0],h[0].y,h[1].y))
 print(x,z,sorted(hits,key=lambda h:-h[2]))
