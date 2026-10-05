from pathlib import Path
import bpy,json,shutil,sys,xml.etree.ElementTree as E
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v23';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod=pack/'models/volcano-remake-fidelity-v23';mod.mkdir(exist_ok=True)
native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v22/asset-registration.json').read_text());p=json.loads((w/'backdrop-changes.json').read_text())
assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
mat=bpy.data.materials['VRV4E_vr_moss_palette.jpg'];path=Path(p['newSharedTerrainModel']);d=parse(path)
proto=bpy.data.objects.new('VRV23_Prototype_RoundedBackdropTerrain',native_mesh('VRV23_RoundedBackdropTerrainMesh',d['buffers'][0],[mat]))
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True
proto['asset_id']='volcano-fidelity-v23-rounded-backdrop-terrain';proto['source_model']=str(path);proto['source_buffer']=0
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':p['newTerrainTriangles'],'materials':[mat.name],'sourcePoolObjectId':'volcano-fidelity-v20-rounded-green-terrain','role':'Copied V20 terrain model with two broad distant caps subdivided and rounded. All other indexed terrain attributes and original collision untouched. Whole local bounds/origin/axes and instance transform retained. Existing green palette reused.'}
obj=bpy.data.objects['VR_OriginalSurface_012'];oldproto=obj['source_prototype'];assert oldproto=='VRV20_Prototype_RoundedGreenTerrain'
obj.data=proto.data;obj['source_prototype']=proto.name;obj['source_model']=str(path);obj['asset_id']=proto['asset_id']
xml=E.parse(w/'candidate/scene.xml').getroot().find('library[@id="VRV20_RoundedGreenTerrain_000"]')
obj['source_xml']=E.tostring(xml,encoding='unicode');obj['shared_runtime_library']=xml.get('name')
for q in a['nativeSharedInstances']:
    if q['name']==obj.name:q['prototype']=proto.name;q['library']=xml.get('name')
a['objects']=[q for q in a['objects']if q['name']!=oldproto]+[row]
a['newPrototypes']=[row];a['newMaterialVariants']=[];a['changedBackdropNativeInstance']=obj.name;a['retiredBackdropPrototype']=oldproto
a['runtimeLibrarySources'][xml.get('name')]=p['newSharedTerrainLibrary']
for filename in ['node.xml','materials.xml']:
    bpy.data.texts.new(xml.get('name')+'/'+filename).write((Path(p['newSharedTerrainLibrary'])/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Rounded Backdrop Library.blend')
bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True);shutil.copy2(path,mod/path.name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V23 rounds two large backdrop green caps. Stone texture and UVs, source terrain collider, all other V22 geometry and source models unchanged. Native candidate; not integrated.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend'])
(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('V23_NATIVE_ROUNDED_BACKDROP_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
