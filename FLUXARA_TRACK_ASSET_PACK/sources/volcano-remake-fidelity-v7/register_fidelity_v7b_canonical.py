from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v7b';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());rows=a['newPrototypes'];backup=w/'canonical-before-v7b.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
for o in list(bpy.data.objects):
 if str(o.get('asset_id','')).startswith('volcano-fidelity-v7b-'):bpy.data.objects.remove(o,do_unlink=True)
materials_before=set(bpy.data.materials)
with bpy.data.libraries.load(a['visualLibrary'],link=False) as(src,dest):
 dest.objects=[q['name']for q in rows]
col=bpy.data.collections.get('Volcano Remake Candidate V7B Effects') or bpy.data.collections.new('Volcano Remake Candidate V7B Effects')
if col.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(col)
for o,row in zip(dest.objects,rows):
 assert o.name==row['name'];o.data.materials.clear()
 for name in row['materials']:o.data.materials.append(bpy.data.materials[name])
 col.objects.link(o);o.hide_set(True);o.hide_render=True
for m in set(bpy.data.materials)-materials_before:
 if m.users==0:bpy.data.materials.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':len(rows),'totalCandidateObjects':len(a['objects']),'newMaterials':0,'reusedTextures':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V7B_CANONICAL_REGISTERED',len(rows),flush=True)
