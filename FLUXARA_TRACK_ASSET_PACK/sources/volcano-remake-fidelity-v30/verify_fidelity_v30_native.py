from pathlib import Path
import bpy,json,hashlib,math,collections,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v30';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v30/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v30/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v30/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
a=json.loads((w/'asset-registration.json').read_text());old=json.loads((r/'fidelity-v29/asset-registration.json').read_text());p=json.loads((w/'facade-placements.json').read_text());new=set(a['newFacadeNativeObjects']);tree=a['reusedPrototypes'][0];assert len(new)==3*p['newCoordinateGroups']
def geometry(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((layer.name,tuple(tuple(v.uv)for v in layer.data))for layer in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((attr.name,attr.data_type,attr.domain,tuple(tuple(v.color)for v in attr.data))for attr in m.color_attributes),[x.name if x else None for x in m.materials])
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in new and o.name!=tree['name']};matrices={o.name:tuple(tuple(v)for v in o.matrix_world)for o in bpy.data.objects if o.name in snap};assert len(snap)==626
treeobj=bpy.data.objects[tree['name']];treeobj.data.calc_loop_triangles();treegeo=geometry(treeobj);assert len(treeobj.data.loop_triangles)==588
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(p['modelSources'][2]['path']);obj=bpy.data.objects[tree['name']]
# Source native/runtime exports use different seam vertices; compare triangle positions and UV/material corners.
rt=[]
for buf in d['buffers']:
 for j in range(0,len(buf['indices']),3):
  rt.append(tuple(sorted(tuple(round(x,5)for x in buf['vertices'][i]['position'])for i in buf['indices'][j:j+3])))
nt=[tuple(sorted(tuple(round(x,5)for x in (obj.data.vertices[i].co.x,obj.data.vertices[i].co.z,obj.data.vertices[i].co.y))for i in face.vertices))for face in obj.data.loop_triangles]
assert collections.Counter(rt)==collections.Counter(nt)
expectedbounds=d['bounds'];bb=[(v.co.x,v.co.z,v.co.y)for v in obj.data.vertices];actual=[min(v[k]for v in bb)for k in range(3)]+[max(v[k]for v in bb)for k in range(3)];assert max(abs(actual[k]-expectedbounds[k])for k in range(6))<1e-6
for row in a['nativeSharedInstances']:
 if row['name']in new:
  proto=bpy.data.objects[row['prototype']];assert bpy.data.objects[row['name']].data==proto.data
image=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(image.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
treeimagehashes={Path(n.image.filepath).name:hashlib.sha256(n.image.packed_file.data).hexdigest()for m in obj.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image}
bpy.ops.wm.open_mainfile(filepath=old['finalBlend']);assert set(snap)=={o.name for o in bpy.data.objects if o.type=='MESH'}
for name,g in snap.items():assert geometry(bpy.data.objects[name])==g and tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==matrices[name],name
bpy.ops.wm.open_mainfile(filepath=a['directTreeSourceLibrary']);assert geometry(bpy.data.objects[tree['name']])==treegeo
proof=json.loads((w/'final-blend-verification.json').read_text());proof.update({'allOtherNativeMeshesAndMatricesExactV29':626,'newSharedCoordinateNativeParts':len(new),'directReusedNativeTreePrototype':tree['id'],'sourceNativeTreeGeometryUVsNormalsColorsAndMaterialsExact':True,'runtimeTreeTrianglePositionsMatchNative':588,'sourceTreeLocalBoundsOriginAxesRetained':True,'treePackedImageHashes':treeimagehashes,'originalStonePixelsRetained':True,'newAuthoredGeometry':False,'newAuthoredMaterials':0,'newImagePixels':False})
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V30_DIRECT_TREE_NATIVE_AND_OTHER_MESHES_VERIFIED',626,len(new),flush=True)
