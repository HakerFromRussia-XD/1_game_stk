import bpy,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent;rows=[]
paths=[('/Users/motoricallc/Downloads/fluxara-drift/.codex-downloads/fluxara-addon-catalog/blender-projects/fluxara-canyon-working.blend','fluxara-canyon'),(str(r.parent/'fluxara-user-ski-dash-final/Ski Dash.blend'),'fluxara-user-ski-dash'),(str(r.parent/'fluxara-user-dust-cross-final/Dust Cross Split Combat.blend'),'fluxara-user-dust-cross-split-combat'),(str(r.parent/'fluxara-user-spell-lab-final/Spell Lab.blend'),'fluxara-user-spell-lab'),(str(r.parent/'fluxara-user-orbital-soccer-final/ORBITAL Simulation - Soccer.blend'),'fluxara-user-orbital-simulation---soccer')]
for path,track in paths:
 bpy.ops.wm.open_mainfile(filepath=path);objects=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();objects.append({'name':o.name,'mesh':o.data.name,'meshUsers':o.data.users,'triangles':len(o.data.loop_triangles),'collections':[c.name for c in o.users_collection],'matrix':[list(v) for v in o.matrix_world],'materials':[m.name if m else None for m in o.data.materials],'properties':{k:str(v)[:600] for k,v in o.items()},'geometryHash':hashlib.sha256(str(([list(v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])).encode()).hexdigest()})
 rows.append({'trackId':track,'path':path,'objects':objects});print('NATIVE_INSPECTED',track,len(objects),flush=True)
(r/'native-inspection.json').write_text(json.dumps(rows,indent=2));print('NATIVE_INSPECTION_READY',flush=True)
