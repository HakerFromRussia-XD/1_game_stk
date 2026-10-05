from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v15/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v15/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v15/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v14/asset-registration.json').read_text());proof=json.loads((w/'castle-atmosphere-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
angles=[];vertices=0
for row in a['newPrototypes']:
 o=bpy.data.objects[row['name']];b=parse(row['sourceModel'])['buffers'][0];assert len(o.data.polygons)==len(b['indices'])//3;assert [m.name for m in o.data.materials]==row['materials'];col=o.data.color_attributes['Color']
 for p in o.data.polygons:
  for j,loopid in enumerate(p.loop_indices):
   v=b['vertices'][b['indices'][p.index*3+2-j]];loop=o.data.loops[loopid];assert tuple(o.data.vertices[loop.vertex_index].co)==(v['position'][0],v['position'][2],v['position'][1]);vertices+=1
   if v.get('uv'):
    uv=o.data.uv_layers.active.data[loopid].uv;assert abs(uv[0]-v['uv'][0])<1e-5 and abs(uv[1]-(1-v['uv'][1]))<1e-5
   actual=col.data[loopid].color;expected=[x/255 for x in v.get('color',(255,255,255))]+[1];assert max(abs(actual[k]-expected[k])for k in range(4))<1e-6
   q=v['normal'];vv=[]
   for shift in [0,10,20]:
    h=(q>>shift)&1023;vv.append((h-1024 if h>511 else h)/511)
   n=Vector((vv[0],vv[2],vv[1]));n.normalize();actual=o.data.corner_normals[loopid].vector;assert actual.length>.9;angles.append(math.degrees(n.angle(actual)))
assert max(angles)<1,max(angles)
def geometry(o):
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple(tuple(v.uv)for v in m.uv_layers.active.data)if m.uv_layers.active else(),tuple(tuple(n.vector)for n in m.corner_normals),tuple(tuple(c.color)for c in m.color_attributes['Color'].data)if m.color_attributes.get('Color')else())
newnames={q['name']for q in a['newPrototypes']}|{q['name']for q in a['nativeSharedInstances']if q['name'].startswith('VRV15_')or q['name'].endswith('_Cap')}|{q['name']for q in a['nativeOriginalObjects']if q['name'].startswith('VRV15_')};changed=set(a['castleSmokeChangedNativeObjectNames'])|{'VRV8_PooledTower_0','VRV8_PooledTower_1'};snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames|changed};transforms={o.name:[list(v)for v in o.matrix_world]for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames};mats={o.name:[m.name if m else None for m in o.data.materials]for o in bpy.data.objects if o.type=='MESH'and o.name not in newnames|changed};packedhash=hashlib.sha256(next(n.image for n in bpy.data.materials['VRV15_BrickAlias_0'].node_tree.nodes if n.type=='TEX_IMAGE').packed_file.data).hexdigest();assert packedhash==hashlib.sha256(Path(proof['globalBrickTexture']).read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g,name
for name,matrix in transforms.items():assert [list(v)for v in bpy.data.objects[name].matrix_world]==matrix,name
for name,mm in mats.items():
 previous=[m.name if m else None for m in bpy.data.objects[name].data.materials];converted=[('VRV15_BrickAlias_'+str(['VRV4E_castelwall.jpg','VRV4E_castelwall.jpg.001'].index(n)))if n in ['VRV4E_castelwall.jpg','VRV4E_castelwall.jpg.001']else n for n in previous];assert mm==converted,(name,mm,converted)
p=w/'final-blend-verification.json';d=json.loads(p.read_text());d.update({'existingUnaffectedNativeGeometryUVsNormalsColorsExactV14':len(snap),'allExistingNativeObjectWorldMatricesExactV14':len(transforms),'newPrototypeCount':len(a['newPrototypes']),'newPrototypeIndexedCornersChecked':vertices,'maxNewPrototypeNormalAngleDegrees':max(angles),'sharedCastleBodyUsedByBothVariants':True,'brickPackedImageHashExactOriginal':True,'retiredOldPrototypesReplacedOnlyInCandidate':a['retiredPrototypeNames'],'upperWeightAndProtectedCourseChecks':str(w/'preservation-verification.json')});p.write_text(json.dumps(d,indent=2));print('V15_NATIVE_SHARED_CASTLES_SMOKE_AND_STONE_VERIFIED',len(snap),max(angles),flush=True)
