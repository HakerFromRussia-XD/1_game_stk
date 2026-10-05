from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v17';a=json.loads((w/'asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;o=bpy.data.objects['VRV14_Prototype_CentralRock'];source=r/'fidelity-v14/candidate/volcano_track.spm';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
assert len(o.data.polygons)==len(parse(source)['buffers'][2]['indices'])//3==72;o['source_model']=str(source);o['source_buffer']=2;bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);print('V17_HISTORICAL_SOURCE_METADATA_MATCHES_ORIGINAL_72_TRIANGLES',flush=True)
