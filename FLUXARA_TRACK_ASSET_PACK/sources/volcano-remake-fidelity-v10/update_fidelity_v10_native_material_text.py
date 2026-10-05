from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';a=json.loads((w/'asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;bpy.data.texts['materials.xml'].clear();bpy.data.texts['materials.xml'].write((w/'candidate/materials.xml').read_text());bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);print('V10_NATIVE_UNUSED_MATERIAL_REMOVED',flush=True)
