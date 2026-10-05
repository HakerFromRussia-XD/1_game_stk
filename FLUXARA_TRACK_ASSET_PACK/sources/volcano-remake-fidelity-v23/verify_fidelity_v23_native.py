from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v23'
code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v23/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v23/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v23/final-blend-verification.json'")
exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());old=json.loads((r/'fidelity-v22/asset-registration.json').read_text())
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
exclude={row['name'],a['changedBackdropNativeInstance']}
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in exclude}
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];image=next(n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE')
assert hashlib.sha256(image.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
bpy.ops.wm.open_mainfile(filepath=old['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV22':len(snap),'newPrototypeCount':1,'newIndexedCornersChecked':corners,'maxNewNormalAngleDegrees':max(angles),'existingNativeStoneTextureAndMaterialReused':True,'newTexturePixels':False,'newMaterialCount':0});p.write_text(json.dumps(d,indent=2))
print('V23_NATIVE_AND_OTHER_MESHES_VERIFIED',len(snap),corners,max(angles),flush=True)
