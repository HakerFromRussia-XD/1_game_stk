from pathlib import Path
import bpy,json,sys,shutil,xml.etree.ElementTree as E
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v29';native=w/'native';native.mkdir(exist_ok=True)
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v29';mod.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v28/asset-registration.json').read_text());p=json.loads((w/'stone-foot-changes.json').read_text());assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];path=Path(p['newSharedModel']);buf=parse(path)['buffers'][0]
proto=bpy.data.objects.new(p['newPrototype'],native_mesh('VRV29_GroundedStoneBodyMesh',buf,[stone]))
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True
proto['asset_id']=p['newPrototypeId'];proto['source_model']=str(path);proto['source_buffer']=0
row={'id':p['newPrototypeId'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':152,'materials':[stone.name],'sourcePoolObjectId':p['sourcePoolObjectId'],'role':'Copied pooled stone component with broader lower body. Original152 triangles/95 vertices, source UVs/RGB, upper body, local bounds/origin/axes and instance transforms retained; lower positions and normals adapted. Stone pixels reused. Source donor untouched.'}
scene=E.parse(w/'candidate/scene.xml').getroot();changed=[]
for q in p['placements']:
    attrs=q['after'];placed=next(v for v in a['nativeSharedInstances']if v.get('sourcePlacementId')==attrs['id']and v['prototype']=='VRV22_Prototype_StoneBody')
    obj=bpy.data.objects[placed['name']];obj.data=proto.data;obj['asset_id']=p['newPrototypeId'];obj['source_model']=str(path);obj['source_prototype']=proto.name;obj['shared_runtime_library']=attrs['name'];obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode')
    placed['prototype']=proto.name;placed['library']=attrs['name'];changed.append(obj.name)
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['reusedPrototypes']=[];a['reusedMaterialVariants']=[]
a['changedGroundedStoneNativeObjects']=changed;a['runtimeLibrarySources'][Path(p['newSharedLibrary']).name]=p['newSharedLibrary']
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(Path(p['newSharedLibrary']).name+'/'+filename).write((Path(p['newSharedLibrary'])/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Grounded Stone Body Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
shutil.copytree(Path(p['newSharedLibrary']),mod/Path(p['newSharedLibrary']).name,dirs_exist_ok=True)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V29 broadens lower stone body for58 existing copied cliff instances. Original stone pixels, local bounds/origin/axes, topology/UV/RGB and instance poses retained. Source donor untouched. Candidate: reference fidelity/production/final/preview integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V29_NATIVE_GROUNDED_STONE_BODY_SAVED',len(changed),len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
