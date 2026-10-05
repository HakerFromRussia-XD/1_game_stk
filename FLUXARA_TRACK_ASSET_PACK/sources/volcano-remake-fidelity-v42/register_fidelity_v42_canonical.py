from pathlib import Path
import bpy,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent;w=r/'fidelity-v42';a=json.loads((w/'asset-registration.json').read_text());pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend'
assert json.loads((w/'final-blend-verification.json').read_text())['stonePackedPixelsExact'];backup=w/'canonical-before-v40.blend'
if not backup.exists():subprocess.run(['/bin/cp','-c',str(canon),str(backup)],check=True)
bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
geometry_cache={}
def geo(o):
 m=o.data
 if m.as_pointer()in geometry_cache:return geometry_cache[m.as_pointer()]
 h=hashlib.sha256()
 for q in [tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(n.vector)for n in m.corner_normals),tuple((layer.name,tuple(tuple(v.uv)for v in layer.data))for layer in m.uv_layers),tuple((c.name,c.domain,c.data_type,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(mat.name if mat else None for mat in m.materials)]:h.update(repr(q).encode())
 result=h.hexdigest();geometry_cache[m.as_pointer()]=result;return result
snapshot={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};oldmats=set(bpy.data.materials);oldimages=set(bpy.data.images);oldimagehash={im.name:hashlib.sha256(im.packed_file.data).hexdigest()for im in oldimages if im.packed_file};oldmatnames={m.name for m in oldmats}
assert all(not bpy.data.objects.get(q['name'])for q in a['newPrototypes']);assert all(not bpy.data.materials.get(q['name'])for q in a['newMaterialVariants'])
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[q['name']for q in a['newPrototypes']];dest.materials=[q['name']for q in a['newMaterialVariants']]
# Unify reused images by exact packed bytes; all previous images and materials stay the same datablocks.
image_map={}
for im in set(bpy.data.images)-oldimages:
 if im.packed_file:
  sha=hashlib.sha256(im.packed_file.data).hexdigest();matches=[x for x in oldimages if x.packed_file and oldimagehash[x.name]==sha]
  if matches:image_map[im]=sorted(matches,key=lambda x:x.name)[0]
for mat in set(bpy.data.materials)-oldmats:
 if mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE'and node.image in image_map:node.image=image_map[node.image]
col=bpy.data.collections.new('Volcano Remake Candidate V42 Stone Scale Variant');bpy.context.scene.collection.children.link(col)
for obj,row in zip(dest.objects,a['newPrototypes']):
 assert obj.name==row['name'];obj.data.materials.clear()
 for name in row['materials']:obj.data.materials.append(bpy.data.materials[name])
 col.objects.link(obj);obj.hide_set(True);obj.hide_render=True
for mat in dest.materials:mat.use_fake_user=True
for mat in list(set(bpy.data.materials)-oldmats):
 mat.use_fake_user=False
 if mat.users==0:bpy.data.materials.remove(mat)
for im in set(bpy.data.images)-oldimages:
 im.use_fake_user=False
 if im.users==0:bpy.data.images.remove(im)
for name,sha in snapshot.items():assert geo(bpy.data.objects[name])==sha,name
assert all(bpy.data.materials.get(m.name)==m for m in oldmats);assert all(bpy.data.images.get(im.name)==im for im in oldimages)
for name,sha in oldimagehash.items():assert hashlib.sha256(bpy.data.images[name].packed_file.data).hexdigest()==sha,name
for name in ['fluxara_chalet_window','fluxara_cottage_windows','LCV1_fluxara_chalet_window.png','LCV1_fluxara_cottage_windows.png']:
 nodes=[n for n in bpy.data.materials[name].node_tree.nodes if n.type=='EMISSION'];assert nodes and all(n.inputs['Strength'].default_value>=1 for n in nodes)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));bpy.ops.wm.open_mainfile(filepath=str(canon));geometry_cache.clear()
for name,sha in snapshot.items():assert geo(bpy.data.objects[name])==sha,name
for row in a['newPrototypes']:
 obj=bpy.data.objects[row['name']];obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==row['triangles'];assert [m.name for m in obj.data.materials]==row['materials']
for name,sha in oldimagehash.items():assert hashlib.sha256(bpy.data.images[name].packed_file.data).hexdigest()==sha,name
for name in ['fluxara_chalet_window','fluxara_cottage_windows','LCV1_fluxara_chalet_window.png','LCV1_fluxara_cottage_windows.png']:
 nodes=[n for n in bpy.data.materials[name].node_tree.nodes if n.type=='EMISSION'];assert nodes and all(n.inputs['Strength'].default_value>=1 for n in nodes)
proof={'path':str(canon),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest(),'allPreviousNativeMeshGeometryNormalsUVColorsMaterialsExactAfterReopen':len(snapshot),'allPreviousImagePackedBytesExact':len(oldimagehash),'previousMaterialsRetained':len(oldmatnames),'newPrototypes':len(a['newPrototypes']),'newMaterialVariants':len(a['newMaterialVariants']),'newNativeImagePixels':False,'previousHouseWindowEmissionPreserved':True,'newPrototypeTriangleAndMaterialBindingsVerified':True}
(w/'canonical-registration.json').write_text(json.dumps(proof,indent=2));n=json.loads((w/'final-blend-verification.json').read_text());n['canonicalPending']=False;n['canonical']=proof;(w/'final-blend-verification.json').write_text(json.dumps(n,indent=2));print('V42_CANONICAL_REOPEN_AND_PREVIOUS_ASSETS_VERIFIED',len(snapshot),flush=True)
