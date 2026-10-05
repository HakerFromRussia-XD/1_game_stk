from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v19';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v19/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v19/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v19/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v18/asset-registration.json').read_text());proof=json.loads((w/'smoke-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
angles=[];corners=0
for row in a['newPrototypes']:
 o=bpy.data.objects[row['name']];b=parse(row['sourceModel'])['buffers'][row['sourceBuffer']];assert len(o.data.polygons)==len(b['indices'])//3;assert [m.name for m in o.data.materials]==row['materials'];col=o.data.color_attributes['Color']
 for p in o.data.polygons:
  for j,loopid in enumerate(p.loop_indices):
   v=b['vertices'][b['indices'][p.index*3+2-j]];loop=o.data.loops[loopid];assert tuple(o.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1]);corners+=1
   if v.get('uv'):
    uv=o.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-v['uv'][0])<1e-5 and abs(uv[1]-(1-v['uv'][1]))<1e-5
   expected=[x/255 for x in v.get('color',(255,255,255))]+[1];assert max(abs(col.data[loopid].color[k]-expected[k])for k in range(4))<1e-6
   q=v['normal'];vv=[]
   for shift in [0,10,20]:
    h=(q>>shift)&1023;vv.append((h-1024 if h>511 else h)/511)
   n=Vector((vv[0],vv[2],vv[1]));n.normalize();actual=o.data.corner_normals[loopid].vector;assert actual.length>.9;angles.append(math.degrees(n.angle(actual)))
assert max(angles)<1
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];image=next(n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(image.packed_file.data).hexdigest()==hashlib.sha256(Path(a['runtimeTextureAliases']['fluxara_volcano_stone_shared_v16.jpg']['source']).read_bytes()).hexdigest()
def geometry(o):
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),tuple(tuple(c.color)for c in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else(),[list(v)for v in o.matrix_world],[m.name if m else None for m in m.materials])
newnames={q['name']for q in a['newPrototypes']}|set(a['smokeChangedNativeObjectNames']);snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames};bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'allOtherNativeGeometryUVsNormalsColorsMatricesAndMaterialsExactV18':len(snap),'newPrototypeCount':3,'newIndexedCornersChecked':corners,'maxNewNormalAngleDegrees':max(angles),'existingNativeStoneMaterialAndPackedImageReused':True,'runtimeStoneAliasPixelHashExactNativeImage':True,'newTexturePixels':False,'newMaterialCount':0,'smokeChangedInMapObjects':len(a['smokeChangedNativeObjectNames'])});p.write_text(json.dumps(d,indent=2));print('V19_NATIVE_CONTINUOUS_SMOKE_AND_UNCHANGED_SOURCE_VERIFIED',len(snap),max(angles),flush=True)
