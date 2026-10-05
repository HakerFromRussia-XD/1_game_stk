from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v13';assert json.loads((w/'final-blend-verification.json').read_text())['materialSettingsExactSourceVariants']==6
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());backup=w/'canonical-before-v13.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0;objects_before={o.name:[m.name if m else None for m in o.data.materials]for o in bpy.data.objects if o.type=='MESH'};materials_before=set(bpy.data.materials.keys());assert all(not bpy.data.objects.get(q['name'])for q in a['newPrototypes']);assert all(not bpy.data.materials.get(q['name'])for q in a['newMaterialVariants'])
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[q['name']for q in a['newPrototypes']];dest.materials=[q['name']for q in a['newMaterialVariants']]
col=bpy.data.collections.new('Volcano Remake Candidate V13 Lava Fountain');bpy.context.scene.collection.children.link(col)
for o in dest.objects:col.objects.link(o);o.hide_set(True);o.hide_render=True
for name,mats in objects_before.items():assert [m.name if m else None for m in bpy.data.objects[name].data.materials]==mats,name
assert set(bpy.data.materials.keys())-materials_before=={q['name']for q in a['newMaterialVariants']}
for m in dest.materials:m.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':1,'newMaterials':6,'newTextureFiles':1,'newImagePixels':False,'existingCanonicalObjectMaterialBindingsUnchanged':len(objects_before),'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V13_CANONICAL_FOUNTAIN_REGISTERED',flush=True)
