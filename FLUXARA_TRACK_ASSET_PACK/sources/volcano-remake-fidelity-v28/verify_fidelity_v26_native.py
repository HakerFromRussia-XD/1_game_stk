from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v26'
code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v26/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v26/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v26/final-blend-verification.json'")
exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());old=json.loads((r/'fidelity-v24/asset-registration.json').read_text())
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
row=a['newPrototypes'][0];obj=bpy.data.objects[row['name']];buf=parse(row['sourceModel'])['buffers'][0]
assert len(obj.data.polygons)==len(buf['indices'])//3 and [m.name for m in obj.data.materials]==row['materials']
corners=0;angles=[]
for p in obj.data.polygons:
    for j,loopid in enumerate(p.loop_indices):
        v=buf['vertices'][buf['indices'][3*p.index+2-j]];loop=obj.data.loops[loopid]
        assert tuple(obj.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1])
        uv=obj.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-v['uv'][0])<1e-5 and abs(uv[1]-(1-v['uv'][1]))<1e-5
        expected=[x/255 for x in v.get('color',(255,255,255))]+[1]
        assert max(abs(obj.data.color_attributes['Color'].data[loopid].color[k]-expected[k])for k in range(4))<1e-6
        q=v['normal'];components=[]
        for shift in [0,10,20]:
            h=(q>>shift)&1023;components.append((h-1024 if h>511 else h)/511)
        n=Vector((components[0],components[2],components[1]));n.normalize();actual=obj.data.corner_normals[loopid].vector
        assert actual.length>.9;angles.append(math.degrees(n.angle(actual)));corners+=1
assert max(angles)<1
def geometry(o):
    m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),tuple(tuple(c.color)for c in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else(),[list(v)for v in o.matrix_world],[m.name if m else None for m in m.materials])
def partial(o,indices):
    m=o.data; pp=[m.polygons[i]for i in indices]; loops=[j for p in pp for j in p.loop_indices]
    return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in pp),tuple(tuple(m.uv_layers.active.data[j].uv)for j in loops),tuple(tuple(m.corner_normals[j].vector)for j in loops),tuple(tuple(m.color_attributes['Color'].data[j].color)for j in loops),[v.name if v else None for v in m.materials],[list(v)for v in o.matrix_world])
arch=bpy.data.objects[a['originalCentralSurfaceWithoutStone']]; collider=bpy.data.objects[a['originalCentralStoneNativeCollider']]
arch_geometry=partial(arch,range(len(arch.data.polygons)));collider_geometry=partial(collider,range(len(collider.data.polygons)))
exclude={row['name'],a['originalCentralSurfaceWithoutStone'],a['centralStoneNativeInstance'],a['originalCentralStoneNativeCollider']}
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in exclude}
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];image=next(n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE')
assert hashlib.sha256(image.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
bpy.ops.wm.open_mainfile(filepath=old['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
source=bpy.data.objects[a['originalCentralSurfaceWithoutStone']]
def compare_partial(actual,expected):
    assert all(actual[i]==expected[i]for i in [0,1,2,4,5,6])
    delta=max(abs(x[k]-y[k])for x,y in zip(actual[3],expected[3])for k in range(3))
    assert delta<1e-4,delta
    angles=[math.degrees(math.acos(max(-1,min(1,sum(x[k]*y[k]for k in range(3))/math.sqrt(sum(v*v for v in x)*sum(v*v for v in y))))))for x,y in zip(actual[3],expected[3])]
    assert max(angles)<.01,max(angles)
    return delta
arch_roundoff=compare_partial(partial(source,a['retainedNativeCentralFaceIndicesV26']),arch_geometry)
collider_roundoff=compare_partial(partial(source,a['removedNativeCentralStoneFaceIndices']),collider_geometry)
print('V26_EXTRACTED_NORMAL_COMPONENT_MAX_ROUNDOFF',arch_roundoff,collider_roundoff,flush=True)
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV24':len(snap),'newPrototypeCount':1,'sourceArch532FacesGeometryUVColorsMatricesAndMaterialsExactV24':True,'sourceCentralStone64ColliderFacesExactV24':True,'extractedArchNormalComponentMaxRoundoff':arch_roundoff,'extractedColliderNormalComponentMaxRoundoff':collider_roundoff,'newIndexedCornersChecked':corners,'maxNewNormalAngleDegrees':max(angles),'existingNativeStoneTextureAndMaterialReused':True,'newTexturePixels':False,'newMaterialCount':0});p.write_text(json.dumps(d,indent=2))
print('V26_NATIVE_AND_OTHER_MESHES_VERIFIED',len(snap),corners,max(angles),flush=True)
