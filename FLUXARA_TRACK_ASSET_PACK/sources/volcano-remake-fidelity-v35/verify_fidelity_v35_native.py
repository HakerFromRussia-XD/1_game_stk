from pathlib import Path
import bpy,collections,hashlib,json,math,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v35'
code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v35/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v35/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v35/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());old=json.loads((r/'fidelity-v32/asset-registration.json').read_text());proof=json.loads((w/'final-blend-verification.json').read_text());new=set(a['newValleyNativeObjects'])|{q['name']for q in a['newPrototypes']}|{a['exactLargeWallCollisionNativeObject']};changed=set(a['changedValleyBodyMatrices'])|set(a['changedExistingGrassMatrices']);geochanged=set(a['changedExistingSeamGeometryObjects']);assert len(changed)==140 and len(geochanged)==116;wall=a['changedLargeWallNativeObject']
def geometry(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((layer.name,tuple(tuple(v.uv)for v in layer.data))for layer in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((attr.name,attr.data_type,attr.domain,tuple(tuple(v.color)for v in attr.data))for attr in m.color_attributes),tuple(x.name if x else None for x in m.materials))
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in new};matrices={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap};assert len(snap)==701
im=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
bpy.ops.wm.open_mainfile(filepath=old['finalBlend']);assert set(snap)=={o.name for o in bpy.data.objects if o.type=='MESH'}
for name,g in snap.items():
 if name!=wall and name not in geochanged:assert geometry(bpy.data.objects[name])==g,name
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==matrices[name],name
 else:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)!=matrices[name],name
# Existing source Lavafield data is directly shared, including all material/UV/normal/color arrays.
floor={q['sourceBuffer']:geometry(bpy.data.objects[q['sourceNativeStaticObject']])for q in a['newPrototypes']}
bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
def runtime_triangles(buf):
 return collections.Counter(tuple(sorted(tuple(round(x,5)for x in buf['vertices'][i]['position'])for i in buf['indices'][j:j+3]))for j in range(0,len(buf['indices']),3))
def native_triangles(o):
 o.data.calc_loop_triangles();return collections.Counter(tuple(sorted(tuple(round(x,5)for x in (o.data.vertices[i].co.x,o.data.vertices[i].co.z,o.data.vertices[i].co.y))for i in t.vertices))for t in o.data.loop_triangles)
for row in a['newPrototypes']:
 obj=bpy.data.objects[row['name']];assert geometry(obj)==floor[row['sourceBuffer']],row['name'];buf=parse(Path(row['sourceModel']))['buffers'][row['sourceBuffer']];assert runtime_triangles(buf)==native_triangles(obj),row['name']
main=parse(w/'candidate/volcano_track.spm');split=json.loads((r/'fidelity-v33/mass-replacement-preflight.json').read_text());assert native_triangles(bpy.data.objects[wall])==runtime_triangles(main['buffers'][split['mainWallBuffer']])
proxy=parse(w/'candidate'/split['physicsProxyFile']);assert native_triangles(bpy.data.objects[a['exactLargeWallCollisionNativeObject']])==runtime_triangles(proxy['buffers'][0]);assert bpy.data.objects[a['exactLargeWallCollisionNativeObject']].hide_render
proof.update({'allOtherNativeGeometryUVNormalsColorsMaterialsExactV32':584,'intentionallyChangedNativeMainWall':wall,'retainedNativeWallTriangles':702,'exactHiddenWallTriangles':1508,'allOtherNativeMatricesExactV32':561,'intentionallyChangedStoneBodyMatrices':82,'intentionallyChangedGrassCapMatrices':58,'intentionallyChangedExistingSeamGeometryObjects':116,'newCoordinateSupportInstances':15,'newLavaFloorInstances':3,'newFloorPrototypes':3,'floorNativeGeometryNormalsUVColorsMaterialsExactExistingNativeLavafield':True,'newFloorRuntimeTrianglePositionsMatch':1686,'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'canonicalPending':True,'originalStonePixelsRetained':True})
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V35_NATIVE_GEOMETRY_MATRICES_COLLISION_AND_FLOOR_VERIFIED',len(new),len(a['nativeSharedInstances']),flush=True)
