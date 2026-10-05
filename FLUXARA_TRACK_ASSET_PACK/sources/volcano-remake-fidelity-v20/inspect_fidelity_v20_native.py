from pathlib import Path
import bpy,json,collections
r=Path(__file__).resolve().parent;w=r/'fidelity-v20';a=json.loads((r/'fidelity-v19/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);rows=[]
for o in bpy.data.objects:
 if o.type=='MESH'and any(m and m.name=='VRV4E_vr_moss_palette.jpg'for m in o.data.materials):
  rows.append({'name':o.name,'mesh':o.data.name,'sourceModel':o.get('source_model'),'polygons':len(o.data.polygons),'materialPolygonCounts':dict(collections.Counter(o.data.materials[p.material_index].name for p in o.data.polygons)),'hideRender':o.hide_render,'hidden':o.hide_get()})
(w/'native-green-inspection.json').write_text(json.dumps(rows,indent=2));print('V20_NATIVE_GREEN_REGION_INSPECTED',rows,flush=True)
