import bpy,json
from pathlib import Path
r=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(r/'fidelity-v24/native/Volcano Remake.blend'))
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('VR_OriginalSurface'):
  rows.append({'name':o.name,'triangles':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'properties':{k:str(o[k]) for k in o.keys()},'matrix':[list(v)for v in o.matrix_world]})
(r/'fidelity-v25/native-source-inspection.json').write_text(json.dumps(rows,indent=2))
print('V25_SOURCE_NATIVE_INSPECTED',flush=True)
