from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
bpy.context.preferences.filepaths.save_version=0
records=[]
for version in ['v10','v10b']:
 w=r/('fidelity-'+version);a=json.loads((w/'asset-registration.json').read_text())
 for path in [a['finalBlend'],a['visualLibrary']]:
  bpy.ops.wm.open_mainfile(filepath=path)
  for row in a['newPrototypes']:
   obj=bpy.data.objects[row['name']];mesh=obj.data;b=parse(row['sourceModel'])['buffers'][row['sourceBuffer']]
   normals=[]
   for loop in mesh.loops:
    packed=b['vertices'][loop.vertex_index]['normal'];bits=[(packed>>(10*k))&1023 for k in range(3)];n=[(x-1024 if x>511 else x)/511 for x in bits];normals.append(Vector((n[0],n[2],n[1])).normalized())
   mesh.normals_split_custom_set(normals);mesh.update()
   bad=[i for i,n in enumerate(mesh.corner_normals) if n.vector.length<.5]
   if bad:
    vertices={mesh.loops[i].vertex_index for i in bad}
    for edge in mesh.edges:
     if any(v in vertices for v in edge.vertices):edge.use_edge_sharp=True
    mesh.update();mesh.normals_split_custom_set(normals);mesh.update()
   remaining=[i for i,n in enumerate(mesh.corner_normals) if n.vector.length<.5]
   print('NORMAL_REPAIR',version,obj.name,'zero-before',len(bad),'zero-after',len(remaining),flush=True)
   assert not remaining,(obj.name,remaining)
   records.append({'version':version,'file':path,'prototype':obj.name,'unitInputNormals':True,'sharpFanBoundaryCornerIds':bad,'remainingZeroNormals':remaining,'positionsTopologyUvsUnchanged':True})
  bpy.ops.wm.save_as_mainfile(filepath=path)
(r/'native-normal-repair.json').write_text(json.dumps(records,indent=2));print('NATIVE_NORMAL_REPAIR_SAVED',flush=True)
