import bpy,json,hashlib,shutil
from pathlib import Path
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');r=Path(__file__).resolve().parent;root=r.parent;canonical=repo/'FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend';backup=r/'canonical-before-material-retention.blend'
if not backup.exists():shutil.copy2(canonical,backup)
bpy.ops.wm.open_mainfile(filepath=str(canonical));bpy.context.preferences.filepaths.save_version=0;restored=[];images={}
for folder in ['dp-motorsports-rework','lap-catch-rework','motorsport-land-rework','summit-run-rework']:
 a=json.load(open(root/folder/'asset-registration.json'));missing=[q['name'] for q in a['materials'] if bpy.data.materials.get(q['name']) is None]
 if missing:
  with bpy.data.libraries.load(a.get('visualLibrary',a.get('library')),link=False) as(src,dst):
   assert all(n in src.materials for n in missing),(folder,missing);dst.materials=list(missing)
  assert {m.name for m in dst.materials}==set(missing),(folder,missing,[m.name for m in dst.materials]);restored.extend([{'map':folder,'name':n} for n in missing])
 for q in a['materials']:
  m=bpy.data.materials[q['name']];m.use_fake_user=True
  if not m.use_nodes or 'textures' not in a:continue
  for node in m.node_tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   name=Path(node.image.filepath).name;row=a['textures'][name];p=Path(row['packPath']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];key=str(p)
   if key not in images:im=bpy.data.images.load(str(p),check_existing=False);im.pack();images[key]=im
   node.image=images[key]
# Materials are catalogued independently of objects. Keep them on subsequent saves
# even when no currently appended object uses a particular surface material.
for m in bpy.data.materials:m.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(canonical));(r/'catalog-material-retention.json').write_text(json.dumps({'restoredMaterials':restored,'standaloneMaterialsRetainedOnSave':True,'sourceRuntimeAssetsChanged':False},indent=2));print('CATALOG_MATERIALS_RETAINED',len(restored))
