from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v35';a=json.loads((w/'asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
for i,row in enumerate(a['newPrototypes']):
 row['sourceBuffer']=[2,1,0][i];row['sourceNativeStaticObject']=f'VR_OriginalStatic_0_{i}';obj=bpy.data.objects[row['name']];obj['source_buffer']=row['sourceBuffer'];original=bpy.data.objects[row['sourceNativeStaticObject']];assert obj.data==original.data
 for record in a['objects']:
  if record['id']==row['id']:record.update(row)
bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in a['newPrototypes']},fake_user=True,compress=True)
bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V35_FLOOR_SOURCE_BUFFER_PROVENANCE_CORRECTED_NO_GEOMETRY_CHANGE',flush=True)
