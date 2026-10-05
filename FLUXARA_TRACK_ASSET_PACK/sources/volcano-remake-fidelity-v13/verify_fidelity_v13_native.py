from pathlib import Path
import bpy,json,math,hashlib,sys
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v13';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v13/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v13/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v13/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v12/asset-registration.json').read_text());proof=json.loads((w/'fountain-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
# Indexed native geometry and custom corner normals for the new shared model.
proto=bpy.data.objects['VRV13_Prototype_LavaFountain'];b=parse(proof['newSharedModel'])['buffers'][0];assert len(proto.data.polygons)==452;angles=[]
for poly in proto.data.polygons:
 for j,loopid in enumerate(poly.loop_indices):
  source=b['vertices'][b['indices'][poly.index*3+2-j]];loop=proto.data.loops[loopid];assert tuple(proto.data.vertices[loop.vertex_index].co)==(source['position'][0],source['position'][2],source['position'][1]);uv=proto.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-source['uv'][0])<1e-6 and abs(uv[1]-(1-source['uv'][1]))<1e-6
  packed=source['normal'];raw=[]
  for shift in [0,10,20]:
   v=(packed>>shift)&1023;raw.append((v-1024 if v>511 else v)/511)
  n=Vector((raw[0],raw[2],raw[1]));n.normalize();actual=proto.data.corner_normals[loopid].vector;assert actual.length>.9;angles.append(math.degrees(n.angle(actual)))
assert max(angles)<1,max(angles)
for row in a['newMaterialVariants']:
 mat=bpy.data.materials[row['name']];images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'];assert images and all(im.name==proof['textureAlias']for im in images);assert all(hashlib.sha256(im.packed_file.data).hexdigest()==a['textures'][proof['textureAlias']]['sha256']for im in images)
excluded=set(a['fountainChangedMainMeshObjects'])|{'VRV13_Prototype_LavaFountain','VRV13_PooledLavaFountain','VRV13_OriginalLavaColumnCollision'}
def geom(o):
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals))
snap={o.name:(geom(o),[list(v)for v in o.matrix_world])for o in bpy.data.objects if o.type=='MESH'and o.name not in excluded};cloud=a['fountainCloudObject'];matsetup={q['name']:bpy.data.materials[q['name']]for q in a['newMaterialVariants']}
# Snapshot material inputs and links without relying on Blender objects after loading another file.
def settings(m):
 nodes=[(n.name,n.type,[(i.name,tuple(i.default_value)if hasattr(i.default_value,'__len__')and not isinstance(i.default_value,str)else i.default_value)for i in n.inputs if hasattr(i,'default_value')])for n in m.node_tree.nodes];links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name)for l in m.node_tree.links];return nodes,links
ms={new['sourceMaterialId']:settings(bpy.data.materials[new['name']])for new in a['newMaterialVariants']};bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,(g,matrix)in snap.items():
 o=bpy.data.objects[name];assert geom(o)==g,name
 if name!=cloud:assert [list(v)for v in o.matrix_world]==matrix,name
for row in a['sourceLavaMaterialRows']:assert settings(bpy.data.materials[row['name']])==ms[row['id']],row['name']
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'newFountainTriangles':452,'fountainNativeIndexedPositionsUVsExactSPM':True,'newFountainMaxNormalAngleDegrees':max(angles),'existingNativeGeometryUVsNormalsExactV12ExceptMainLavaColumn':len(snap),'existingObjectMatricesExactV12ExceptAshColumn':True,'materialSettingsExactSourceVariants':6,'sharedLavaImagePixelsExactOriginal':True,'newFountainInstanceLinked':True,'hiddenOriginalCollisionRetained':True});p.write_text(json.dumps(d,indent=2));print('V13_NATIVE_PRESERVATION_AND_FOUNTAIN_VERIFIED',max(angles),flush=True)
