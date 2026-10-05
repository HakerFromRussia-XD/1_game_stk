import bpy,json,shutil,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent;pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');a=json.loads((r/'asset-registration.json').read_text());canonical=pack/'blender/FLUXARA_Track_Asset_Library.blend';backup=r/'canonical-before-lap-catch.blend'
if not backup.exists():shutil.copy2(canonical,backup)
bpy.ops.wm.open_mainfile(filepath=str(canonical));bpy.context.preferences.filepaths.save_version=0
ids={q['id'] for q in a['objects']}
for o in list(bpy.data.objects):
 if str(o.get('asset_id','')).startswith('lap-v1-'):
  data=o.data;bpy.data.objects.remove(o,do_unlink=True)
  if data and data.users==0:bpy.data.meshes.remove(data)
for m in list(bpy.data.materials):
 if m.name.startswith('LCV1_'):bpy.data.materials.remove(m,do_unlink=True)
with bpy.data.libraries.load(a['visualLibrary'],link=False) as(src,dest):dest.objects=[q['name'] for q in a['objects']];dest.materials=[q['name'] for q in a['materials']]
col=bpy.data.collections.get('Lap Catch Shared Assets') or bpy.data.collections.new('Lap Catch Shared Assets')
if col.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(col)
for o in dest.objects:
 if o:col.objects.link(o);o.hide_set(True);o.hide_render=True
assert {m.name for m in dest.materials}=={q['name'] for q in a['materials']}
bpy.ops.wm.save_as_mainfile(filepath=str(canonical));(r/'canonical-registration.json').write_text(json.dumps({'objects':len(dest.objects),'materials':len(dest.materials),'path':str(canonical),'bytes':canonical.stat().st_size,'sha256':hashlib.sha256(canonical.read_bytes()).hexdigest()},indent=2));print('CANONICAL_REGISTERED',len(dest.objects),len(dest.materials))
