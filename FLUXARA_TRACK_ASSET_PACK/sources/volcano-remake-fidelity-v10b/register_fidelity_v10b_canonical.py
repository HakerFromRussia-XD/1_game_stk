from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v10b';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());backup=w/'canonical-before-v10b.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0;materials_before=set(bpy.data.materials);assert all(not bpy.data.objects.get(q['name'])for q in a['newPrototypes'])
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[q['name']for q in a['newPrototypes']]
col=bpy.data.collections.new('Volcano Remake Candidate V10B Textured Cliffs');bpy.context.scene.collection.children.link(col)
for obj,row in zip(dest.objects,a['newPrototypes']):
 assert obj.name==row['name'];obj.data.materials.clear()
 for name in row['materials']:obj.data.materials.append(bpy.data.materials[name])
 col.objects.link(obj);obj.hide_set(True);obj.hide_render=True
for m in set(bpy.data.materials)-materials_before:
 if m.users==0:bpy.data.materials.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':4,'newMaterials':0,'newTextureFiles':0,'existingStoneTextureAndMaterialsReused':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V10B_CANONICAL_REGISTERED',flush=True)
