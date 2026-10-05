import bpy,json,sys,hashlib,struct,collections
from pathlib import Path
from mathutils import Vector,kdtree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rows=json.load(open(r/'native-inspection.json'));row=rows[0];bpy.ops.wm.open_mainfile(filepath=row['path']);bpy.context.view_layer.update();meshes=[];groups=collections.defaultdict(list)
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not (o.name.startswith('Orbital_V5_WarmLamp_') or o.name in ['Orbital_V5_ModuleTop','Orbital_V5_ModuleBottom','Orbital_V5_ModuleLeft','Orbital_V5_ModuleRight']):continue
 o.data.calc_loop_triangles()
 # Include complete local mesh and material appearance. No merge across reskins.
 signature=hashlib.sha256(str(([list(v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],[[tuple(q.uv) for q in l.data] for l in o.data.uv_layers],[m.name if m else None for m in o.data.materials])).encode()).hexdigest();groups[signature].append(o)
for sig,os in groups.items():
 if len(os)>=2 and len(os)*len(os[0].data.loop_triangles)>=40:meshes.extend(os)
verts=[];owners=[]
for i,o in enumerate(meshes):
 for v in o.data.vertices:
  p=o.matrix_world@v.co;verts.append((p.x,p.z,p.y));owners.append(i)
kd=kdtree.KDTree(len(verts))
for i,v in enumerate(verts):kd.insert(v,i)
kd.balance();d=parse(r/'before/orbital_scenery.spm');counts=collections.Counter();chunks=collections.defaultdict(list);ambiguities=0
for bi,b in enumerate(d['buffers']):
 ids=[]
 for v in b['vertices']:
  p,idx,dist=kd.find(v['position']);ids.append(owners[idx] if dist<.0002 else -1)
 for ti in range(0,len(b['indices']),3):
  tri=b['indices'][ti:ti+3];q={ids[i] for i in tri}
  if len(q)==1 and -1 not in q:owner=q.pop();counts[owner]+=1;chunks[owner].append([bi,ti])
result=[]
for i,o in enumerate(meshes):
 expected=len(o.data.loop_triangles);result.append({'name':o.name,'matchedTriangles':counts[i],'expectedTriangles':expected,'complete':counts[i]==expected,'matched':chunks[i],'materials':[m.name if m else None for m in o.data.materials],'matrix':[list(v) for v in o.matrix_world]})
(r/'orbital-match.json').write_text(json.dumps(result,indent=2));print('BAKED_MATCH_READY',len(result),sum(q['complete'] for q in result),sum(q['matchedTriangles'] for q in result if q['complete']),flush=True)
