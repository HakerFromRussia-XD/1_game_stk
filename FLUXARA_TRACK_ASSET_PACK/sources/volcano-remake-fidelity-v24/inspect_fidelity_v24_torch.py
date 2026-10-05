from pathlib import Path
import bpy,json
p=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/models/shared/fluxara_bronze_wall_torch_v1/Fluxara Bronze Wall Torch.blend')
bpy.ops.wm.open_mainfile(filepath=str(p))
rows=[{'object':o.name,'type':o.type,'vertices':len(o.data.vertices)if o.type=='MESH'else None,'triangles':sum(len(f.vertices)-2 for f in o.data.polygons)if o.type=='MESH'else None,'materials':[m.name for m in o.data.materials]if o.type=='MESH'else []}for o in bpy.data.objects]
print('TORCH_POOL_NATIVE_INSPECTED',json.dumps(rows),flush=True)
Path('output/volcano-remake-rework/torch-native-inspection.json').write_text(json.dumps(rows,indent=2))
