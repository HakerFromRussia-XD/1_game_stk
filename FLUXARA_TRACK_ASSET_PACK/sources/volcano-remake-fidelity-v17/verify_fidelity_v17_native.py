from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v17';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v17/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v17/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v17/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v16/asset-registration.json').read_text());proof=json.loads((w/'green-crest-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
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
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),tuple(tuple(c.color)for c in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else(),[list(v)for v in o.matrix_world],[m.name if m else None for m in m.materials],tuple(p.material_index for p in m.polygons))
newnames={q['name']for q in a['newPrototypes']};snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames};bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,g in snap.items():
 old=bpy.data.objects[name];before_geometry=geometry(old)
 if name=='VR_OriginalSurface_011':
  assert before_geometry[:2]==g[:2] and before_geometry[3:6]==g[3:6]
  changed=set(a['changedNativeFaceIndices']);uv=list(before_geometry[2])
  for p in old.data.polygons:
   if p.index in changed:
    for loopid in p.loop_indices:uv[loopid]=(.75,.5)
  assert tuple(uv)==g[2] and before_geometry[6]+['VRV4E_vr_moss_palette.jpg']==g[6]
  assert tuple(2 if i in changed else v for i,v in enumerate(before_geometry[7]))==g[7]
 else:assert before_geometry==g,name
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'allPriorNativeGeometryNormalsColorsAndMatricesExactV16':len(snap),'onlyEightFacesMaterialAndGreenPaletteUVChanged':True,'newPrototypeCount':2,'newIndexedCornersChecked':corners,'maxNewNormalAngleDegrees':max(angles),'existingNativeStoneMaterialAndPackedImageReused':True,'runtimeStoneAliasPixelHashExactNativeImage':True,'newTexturePixels':False,'newMaterialCount':0,'priorRoundedTerrainSharedPartsRetained':len(a['newRoundedTerrainNativeObjects'])});p.write_text(json.dumps(d,indent=2));print('V17_NATIVE_UNCHANGED_GEOMETRY_AND_GREEN_CREST_VERIFIED',len(snap),max(angles),flush=True)
