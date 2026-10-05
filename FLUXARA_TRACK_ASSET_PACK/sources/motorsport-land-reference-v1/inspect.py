import bpy,sys,json
from pathlib import Path
r=Path(__file__).resolve().parent;bpy.ops.wm.read_factory_settings(use_empty=True);sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register();bpy.ops.screen.spm_import(filepath=str(r/'before/motorsport-land_track.spm'),extra_tex_path=str(r/'before'));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'source-inspection.blend'));print('IMPORTED',len(bpy.data.objects))
