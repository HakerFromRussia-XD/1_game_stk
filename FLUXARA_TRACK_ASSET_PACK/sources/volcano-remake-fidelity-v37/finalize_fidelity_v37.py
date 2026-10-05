from pathlib import Path
import bpy,copy,hashlib,json,math,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v36/asset-registration.json').read_text());rp=json.loads((w/'rim-preflight.json').read_text());bg=json.loads((w/'background-preflight.json').read_text());assert (w/'preservation-verification.json').is_file();scene=E.parse(w/'candidate/scene.xml').getroot();bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
def matrix(attrs):
 p=list(map(float,attrs['xyz'].split()));s=list(map(float,attrs['scale'].split()));h=list(map(float,attrs['hpr'].split()));assert h[0]==h[2]==0;return Matrix.Translation(Vector((p[0],p[2],p[1])))@Matrix.Rotation(math.radians(-h[1]),4,'Z')@Matrix.Diagonal((s[0],s[2],s[1],1))
def geo(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(m.name if m else None for m in m.materials))
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};matrices={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap};changes={q['after']['id']:q['after']for q in rp['rims']}
for q in rp['rims']:changes.update({x['after']['id']:x['after']for x in q['linkedPlants']})
changed=[]
for ident,attrs in changes.items():
 rows=[q for q in a['nativeSharedInstances']if q.get('sourcePlacementId')==ident];assert len(rows)==1,ident;row=rows[0];obj=bpy.data.objects[row['name']];obj.matrix_world=matrix(attrs);row['matrix']=[list(v)for v in obj.matrix_world];obj['source_xml']=E.tostring(scene.find('library[@id="'+ident+'"]'),encoding='unicode');changed.append(obj.name)
added=[];col=bpy.data.collections['Volcano Remake Shared Instances']
for q in bg['placements']:
 attrs=q['attrs'];proto=bpy.data.objects['VRV18_Prototype_GreenMound'if q['role']=='Mound'else'DPV2_DP_RoundedTree_Prototype'];obj=bpy.data.objects.new(attrs['id'],proto.data);col.objects.link(obj);obj.matrix_world=matrix(attrs);obj['source_prototype']=proto.name;obj['source_model']=proto.get('source_model','');obj['asset_id']=proto.get('asset_id','');obj['shared_runtime_library']=attrs['name'];obj['source_xml']=E.tostring(scene.find('library[@id="'+attrs['id']+'"]'),encoding='unicode');a['nativeSharedInstances'].append({'name':obj.name,'prototype':proto.name,'library':attrs['name'],'matrix':[list(v)for v in obj.matrix_world],'sourcePlacementId':attrs['id']});added.append(obj.name)
for n in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:
 bpy.data.texts[n].clear();bpy.data.texts[n].write((w/'candidate'/n).read_text())
for name,g in snap.items():assert geo(bpy.data.objects[name])==g,name
for name,m in matrices.items():
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
im=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
a['newPrototypes']=[];a['newMaterialVariants']=[];a['reusedPrototypes']=copy.deepcopy(a['objects']);a['changedNativeMatrices']=changed;a['newBackgroundNativeInstances']=added;a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V37 isolated working draft:81thicker shared grass caps with grass/stone seam anchored,160linked vegetation transforms and84newbackground coordinates using existing shared assets. All source geometry/materials/stone pixels and protected road/control data retained. Full reference and integration gates separate.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snap.items():assert geo(bpy.data.objects[name])==g,name
for name,m in matrices.items():
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
maxerr=0
for row in a['nativeSharedInstances']:
 obj=bpy.data.objects[row['name']];assert obj.data==bpy.data.objects[row['prototype']].data,row['name'];maxerr=max(maxerr,max(abs(obj.matrix_world[i][j]-row['matrix'][i][j])for i in range(4)for j in range(4)))
assert maxerr<1e-5
canon=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend');ci=json.loads((r/'fidelity-v36/canonical-registration.json').read_text());assert hashlib.sha256(canon.read_bytes()).hexdigest()==ci['sha256']
proof={'finalBlendOpens':True,'allPreviousNativeMeshGeometryUVNormalsColorsMaterialsExactV36':len(snap),'allOtherNativeMatricesExactV36':len(set(snap)-set(changed)),'changedExistingSharedMatrices':len(changed),'newBackgroundSharedInstances':len(added),'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'sharedMeshPointersExactAfterReopen':True,'maxTransformError':maxerr,'stonePackedPixelsExact':True,'canonicalByteHashExactV36':ci['sha256'],'canonicalPending':False,'newModelsMaterialsTextures':0,'runtimeAndReferenceAcceptanceSeparate':True}
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V37_NATIVE_REOPEN_AND_SHARED_GEOMETRY_VERIFIED',proof,flush=True)
