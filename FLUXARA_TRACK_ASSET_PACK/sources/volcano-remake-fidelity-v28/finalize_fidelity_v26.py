from pathlib import Path
import bpy,json,sys,shutil,xml.etree.ElementTree as E
from mathutils import Vector,Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v26';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod=pack/'models/volcano-remake-fidelity-v26';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v24/asset-registration.json').read_text());p=json.loads((w/'cliff-changes.json').read_text());assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
original=bpy.data.objects['VR_OriginalSurface_011'];source=original.data;assert len(source.polygons)==596
stone=bpy.data.materials['VRV4E_Rock13_col.jpg']
removed=[p for p in source.polygons if source.materials[p.material_index]==stone];kept=[p for p in source.polygons if source.materials[p.material_index]!=stone]
assert len(removed)==64 and len(kept)==532
assert max(abs(original.matrix_world[k][j]-Matrix.Identity(4)[k][j])for k in range(4)for j in range(4))<1e-6
def subset(name,faces):
    m=bpy.data.meshes.new(name);m.from_pydata([tuple(v.co)for v in source.vertices],[],[tuple(p.vertices)for p in faces]);m.update()
    for mat in source.materials:m.materials.append(mat)
    for p,q in zip(m.polygons,faces):p.material_index=q.material_index;p.use_smooth=q.use_smooth
    loops=[i for p in faces for i in p.loop_indices]
    m.uv_layers.new(name=source.uv_layers.active.name).data.foreach_set('uv',[x for i in loops for x in source.uv_layers.active.data[i].uv])
    m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER').data.foreach_set('color',[x for i in loops for x in source.color_attributes['Color'].data[i].color])
    m.normals_split_custom_set([tuple(source.corner_normals[i].vector)for i in loops]);m.update();return m
collider=bpy.data.objects.new('VRV26_OriginalCentralStoneCollision',subset('VRV26_OriginalCentralStoneCollisionMesh',removed));collider.matrix_world=original.matrix_world.copy()
next(c for c in bpy.data.collections if 'Protected'in c.name).objects.link(collider);collider.hide_set(True);collider.hide_render=True
scene=E.parse(w/'candidate/scene.xml').getroot();colxml=scene.find('object[@id="VRV26_OriginalCentralStoneCollision"]');xml=scene.find('library[@id="VRV26_RoundedCentralStone_000"]')
collider['source_model']=p['originalCollider'];collider['source_xml']=E.tostring(colxml,encoding='unicode');collider['protected_course_geometry']=True
original.data=subset('VRV26_OriginalSurfaceWithoutCentralStone',kept);original['source_model']=str(w/'candidate/volcano_track.spm')
path=Path(p['newSharedModel']);buf=parse(path)['buffers'][0]
proto=bpy.data.objects.new('VRV26_Prototype_RoundedCentralStone',native_mesh('VRV26_RoundedCentralStoneMesh',buf,[stone]))
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True
proto['asset_id']='volcano-fidelity-v26-rounded-central-stone';proto['source_model']=str(path);proto['source_buffer']=0
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':1024,'materials':[stone.name],
     'sourcePoolObjectId':'volcano-fidelity-v14-central-rock','role':'Rounded copy of central64-face stone support. Original stone pixels and UVs retained with interpolated coordinates on new vertices. Exact source64-face collision separate. Whole local bounds, origin, axes and instance transform retained.'}
instance=bpy.data.objects.new(xml.get('id'),proto.data);instance.matrix_world=original.matrix_world.copy();bpy.data.collections['Volcano Remake Shared Instances'].objects.link(instance)
instance['source_model']=str(path);instance['source_prototype']=proto.name;instance['asset_id']=proto['asset_id'];instance['source_xml']=E.tostring(xml,encoding='unicode');instance['shared_runtime_library']=xml.get('name');instance['protected_course_geometry']=False
a['nativeSharedInstances'].append({'name':instance.name,'prototype':proto.name,'library':xml.get('name'),'matrix':[list(v)for v in instance.matrix_world],'sourcePlacementId':instance.name})
a['nativeOriginalObjects'].append({'name':collider.name,'model':Path(p['originalCollider']).name,'matrix':[list(v)for v in collider.matrix_world],'sourceXml':collider['source_xml']})
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['reusedPrototypes']=[];a['reusedMaterialVariants']=[]
a['centralStoneNativeInstance']=instance.name;a['originalCentralStoneNativeCollider']=collider.name;a['originalCentralSurfaceWithoutStone']=original.name
a['removedNativeCentralStoneFaceIndices']=[p.index for p in removed];a['retainedNativeCentralFaceIndicesV26']=[p.index for p in kept]
a['runtimeLibrarySources'][xml.get('name')]=p['newSharedLibrary']
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(xml.get('name')+'/'+filename).write((Path(p['newSharedLibrary'])/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Rounded Central Stone Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
for f in [path,w/'candidate/volcano_track.spm',Path(p['originalCollider'])]:shutil.copy2(f,mod/f.name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V26 rounds central stone support, source64-face collider retained. Other source geometry and stone pixels retained. Rejected outer-wall V25 not included. Native candidate; reference fidelity/integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('V26_NATIVE_CENTRAL_STONE_AND_COLLIDER_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
