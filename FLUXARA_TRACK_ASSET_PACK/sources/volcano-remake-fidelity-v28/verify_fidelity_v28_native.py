from pathlib import Path
import bpy,json,hashlib,math,sys
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v28'
code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v28/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v28/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v28/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());a27=json.loads((r/'fidelity-v27/asset-registration.json').read_text());parts=json.loads((r/'fidelity-v27/column-changes.json').read_text())['parts']
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
corners=0;angles=[]
for row in parts:
    obj=bpy.data.objects[row['nativePrototype']];buf=parse(row['model'])['buffers'][0];assert len(obj.data.polygons)==len(buf['indices'])//3
    for face in obj.data.polygons:
        for j,lid in enumerate(face.loop_indices):
            v=buf['vertices'][buf['indices'][3*face.index+2-j]];loop=obj.data.loops[lid]
            assert tuple(obj.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1])
            if 'uv'in v:
                uv=obj.data.uv_layers.active.data[lid].uv;assert abs(uv[0]-v['uv'][0])<1e-5 and abs(uv[1]-(1-v['uv'][1]))<1e-5
            color=[x/255 for x in v.get('color',(255,255,255))]+[1];assert max(abs(obj.data.color_attributes['Color'].data[lid].color[k]-color[k])for k in range(4))<1e-6
            packed=v['normal'];nn=[(packed>>shift)&1023 for shift in [0,10,20]];nn=[(x-1024 if x>511 else x)/511 for x in nn]
            n=Vector((nn[0],nn[2],nn[1]));n.normalize();actual=obj.data.corner_normals[lid].vector;angles.append(math.degrees(n.angle(actual)));corners+=1
assert max(angles)<1
def geometry(obj):
    m=obj.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(v.vector)for v in m.corner_normals),tuple(tuple(v.color)for v in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else(),[m.name if m else None for m in m.materials])
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'};matrices={o.name:[list(v)for v in o.matrix_world]for o in bpy.data.objects if o.type=='MESH'}
changed=set(a['changedVisibleCliffNativeObjectNames'])|set(a27['changedStoneColumnNativeObjects'])
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];image=next(n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(image.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
materials_before=set(bpy.data.materials.keys());images_before=set(bpy.data.images.keys());bpy.ops.wm.open_mainfile(filepath=str(r/'fidelity-v26/native/Volcano Remake.blend'))
assert set(snap)=={o.name for o in bpy.data.objects if o.type=='MESH'}and materials_before==set(bpy.data.materials.keys())and images_before==set(bpy.data.images.keys())
roundoff=0
for name,g in snap.items():
    o=bpy.data.objects[name];assert geometry(o)==g,name
    if name not in changed:roundoff=max(roundoff,max(abs(o.matrix_world[i][j]-matrices[name][i][j])for i in range(4)for j in range(4)))
assert roundoff<1e-5,roundoff
proof=json.loads((w/'final-blend-verification.json').read_text());proof.update({'allNativeMeshGeometryUVsNormalsColorsAndMaterialsExactV26':len(snap),'intentionallyChangedCoordinatePartMatricesVsV26':len(changed),'otherMatrixMaxFloatRoundoffVsV26':roundoff,'reusedPartIndexedCornersChecked':corners,'maxReusedPartNormalAngleDegrees':max(angles),'stonePackedImagePixelsRetained':True,'newNativeGeometry':False,'newMaterials':0,'newImagePixels':False,'V26CentralSupportPreservationVerifiedSeparately':True})
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V28_NATIVE_REUSED_GEOMETRY_AND_COORDINATES_VERIFIED',len(snap),len(changed),roundoff,flush=True)
