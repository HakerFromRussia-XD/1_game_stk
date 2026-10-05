import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/lap-catch_track.spm');vs=[];fs=[]
# The highest original solid surface provides the actual visible support.
for i,b in enumerate(d['buffers']):
 if i in {5,11,13,16,21,23,24,28,30,31,33,36,38,39,40,42,49,57,66,72,73,74}:continue
 off=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']);fs.extend(tuple(off+k for k in b['indices'][j:j+3]) for j in range(0,len(b['indices']),3))
ground=BVHTree.FromPolygons(vs,fs,all_triangles=True)
bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));rows=json.loads((r/'placements.json').read_text());corrections=[]
for row in rows:
 if row['role'] not in {'tower','cliff','waterfall','arch'}:continue
 o=bpy.data.objects[row['name']];hit=ground.ray_cast(Vector((o.location.x,o.location.y,220)),Vector((0,0,-1)),400)[0]
 if hit is None:continue
 old=o.location.z;o.location.z=hit.z+(-.5 if row['role']=='cliff' else 0)
 row['xyz']=[o.location.x,o.location.z,o.location.y];corrections.append({'name':o.name,'oldHeight':old,'newHeight':o.location.z})
(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'landmark-grounding.json').write_text(json.dumps(corrections,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));print('LANDMARKS_GROUNDED',len(corrections))
