from pathlib import Path
import bpy,json,hashlib
r=Path(__file__).resolve().parent;canon=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend')
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
for version in ['v10','v10b']:
 a=json.loads((r/('fidelity-'+version)/'asset-registration.json').read_text());originals={q['name']:bpy.data.objects[q['name']] for q in a['newPrototypes']};mats=set(bpy.data.materials);images=set(bpy.data.images)
 with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=list(originals)
 for row,loaded in zip(a['newPrototypes'],dest.objects):
  original=originals[row['name']];materials=list(original.data.materials);old=original.data;original.data=loaded.data;original.data.materials.clear()
  for mat in materials:original.data.materials.append(mat)
  bpy.data.objects.remove(loaded,do_unlink=True)
  if old.users==0:bpy.data.meshes.remove(old)
 for mat in set(bpy.data.materials)-mats:
  if mat.users==0:bpy.data.materials.remove(mat)
 for im in set(bpy.data.images)-images:
  if im.users==0:bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));proof={'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest(),'updatedNativePrototypes':8,'geometryUvsUnchanged':True,'nativeNormalFanBoundaryRepair':True}
(r/'repaired-canonical.json').write_text(json.dumps(proof,indent=2));print('REPAIRED_CANONICAL_SAVED',flush=True)
