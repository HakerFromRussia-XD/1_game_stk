from pathlib import Path
import bpy,json,sys,copy,shutil,xml.etree.ElementTree as E
from mathutils import Matrix, Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v21';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v21';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v20/asset-registration.json').read_text());proof=json.loads((w/'crest-changes.json').read_text());assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')]);helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
green=bpy.data.materials['VRV4E_vr_moss_palette.jpg'];stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];path=Path(proof['newSharedCrestModel']);d=parse(path)
combined={'vertices':[],'indices':[],'material':0}
for b in d['buffers']:
    offset=len(combined['vertices']);combined['vertices']+=b['vertices'];combined['indices'] +=[i+offset for i in b['indices']]
mesh=native_mesh('VRV21_RoundedCentralCrestMesh',combined,[green,stone]);grass_faces=len(d['buffers'][0]['indices'])//3
for p in mesh.polygons:p.material_index=0 if p.index<grass_faces else 1
proto=bpy.data.objects.new('VRV21_Prototype_RoundedCentralCrest',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True
proto['asset_id']='volcano-fidelity-v21-roundedcentralcrest';proto['source_model']=str(path);proto['source_buffers']='0,1'
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffers':[0,1],'triangles':proof['visibleTriangles'],'materials':[green.name,stone.name],'sourcePoolObjectId':proof['sourcePoolObjectId'],
     'role':'Rounded green central crest follows an inscribed smooth copy of the original rim, with a stone transition into the exact existing stone side. Whole original 72-face cliff object bounds, world axes and origin retained; all original stone triangles/UVs and exact 8-face collision retained.'}
original=bpy.data.objects['VR_OriginalSurface_011'];old_mesh=original.data;assert len(old_mesh.polygons)==604
assert max(abs(original.matrix_world[k][j]-Matrix.Identity(4)[k][j])for k in range(4)for j in range(4))<1e-6
kept=[p for p in old_mesh.polygons if old_mesh.materials[p.material_index]!=green];removed=[p for p in old_mesh.polygons if old_mesh.materials[p.material_index]==green]
assert len(kept)==596 and len(removed)==8
loops=[i for p in kept for i in p.loop_indices];uv=[tuple(old_mesh.uv_layers.active.data[i].uv)for i in loops];colors=[tuple(old_mesh.color_attributes['Color'].data[i].color)for i in loops];normals=[tuple(old_mesh.corner_normals[i].vector)for i in loops]
replacement=bpy.data.meshes.new('VRV21_OriginalSurfaceWithoutCrest');replacement.from_pydata([tuple(v.co)for v in old_mesh.vertices],[],[tuple(p.vertices)for p in kept]);replacement.update()
for mat in old_mesh.materials:replacement.materials.append(mat)
for p,source in zip(replacement.polygons,kept):p.material_index=source.material_index;p.use_smooth=source.use_smooth
replacement.uv_layers.new(name=old_mesh.uv_layers.active.name).data.foreach_set('uv',[x for v in uv for x in v]);replacement.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER').data.foreach_set('color',[x for v in colors for x in v]);replacement.normals_split_custom_set(normals);replacement.update()
original.data=replacement;original['source_model']=str(w/'candidate/volcano_track.spm')
scene=E.parse(w/'candidate/scene.xml').getroot();colxml=scene.find('object[@id="VRV21_OriginalCentralCrestCollision"]');libxml=scene.find('library[@id="VRV21_RoundedCentralCrest_000"]')
cb=parse(w/'candidate'/proof['sourceColliderModel'])['buffers'][0];collider=bpy.data.objects.new(colxml.get('id'),native_mesh('VRV21_OriginalCentralCrestCollisionMesh',cb,[green]));collider.matrix_world=original.matrix_world.copy();next(c for c in bpy.data.collections if 'Protected'in c.name).objects.link(collider);collider.hide_set(True);collider.hide_render=True;collider['source_model']=str(w/'candidate'/proof['sourceColliderModel']);collider['source_xml']=E.tostring(colxml,encoding='unicode')
instance=bpy.data.objects.new(libxml.get('id'),proto.data);instance.matrix_world=original.matrix_world.copy();bpy.data.collections['Volcano Remake Shared Instances'].objects.link(instance);instance['source_model']=str(path);instance['source_prototype']=proto.name;instance['asset_id']=proto['asset_id'];instance['source_xml']=E.tostring(libxml,encoding='unicode');instance['shared_runtime_library']=libxml.get('name')
a['nativeSharedInstances'].append({'name':instance.name,'prototype':proto.name,'library':libxml.get('name'),'matrix':[list(v)for v in instance.matrix_world],'sourcePlacementId':instance.name})
a['nativeOriginalObjects'].append({'name':collider.name,'model':proof['sourceColliderModel'],'matrix':[list(v)for v in collider.matrix_world],'sourceXml':collider['source_xml']})
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['centralCrestNativeInstance']=instance.name;a['originalCentralCrestNativeCollider']=collider.name;a['nativeCentralSurfaceWithoutCrest']=original.name
a['removedNativeCrestFaceIndices']=[p.index for p in removed];a['retainedNativeCentralFaceIndices']=[p.index for p in kept]
a['runtimeLibrarySources'][libxml.get('name')]=proof['newSharedCrestLibrary']
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(libxml.get('name')+'/'+filename).write((Path(proof['newSharedCrestLibrary'])/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Rounded Central Crest Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
for p in [path,w/'candidate/volcano_track.spm',w/'candidate'/proof['sourceColliderModel']]:shutil.copy2(p,mod/p.name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V21 rounded central green crest and stone transition, current stone pixels retained, exact original collision and central object composite bounds preserved. Isolated candidate; other near-road green terrain, cliff placement and lighting unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V21_NATIVE_ROUNDED_CENTRAL_CREST_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
