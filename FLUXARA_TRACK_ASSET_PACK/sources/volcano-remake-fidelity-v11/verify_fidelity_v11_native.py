from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v11';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v11/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v11/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v11/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());snap={}
for q in a['objects']:
 o=bpy.data.objects[q['name']];snap[o.name]=([(tuple(v.co))for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[(tuple(l.uv))for l in o.data.uv_layers.active.data],[(tuple(n.vector))for n in o.data.corner_normals])
matrices=[]
for q in a['nativeOriginalObjects']:
 if q['name']in a['smokeTransformUpdatedObjects']:
  o=bpy.data.objects[q['name']];err=max(abs(o.matrix_world[i][j]-q['matrix'][i][j])for i in range(4)for j in range(4));assert err<.00001;matrices.append({'object':o.name,'matrixMaxError':err})
bpy.ops.wm.open_mainfile(filepath=json.loads((r/'fidelity-v10b/asset-registration.json').read_text())['finalBlend'])
for name,value in snap.items():
 o=bpy.data.objects[name];actual=([(tuple(v.co))for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[(tuple(l.uv))for l in o.data.uv_layers.active.data],[(tuple(n.vector))for n in o.data.corner_normals]);assert actual==value,name
p=w/'final-blend-verification.json';proof=json.loads(p.read_text());proof.update({'all23PrototypeGeometryUvsNormalsMatchV10B':True,'threeSmokeMatricesMatchXml':matrices,'newModelsOrTextures':0});p.write_text(json.dumps(proof,indent=2));print('V11_NATIVE_GEOMETRY_AND_PLACEMENTS_VERIFIED',flush=True)
