from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v16';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());proof=json.loads((w/'final-blend-verification.json').read_text());assert proof['newRoundedTerrainSharedParts']==116 and proof['existingNativeStoneMaterialAndPackedImageReused']
backup=w/'canonical-before-v16.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
before_mats=set(bpy.data.materials);before_images=set(bpy.data.images)
assert all(not bpy.data.objects.get(q['name'])for q in a['newPrototypes'])
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):
 dest.objects=[q['name']for q in a['newPrototypes']]
 dest.materials=[q['name']for q in a['newMaterialVariants']]
col=bpy.data.collections.new('Volcano Remake Candidate V16 Rounded Stone Terrain');bpy.context.scene.collection.children.link(col)
for obj,row in zip(dest.objects,a['newPrototypes']):
 assert obj.name==row['name'];obj.data.materials.clear()
 for name in row['materials']:obj.data.materials.append(bpy.data.materials[name])
 col.objects.link(obj);obj.hide_set(True);obj.hide_render=True
expected=set(q['name']for q in a['newMaterialVariants'])
for mat in set(bpy.data.materials)-before_mats:
 if mat.name not in expected:
  mat.use_fake_user=False
  assert mat.users==0,mat.name
  bpy.data.materials.remove(mat)
for im in set(bpy.data.images)-before_images:
 im.use_fake_user=False
 assert im.users==0,im.name
 bpy.data.images.remove(im)
assert {m.name for m in set(bpy.data.materials)-before_mats}==expected
assert set(bpy.data.images)==before_images
stone=bpy.data.objects['VRV16_Prototype_StoneBody'].data.materials[0];assert stone==bpy.data.materials['VRV4E_Rock13_col.jpg']
alias=a['runtimeTextureAliases']['fluxara_volcano_stone_shared_v16.jpg'];ims=[n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE'];assert ims and all(hashlib.sha256(im.packed_file.data).hexdigest()==alias['sha256']for im in ims)
bpy.ops.wm.save_as_mainfile(filepath=str(canon))
out={'newObjects':2,'newMaterials':1,'newNativeImages':0,'newRuntimeTextureAliases':1,'stoneImageAndMaterialReusedExactly':True,'otherMaterialsAndImagesRetained':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()};(w/'canonical-registration.json').write_text(json.dumps(out,indent=2));print('V16_CANONICAL_ROUNDED_TERRAIN_REGISTERED',flush=True)
