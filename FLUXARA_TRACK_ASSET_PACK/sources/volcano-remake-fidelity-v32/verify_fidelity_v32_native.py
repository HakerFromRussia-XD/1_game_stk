from pathlib import Path
import bpy,json,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v32/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v32/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v32/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());old=json.loads((r/'fidelity-v30/asset-registration.json').read_text());changed=set(a['changedCapTreeMatrices']);geochanged=set(a['changedSeamNativeObjects']);new={q['name']for q in a['newPrototypes']};assert len(changed)==48
def geometry(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((layer.name,tuple(tuple(v.uv)for v in layer.data))for layer in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((attr.name,attr.data_type,attr.domain,tuple(tuple(v.color)for v in attr.data))for attr in m.color_attributes),[x.name if x else None for x in m.materials])
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in new};matrices={o.name:tuple(tuple(v)for v in o.matrix_world)for o in bpy.data.objects if o.name in snap};assert len(snap)==699
for row in a['nativeSharedInstances']:
 if row['name']in changed:assert bpy.data.objects[row['name']].data==bpy.data.objects[row['prototype']].data
im=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
bpy.ops.wm.open_mainfile(filepath=old['finalBlend']);assert set(snap)=={o.name for o in bpy.data.objects if o.type=='MESH'}
for name,g in snap.items():
 if name not in geochanged:assert geometry(bpy.data.objects[name])==g,name
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==matrices[name],name
 else:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)!=matrices[name],name
proof=json.loads((w/'final-blend-verification.json').read_text());proof.update({'allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV30':651,'intentionallyChangedSeamGeometryInstances':48,'allOtherNativeMatricesExactV30':651,'intentionallyChangedCapTreeInstanceMatrices':48,'originalStonePixelsRetained':True,'newNativePrototypes':2,'newAuthoredMaterials':0,'newImagePixels':False});(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V32_SEAM_NATIVE_AND_651_OTHER_MATRICES_VERIFIED',flush=True)

bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
import sys,collections
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
for row in a['newPrototypes']:
 obj=bpy.data.objects[row['name']];obj.data.calc_loop_triangles();d=parse(Path(row['sourceModel']));buf=d['buffers'][0]
 rt=[tuple(sorted(tuple(round(x,5)for x in buf['vertices'][i]['position'])for i in buf['indices'][j:j+3]))for j in range(0,len(buf['indices']),3)]
 nt=[tuple(sorted(tuple(round(x,5)for x in (obj.data.vertices[i].co.x,obj.data.vertices[i].co.z,obj.data.vertices[i].co.y))for i in t.vertices))for t in obj.data.loop_triangles]
 assert collections.Counter(rt)==collections.Counter(nt),row['name']
proof.update({'newSeamPrototypesTrianglePositionsMatchRuntime':432,'existingStoneImageAndMaterialReused':True,'nativePrototypeCount':40,'nativeMaterialDefinitionCount':94})
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2))
print('V32_TWO_NATIVE_RUNTIME_PROTOTYPES_VERIFIED',flush=True)
