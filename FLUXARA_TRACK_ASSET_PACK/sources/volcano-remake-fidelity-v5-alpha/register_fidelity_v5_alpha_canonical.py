from pathlib import Path
import bpy,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());rows=a['newPrototypes'];backup=w/'canonical-before-v5-alpha.blend'
if not backup.exists():shutil.copy2(canon,backup)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
for o in list(bpy.data.objects):
 if str(o.get('asset_id','')).startswith('volcano-fidelity-v5a-'):bpy.data.objects.remove(o,do_unlink=True)
for m in list(bpy.data.materials):
 if m.name.startswith('VRV5A_'):bpy.data.materials.remove(m,do_unlink=True)
with bpy.data.libraries.load(a['visualLibrary'],link=False) as(src,dest):
 dest.objects=[q['name']for q in rows];dest.materials=['VRV5A_Smoke']
assert dest.materials[0].name=='VRV5A_Smoke'
for node in dest.materials[0].node_tree.nodes:
 if node.type=='TEX_IMAGE':
  entry=a['textures']['vr_volcanic_smoke.png'];assert hashlib.sha256(Path(entry['packPath']).read_bytes()).hexdigest()==entry['sha256'];image=bpy.data.images.load(entry['packPath'],check_existing=False);image.pack();node.image=image

col=bpy.data.collections.get('Volcano Remake Candidate V5 Alpha Effects') or bpy.data.collections.new('Volcano Remake Candidate V5 Alpha Effects')
if col.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(col)
for o,row in zip(dest.objects,rows):
 assert o.name==row['name'];o.data.materials.clear()
 for name in row['materials']:o.data.materials.append(bpy.data.materials[name])
 col.objects.link(o);o.hide_set(True);o.hide_render=True
for m in list(bpy.data.materials):
 if m.users==0 and m.name.startswith('VRV4E_'):bpy.data.materials.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));(w/'canonical-registration.json').write_text(json.dumps({'newObjects':len(rows),'totalCandidateObjects':len(a['objects']),'newMaterials':1,'reusedTextures':True,'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()},indent=2));print('V5_ALPHA_CANONICAL_REGISTERED',len(rows),flush=True)
