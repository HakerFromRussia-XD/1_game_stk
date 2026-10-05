from pathlib import Path
import bpy,json,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';a=json.loads((w/'asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0;row=next(q for q in a['newPrototypes']if q['name']=='VRV15_Prototype_GateRoof');assert row['triangles']==160;target=bpy.data.objects[row['name']];other={o.name:o.data.as_pointer()for o in bpy.data.objects if o.type=='MESH'and o!=target};mb=set(bpy.data.materials);ib=set(bpy.data.images)
with bpy.data.libraries.load(a['visualLibrary'],link=False)as(src,dest):dest.objects=[row['name']]
temp=dest.objects[0];assert len(temp.data.polygons)==160;target.data=temp.data;target.data.materials.clear()
for name in row['materials']:target.data.materials.append(bpy.data.materials[name])
bpy.data.objects.remove(temp,do_unlink=True)
for mat in set(bpy.data.materials)-mb:
 if mat.users==0:bpy.data.materials.remove(mat)
for im in set(bpy.data.images)-ib:
 if im.users==0:bpy.data.images.remove(im)
for name,ptr in other.items():assert bpy.data.objects[name].data.as_pointer()==ptr,name
bpy.ops.wm.save_as_mainfile(filepath=str(canon));p=w/'canonical-registration.json';d=json.loads(p.read_text());d.update({'gateRoofTriangles':160,'otherObjectMeshDataUnmodifiedDuringGateOptimization':len(other),'bytes':canon.stat().st_size,'sha256':hashlib.sha256(canon.read_bytes()).hexdigest()});p.write_text(json.dumps(d,indent=2));print('V15_CANONICAL_GATE_OPTIMIZATION_SAVED',len(other),flush=True)
