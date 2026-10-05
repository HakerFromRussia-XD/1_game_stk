from pathlib import Path
import bpy,sys,json,xml.etree.ElementTree as E,math
from mathutils import Vector
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift')
bpy.ops.wm.read_factory_settings(use_empty=True);sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
bpy.ops.screen.spm_import(filepath=str(r/'before/lap-catch_track.spm'),extra_tex_path=str(r/'before')+';'+str(repo/'iosApp/FluxaraResources/textures'))
rows=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  o.data.calc_loop_triangles();rows.append({'name':o.name,'triangles':len(o.data.loop_triangles),'bounds':[[min((o.matrix_world@v.co)[k] for v in o.data.vertices),max((o.matrix_world@v.co)[k] for v in o.data.vertices)] for k in range(3)]})
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'source-inspection.blend'));(r/'blender-source-inspection.json').write_text(json.dumps(rows,indent=2));print('SOURCE_IMPORTED',len(rows))
