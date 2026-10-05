from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v9';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());backup=w/'canonical-before-v9.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
assert not bpy.data.objects.get('VRV9_Prototype_CastleTower');assert not bpy.data.materials.get('VRV9_CastlePalette')
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[q['name']for q in a['newPrototypes']]
col=bpy.data.collections.new('Volcano Remake Candidate V9 Castles');bpy.context.scene.collection.children.link(col)
for obj in dest.objects:
    assert obj.name=='VRV9_Prototype_CastleTower';assert obj.data.materials[0].name=='VRV9_CastlePalette';col.objects.link(obj);obj.hide_set(True);obj.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':1,'newMaterials':1,'newTextureFiles':1,'texturePixelsReused':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V9_CANONICAL_REGISTERED',flush=True)
