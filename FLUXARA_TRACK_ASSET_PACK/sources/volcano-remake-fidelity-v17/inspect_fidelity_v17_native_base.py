from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v17';a=json.loads((r/'fidelity-v16/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);out=[]
for o in bpy.data.objects:
 if o.type=='MESH'and len(o.data.polygons)in [604,72]:out.append({'name':o.name,'mesh':o.data.name,'triangles':len(o.data.polygons),'materials':[m.name if m else None for m in o.data.materials],'source_model':o.get('source_model'),'hidden':o.hide_render,'collections':[c.name for c in o.users_collection]})
(w/'native-base-inspection.json').write_text(json.dumps(out,indent=2));print('V17_NATIVE_BASE_MESHES',out,flush=True)
