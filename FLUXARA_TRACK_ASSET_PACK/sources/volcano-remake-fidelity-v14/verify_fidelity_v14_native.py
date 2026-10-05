from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v14';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v14/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v14/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v14/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v13/asset-registration.json').read_text());proof=json.loads((w/'central-rock-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
proto=bpy.data.objects['VRV14_Prototype_CentralRock'];b=parse(w/'candidate/volcano_track.spm')['buffers'][2];assert len(proto.data.polygons)==72;angles=[]
for p in proto.data.polygons:
 for j,loopid in enumerate(p.loop_indices):
  v=b['vertices'][b['indices'][p.index*3+2-j]];loop=proto.data.loops[loopid];assert tuple(proto.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1]);uv=proto.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-v['uv'][0])<1e-6 and abs(uv[1]-(1-v['uv'][1]))<1e-6
  q=v['normal'];vv=[]
  for shift in [0,10,20]:
   h=(q>>shift)&1023;vv.append((h-1024 if h>511 else h)/511)
  n=Vector((vv[0],vv[2],vv[1]));n.normalize();actual=proto.data.corner_normals[loopid].vector;assert actual.length>.9;angles.append(math.degrees(n.angle(actual)))
assert max(angles)<1;assert [m.name for m in proto.data.materials]==['VRV4E_Rock13_col.jpg']
for name in a['centralRockMaterialChangedMeshObjects']:
 mesh=bpy.data.objects[name].data
 for p in mesh.polygons:assert mesh.materials[p.material_index].name==('VRV4E_Rock13_col.jpg'if p.index in proof['originalComponentTriangleIds']else'VRV4E_vr_arch_stone.png')
def geometry(o):
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),[list(v)for v in o.matrix_world])
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name!='VRV14_Prototype_CentralRock'};materials={o.name:[m.name if m else None for m in o.data.materials]for o in bpy.data.objects if o.type=='MESH'and o.name not in a['centralRockMaterialChangedMeshObjects']and o.name!='VRV14_Prototype_CentralRock'};bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
for name,mats in materials.items():assert [m.name if m else None for m in bpy.data.objects[name].data.materials]==mats,name
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'allExistingNativeGeometryUVsNormalsMatricesExactV13':len(snap),'onlyCentral72TriangleMaterialChanged':True,'castlePortalMaterialPreserved':True,'newPrototypeTriangles':72,'maxNewPrototypeNormalAngleDegrees':max(angles),'newMaterials':0,'newTextureFiles':0});p.write_text(json.dumps(d,indent=2));print('V14_NATIVE_GEOMETRY_AND_REUSED_STONE_VERIFIED',max(angles),flush=True)
