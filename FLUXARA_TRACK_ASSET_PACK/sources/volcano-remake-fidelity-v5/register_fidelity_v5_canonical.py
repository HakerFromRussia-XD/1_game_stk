from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());rows=a['newPrototypes'];backup=w/'canonical-before-v5.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
for o in list(bpy.data.objects):
 if str(o.get('asset_id','')).startswith('volcano-fidelity-v5-'):bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(a['visualLibrary'],link=False) as(src,dest):dest.objects=[q['name']for q in rows]
col=bpy.data.collections.get('Volcano Remake Candidate V5 Clouds') or bpy.data.collections.new('Volcano Remake Candidate V5 Clouds')
if col.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(col)
for o,row in zip(dest.objects,rows):
 assert o.name==row['name'];o.data.materials.clear()
 for name in row['materials']:o.data.materials.append(bpy.data.materials[name])
 col.objects.link(o);o.hide_set(True);o.hide_render=True
for m in list(bpy.data.materials):
 if m.users==0 and m.name.startswith('VRV4E_'):bpy.data.materials.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':len(rows),'totalCandidateObjects':len(a['objects']),'reusedMaterials':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V5_CANONICAL_REGISTERED',len(rows),flush=True)
