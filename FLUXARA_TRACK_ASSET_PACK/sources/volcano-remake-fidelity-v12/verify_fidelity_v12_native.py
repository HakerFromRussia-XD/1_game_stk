from pathlib import Path
import bpy,json,hashlib,struct
r=Path(__file__).resolve().parent;w=r/'fidelity-v12';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v12/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v12/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v12/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));a=json.loads((w/'asset-registration.json').read_text());before=json.loads((r/'fidelity-v11/asset-registration.json').read_text());snap={};old_names=set(bpy.data.objects.keys())-set(a['newCoordinateGreeneryObjects'])
for name in old_names:
 o=bpy.data.objects[name]
 if o.type=='MESH':snap[name]=(list(tuple(v.co)for v in o.data.vertices),list(tuple(p.vertices)for p in o.data.polygons),[list(row)for row in o.matrix_world])
proto=bpy.data.objects['VRV4E_Prototype_fluxara_driftlib_round_bush_green_v2_main_0'];assert all(bpy.data.objects[name].data==proto.data for name in a['newCoordinateGreeneryObjects']);assert len(a['objects'])==len(before['objects'])==23
bpy.ops.wm.open_mainfile(filepath=before['finalBlend'])
for name,value in snap.items():
 o=bpy.data.objects[name];actual=(list(tuple(v.co)for v in o.data.vertices),list(tuple(p.vertices)for p in o.data.polygons),[list(row)for row in o.matrix_world]);assert actual==value,name
p=w/'final-blend-verification.json';proof=json.loads(p.read_text());proof.update({'existingMeshObjectsPositionsTopologyMatricesExactV11':len(snap),'newGreeneryLinkedToExistingSingleMesh':len(a['newCoordinateGreeneryObjects']),'reusablePrototypeCount':23,'newPrototypeMeshes':0,'newTextures':0});p.write_text(json.dumps(proof,indent=2));print('V12_NATIVE_LINKED_INSTANCES_AND_PRESERVATION_VERIFIED',flush=True)
