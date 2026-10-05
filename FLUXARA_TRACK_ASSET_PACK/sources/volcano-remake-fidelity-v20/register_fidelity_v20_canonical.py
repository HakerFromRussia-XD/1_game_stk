from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v20';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());assert json.loads((w/'final-blend-verification.json').read_text())['existingNativeStoneMaterialAndPackedImageReused'];backup=w/'canonical-before-v20.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0;materials_before=set(bpy.data.materials);images_before=set(bpy.data.images);assert all(not bpy.data.objects.get(q['name'])for q in a['newPrototypes'])
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[q['name']for q in a['newPrototypes']]
col=bpy.data.collections.new('Volcano Remake Candidate V20 Rounded Terrain');bpy.context.scene.collection.children.link(col)
for obj,row in zip(dest.objects,a['newPrototypes']):
 assert obj.name==row['name'];obj.data.materials.clear()
 for name in row['materials']:obj.data.materials.append(bpy.data.materials[name])
 col.objects.link(obj);obj.hide_set(True);obj.hide_render=True
for m in set(bpy.data.materials)-materials_before:
 m.use_fake_user=False
 if m.users==0:bpy.data.materials.remove(m)
for im in set(bpy.data.images)-images_before:
 im.use_fake_user=False
 if im.users==0:bpy.data.images.remove(im)
assert set(bpy.data.materials)==materials_before
assert set(bpy.data.images)==images_before
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':1,'newMaterials':0,'newRuntimeTextureAliases':1, 'newImagePixels':False,'existingStoneTextureAndMaterialsReused':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V20_CANONICAL_REGISTERED',flush=True)
