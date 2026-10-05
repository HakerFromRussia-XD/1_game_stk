from pathlib import Path
import bpy, json, sys, shutil, hashlib, xml.etree.ElementTree as E
from mathutils import Vector

r=Path(__file__).resolve().parent; w=r/'fidelity-v20'; pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod=pack/'models/volcano-remake-fidelity-v20'; mod.mkdir(exist_ok=True)
native=w/'native'; native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v19/asset-registration.json').read_text())
proof=json.loads((w/'terrain-changes.json').read_text())
assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']); bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign')); from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text(); exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper=(r/'finalize_fidelity_v15.py').read_text(); exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
original=bpy.data.objects['VR_OriginalSurface_012']; original_mesh=original.data
assert len(original_mesh.polygons)==427
assert all(original_mesh.materials[p.material_index].name=='VRV4E_vr_moss_palette.jpg'for p in original_mesh.polygons)
mat=bpy.data.materials['VRV4E_vr_moss_palette.jpg']; path=Path(proof['newSharedTerrainModel']); d=parse(path)
proto=bpy.data.objects.new('VRV20_Prototype_RoundedGreenTerrain',native_mesh('VRV20_RoundedGreenTerrainMesh',d['buffers'][0],[mat]))
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto); proto.hide_set(True); proto.hide_render=True
proto['asset_id']='volcano-fidelity-v20-rounded-green-terrain'; proto['source_model']=str(path); proto['source_buffer']=0
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':proof['visualTriangles'],
     'materials':[mat.name],'sourcePoolObjectId':'volcano-fidelity-v17-runtime-volcano-track',
     'role':'Large green terrain surfaces copied from original main decorative buffer, conformingly subdivided and rounded upward away from road. Whole terrain box, origin and axes retained. Original collision geometry retained separately.'}
scene=E.parse(w/'candidate/scene.xml').getroot()
colxml=scene.find('object[@id="VRV20_OriginalGreenTerrainCollision"]')
collision=bpy.data.objects.new(colxml.get('id'),original_mesh.copy()); collision.matrix_world=original.matrix_world.copy()
protected=next(c for c in bpy.data.collections if 'Protected'in c.name); protected.objects.link(collision)
collision.hide_set(True); collision.hide_render=True; collision['source_model']=str(w/'candidate'/proof['sourceColliderModel'])
collision['source_xml']=E.tostring(colxml,encoding='unicode'); collision['preserved_native_source']=original.name
original.data=proto.data; original['source_model']=str(path); original['source_prototype']=proto.name; original['asset_id']=proto['asset_id']
xml=scene.find('library[@id="VRV20_RoundedGreenTerrain_000"]'); original['source_xml']=E.tostring(xml,encoding='unicode'); original['shared_runtime_library']=xml.get('name')
for col in list(original.users_collection):col.objects.unlink(original)
bpy.data.collections['Volcano Remake Shared Instances'].objects.link(original)
a['nativeOriginalObjects']=[q for q in a['nativeOriginalObjects']if q['name']!=original.name]
a['nativeOriginalObjects'].append({'name':collision.name,'model':proof['sourceColliderModel'],'matrix':[list(v)for v in collision.matrix_world],'sourceXml':collision['source_xml']})
assert not any(q['name']==original.name for q in a['nativeSharedInstances'])
a['nativeSharedInstances'].append({'name':original.name,'prototype':proto.name,'library':xml.get('name'),'matrix':[list(v)for v in original.matrix_world],'sourcePlacementId':xml.get('id')})
a['objects'].append(row); a['newPrototypes']=[row]; a['newMaterialVariants']=[]
a['newTerrainNativeInstance']=original.name; a['originalTerrainNativeCollider']=collision.name
a['runtimeLibrarySources'][Path(proof['newSharedTerrainLibrary']).name]=proof['newSharedTerrainLibrary']
for filename in ['node.xml','materials.xml']:
    bpy.data.texts.new(Path(proof['newSharedTerrainLibrary']).name+'/'+filename).write((Path(proof['newSharedTerrainLibrary'])/filename).read_text())
for filename in ['scene.xml','materials.xml']:
    bpy.data.texts[filename].clear(); bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
texture=Path(proof['existingGreenPaletteGlobalAlias']); shipped=pack/'textures/volcano-remake-fidelity-v20'/texture.name
shipped.parent.mkdir(exist_ok=True); shutil.copy2(texture,shipped)
oldtex=a['textures']['vr_moss_palette.jpg']
a['runtimeTextureAliases'][texture.name]={'source':str(texture),'packPath':str(shipped),'bytes':texture.stat().st_size,'sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),
                                        'poolId':'volcano-fidelity-v20-moss-runtime-alias','reusedPixelsPoolId':oldtex['poolId'],'nativeMaterial':mat.name,
                                        'nativePackedImagePreserved':True,'reason':'One runtime global file for retained central crest, three volcano models, copied collision mesh and new terrain library. Existing packed native image retained.'}
for name in proof['textureAliasOnlyOtherModels']:
    for obj in bpy.data.objects:
        if Path(obj.get('source_model','')).name==name:obj['source_model']=str(w/'candidate'/name)
a['visualLibrary']=str(mod/'Volcano Remake Rounded Terrain Library.blend')
bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
for p in [path,w/'candidate/volcano_track.spm',w/'candidate'/proof['sourceColliderModel']]:shutil.copy2(p,mod/p.name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),
          'status':'V20 large rounded green terrain, original collision triangles and stone/road indexed attributes retained. One shared terrain model and global existing green palette. Isolated candidate; visual reference work remains.'})
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend'])
(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('V20_NATIVE_ROUNDED_TERRAIN_AND_ORIGINAL_COLLIDER_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
