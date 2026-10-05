from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v21';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v21/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v21/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v21/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v20/asset-registration.json').read_text());proof=json.loads((w/'crest-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
angles=[];corners=0;face_offset=0;obj=bpy.data.objects[a['newPrototypes'][0]['name']];assert [m.name for m in obj.data.materials]==a['newPrototypes'][0]['materials']
def verify_buffer(o,b,start,material):
    global corners
    for fi in range(len(b['indices'])//3):
        p=o.data.polygons[start+fi];assert p.material_index==material
        for j,loopid in enumerate(p.loop_indices):
            v=b['vertices'][b['indices'][fi*3+2-j]];loop=o.data.loops[loopid];assert tuple(o.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1]);corners+=1
            uv=o.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-v['uv'][0])<1e-5 and abs(uv[1]-(1-v['uv'][1]))<1e-5
            expected=[x/255 for x in v.get('color',(255,255,255))]+[1];assert max(abs(o.data.color_attributes['Color'].data[loopid].color[k]-expected[k])for k in range(4))<1e-6
            q=v['normal'];vv=[]
            for shift in [0,10,20]:
                h=(q>>shift)&1023;vv.append((h-1024 if h>511 else h)/511)
            n=Vector((vv[0],vv[2],vv[1]));n.normalize();angles.append(math.degrees(n.angle(o.data.corner_normals[loopid].vector)))
for bi,b in enumerate(parse(proof['newSharedCrestModel'])['buffers']):verify_buffer(obj,b,face_offset,bi);face_offset+=len(b['indices'])//3
collider=bpy.data.objects[a['originalCentralCrestNativeCollider']];verify_buffer(collider,parse(w/'candidate'/proof['sourceColliderModel'])['buffers'][0],0,0);assert max(angles)<1
for name,texture in [('VRV4E_Rock13_col.jpg',proof['existingRuntimeTextures'][1]),('VRV4E_vr_moss_palette.jpg',proof['existingRuntimeTextures'][0])]:
    assert all(hashlib.sha256(n.image.packed_file.data).hexdigest()==hashlib.sha256(Path(texture).read_bytes()).hexdigest()for n in bpy.data.materials[name].node_tree.nodes if n.type=='TEX_IMAGE')
def geometry(o):
    m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),tuple(tuple(c.color)for c in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else(),[list(v)for v in o.matrix_world],[m.name if m else None for m in m.materials])
newnames={q['name']for q in a['newPrototypes']}|{a['centralCrestNativeInstance'],a['originalCentralCrestNativeCollider'],a['nativeCentralSurfaceWithoutCrest']}
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames}
retained=geometry(bpy.data.objects[a['nativeCentralSurfaceWithoutCrest']]); kept_mat=[p.material_index for p in bpy.data.objects[a['nativeCentralSurfaceWithoutCrest']].data.polygons]
bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
original=bpy.data.objects[a['nativeCentralSurfaceWithoutCrest']];g=geometry(original);kept=a['retainedNativeCentralFaceIndices'];loops=[i for fi in kept for i in original.data.polygons[fi].loop_indices]
assert retained[0]==g[0] and retained[1]==tuple(g[1][fi]for fi in kept) and retained[2]==tuple(g[2][i]for i in loops) and retained[4]==tuple(g[4][i]for i in loops) and retained[5:]==g[5:]
assert kept_mat==[original.data.polygons[fi].material_index for fi in kept]
normal_angles=[math.degrees(Vector(n).angle(Vector(g[3][i])))for n,i in zip(retained[3],loops)];assert max(normal_angles)<.1
p=w/'final-blend-verification.json';data=json.loads(p.read_text());data.update({'allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV20':len(snap),'retainedCentralNativeTriangles':len(kept),'retainedCentralNativePositionsUVsColorsMatricesMaterialsExact':True,'retainedCentralNormalMaxAngleDegrees':max(normal_angles),'newPrototypeCount':1,'newIndexedCornersCheckedIncludingOriginalCollider':corners,'maxNewNormalAngleDegrees':max(angles),'existingStoneAndGreenPackedImagesReused':True,'newTexturePixels':False,'newMaterialCount':0,'sourceCrestCollisionIndexedAttributesVerified':True});p.write_text(json.dumps(data,indent=2));print('V21_NATIVE_ROUNDED_CREST_AND_RETAINED_SOURCE_VERIFIED',len(snap),len(kept),max(normal_angles),flush=True)
