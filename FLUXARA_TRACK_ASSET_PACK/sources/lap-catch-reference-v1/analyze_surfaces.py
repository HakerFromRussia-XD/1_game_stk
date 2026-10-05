import bpy,sys,json,collections,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/lap-catch_track.spm');vs=[];fs=[];ids=[]
for bi,b in enumerate(d['buffers']):
 off=len(vs);vs.extend(v['position'] for v in b['vertices'])
 for j in range(0,len(b['indices']),3):fs.append(tuple(off+k for k in b['indices'][j:j+3]));ids.append(bi)
bvh=BVHTree.FromPolygons(vs,fs,all_triangles=True);quads=[];rows=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));q.append(quads[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 quads.append(q);c=sum([Vector(p) for p in q],Vector())/4;hit,n,i,dist=bvh.find_nearest(c);rows.append({'quad':len(quads)-1,'center':list(c),'buffer':ids[i],'material':d['materials'][d['buffers'][ids[i]]['material']][0],'distance':dist})
(r/'driving-surface-inspection.json').write_text(json.dumps(rows,indent=2));print('ROUTE_SURFACES',collections.Counter((a['buffer'],a['material']) for a in rows));print('BEACH',collections.Counter((a['buffer'],a['material']) for a in rows if a['center'][2]<-200 and a['center'][0]<0));print('DIST_MAX',max(a['distance'] for a in rows))
