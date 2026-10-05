from pathlib import Path
import bpy,json,sys,shutil,xml.etree.ElementTree as E
from mathutils import Vector, Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v25';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod=pack/'models/volcano-remake-fidelity-v25';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v24/asset-registration.json').read_text());p=json.loads((w/'cliff-changes.json').read_text())
assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
original=next(o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith('VR_OriginalSurface')and len(o.data.polygons)==2210)
assert [m.name for m in original.data.materials]==['VRV4E_Rock13_col.jpg']
assert max(abs(original.matrix_world[k][j]-Matrix.Identity(4)[k][j])for k in range(4)for j in range(4))<1e-6
mat=bpy.data.materials['VRV4E_Rock13_col.jpg'];path=Path(p['newSharedModel']);d=parse(path)
proto=bpy.data.objects.new('VRV25_Prototype_RoundedStoneWalls',native_mesh('VRV25_RoundedStoneWallsMesh',d['buffers'][0],[mat]))
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True
proto['asset_id']='volcano-fidelity-v25-rounded-stone-walls';proto['source_model']=str(path);proto['source_buffer']=0
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':p['targetTriangles'],
     'materials':[mat.name],'sourcePoolObjectId':'volcano-fidelity-v16-runtime-volcano_track',
     'role':'Copy of original large stone terrain. Two connected foreground/side masses subdivided and rounded where road clearance allows; other702 faces exact. Stone image pixels reused, original UV coordinates retained with interpolated new UVs. Component and whole active bounds/origin/axes retained, original collision separate.'}
scene=E.parse(w/'candidate/scene.xml').getroot();colxml=scene.find('object[@id="VRV25_OriginalStoneWallsCollision"]');xml=scene.find('library[@id="VRV25_RoundedStoneWalls_000"]')
collider=bpy.data.objects.new(colxml.get('id'),original.data.copy());collider.matrix_world=original.matrix_world.copy()
next(c for c in bpy.data.collections if 'Protected'in c.name).objects.link(collider);collider.hide_set(True);collider.hide_render=True
collider['source_model']=p['originalCollider'];collider['source_xml']=E.tostring(colxml,encoding='unicode');collider['preserved_native_source']=original.name
original.data=proto.data;original['source_model']=str(path);original['source_prototype']=proto.name;original['asset_id']=proto['asset_id']
original['protected_course_geometry']=False
original['source_xml']=E.tostring(xml,encoding='unicode');original['shared_runtime_library']=xml.get('name')
for col in list(original.users_collection):col.objects.unlink(original)
bpy.data.collections['Volcano Remake Shared Instances'].objects.link(original)
a['nativeOriginalObjects']=[q for q in a['nativeOriginalObjects']if q['name']!=original.name]
a['nativeOriginalObjects'].append({'name':collider.name,'model':Path(p['originalCollider']).name,'matrix':[list(v)for v in collider.matrix_world],'sourceXml':collider['source_xml']})
assert not any(q['name']==original.name for q in a['nativeSharedInstances'])
a['nativeSharedInstances'].append({'name':original.name,'prototype':proto.name,'library':xml.get('name'),'matrix':[list(v)for v in original.matrix_world],'sourcePlacementId':xml.get('id')})
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['reusedPrototypes']=[];a['reusedMaterialVariants']=[]
a['roundedStoneNativeInstance']=original.name;a['originalStoneNativeCollider']=collider.name
a['runtimeLibrarySources'][xml.get('name')]=p['newSharedLibrary']
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(xml.get('name')+'/'+filename).write((Path(p['newSharedLibrary'])/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Rounded Stone Walls Library.blend')
bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
for source in [path,w/'candidate/volcano_track.spm',Path(p['originalCollider'])]:shutil.copy2(source,mod/source.name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V25 smooths two major stone masses, retains actual stone pixels, original UVs with new interpolated coordinates and exact original collision. Original dimensions/origin/axes retained. Isolated candidate; fidelity and integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend'])
(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V25_NATIVE_STONE_MASSES_AND_COLLIDER_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
