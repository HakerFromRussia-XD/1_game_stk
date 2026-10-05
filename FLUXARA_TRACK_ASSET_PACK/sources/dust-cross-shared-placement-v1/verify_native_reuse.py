from pathlib import Path
import bpy,hashlib,json
r=Path(__file__).resolve().parent;w=r/'delivery-v1';n=json.loads((w/'native-verification.json').read_text());canon=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend');before=hashlib.sha256(canon.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=n['finalBlend'])
def shape(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple((tuple(p.vertices),p.material_index)for p in m.polygons),tuple((u.name,tuple(tuple(v.uv)for v in u.data))for u in m.uv_layers),tuple((c.name,c.domain,c.data_type,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes))
def pixels(o):
 result=[]
 for mat in o.data.materials:
  images=[]
  if mat and mat.use_nodes:
   for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE'and node.image:
     im=node.image;raw=im.packed_file.data if im.packed_file else Path(bpy.path.abspath(im.filepath)).read_bytes();images.append(hashlib.sha256(raw).hexdigest())
  result.append(tuple(sorted(images)))
 return tuple(result)
saved={q['canonicalNativePrototype']:(shape(bpy.data.objects[q['nativePrototype']]),pixels(bpy.data.objects[q['nativePrototype']]))for q in n['reusedCanonicalPrototypes']}
with bpy.data.libraries.load(str(canon),link=True)as(src,dest):
 assert all(name in src.objects for name in saved);dest.objects=list(saved)
rows=[]
for o in dest.objects:
 source=saved[o.name];same=shape(o)==source[0];pixelsmatch=pixels(o)==source[1];rows.append({'object':o.name,'localMeshAttributesExact':same,'sourceImageBytesExact':pixelsmatch});assert same and pixelsmatch,o.name
assert hashlib.sha256(canon.read_bytes()).hexdigest()==before
proof={'canonicalPath':str(canon),'canonicalSha256':before,'canonicalNotModified':True,'reusedObjectsVerified':rows,'canonicalReusedPrototypeCount':len(rows),'newCanonicalGeometryMaterialsImages':0};(w/'canonical-reuse-verification.json').write_text(json.dumps(proof,indent=2));print('DUST_SIX_EXISTING_CANONICAL_NATIVE_ASSETS_EXACT_REUSE_VERIFIED',proof,flush=True)
