import bpy,json
from pathlib import Path
p=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend')
with bpy.data.libraries.load(str(p),link=False) as(a,b):
 b.objects=[n for n in a.objects if any(k in n for k in ['SkiDash_WarmCliff_v1','SkiDash_CanyonMesa_','SkiDash_CascadeFlow_v2_00','Fluxara_ReusedWinterFirB_High'])]
rows=[]
for o in b.objects:
 if o and o.type=='MESH':
  o.data.calc_loop_triangles();rows.append({'name':o.name,'triangles':len(o.data.loop_triangles),'bounds':list(map(list,o.bound_box)),'dimensions':list(o.dimensions),'materials':[m.name for m in o.data.materials]})
Path('/Users/motoricallc/Downloads/stk-code-master/output/summit-run-rework/pooled-mesh-inspection.json').write_text(json.dumps(rows,indent=2))
print('INSPECTED',[(v['name'],v['triangles']) for v in rows])
