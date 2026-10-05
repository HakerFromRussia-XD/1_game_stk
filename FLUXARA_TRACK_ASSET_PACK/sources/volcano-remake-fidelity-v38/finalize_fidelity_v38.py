from pathlib import Path
import bpy,copy,hashlib,json,math,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v38';native=w/'native';native.mkdir(exist_ok=True);assert(w/'preservation-verification.json').is_file();a=json.loads((r/'fidelity-v37/asset-registration.json').read_text());pre=json.loads((w/'shape-sky-preflight.json').read_text());bg=json.loads((w/'background-grounding.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')]);scene=E.parse(w/'candidate/scene.xml').getroot();proto_col=bpy.data.collections['Volcano Remake Asset Prototypes'];col=bpy.data.collections['Volcano Remake Shared Instances'];newrows=[]
def matrix(attrs):
 p=list(map(float,attrs['xyz'].split()));s=list(map(float,attrs['scale'].split()));h=list(map(float,attrs['hpr'].split()));assert h[0]==h[2]==0;return Matrix.Translation(Vector((p[0],p[2],p[1])))@Matrix.Rotation(math.radians(-h[1]),4,'Z')@Matrix.Diagonal((s[0],s[2],s[1],1))
def geo(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(m.name if m else None for m in m.materials))
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};matrices={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap}
def proto(role,mat):
 path=pre['new'+role+'Model']['path'];d=parse(path);name='VRV38_Prototype_'+role;mesh=native_mesh(name+'Mesh',d['buffers'][0],[bpy.data.materials[mat]]);obj=bpy.data.objects.new(name,mesh);proto_col.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']='volcano-fidelity-v38-'+role.lower();obj['source_model']=path;row={'id':obj['asset_id'],'name':name,'sourceModel':path,'sourceBuffer':0,'triangles':len(d['buffers'][0]['indices'])//3,'materials':[mat],'sourcePoolObjectId':{'Grass':'volcano-fidelity-v32-sealed-grasscap','Terrain':'volcano-fidelity-v23-rounded-backdrop-terrain','Cloud':'volcano-fidelity-v24-cloud-ashcloud'}[role]};newrows.append(row);return obj
protos={role:proto(role,mat)for role,mat in [('Grass','VRV16_GrassLipVertexColor'),('Terrain','VRV4E_vr_moss_palette.jpg'),('Cloud','VRV16_GrassLipVertexColor')]};changes={q['after']['id']:q['after']for q in pre['grassPlacements']}
for q in pre['grassPlacements']:changes.update({x['after']['id']:x['after']for x in q['linkedPlants']})
changes.update({q['after']['id']:q['after']for q in bg['placements']});changes[pre['newTerrainPlacement']['id']]=pre['newTerrainPlacement'];changed=[];changedgeo=[]
for ident,attrs in changes.items():
 rows=[q for q in a['nativeSharedInstances']if q.get('sourcePlacementId')==ident];assert len(rows)==1,ident;row=rows[0];obj=bpy.data.objects[row['name']];obj.matrix_world=matrix(attrs);row['matrix']=[list(v)for v in obj.matrix_world];row['library']=attrs['name'];obj['source_xml']=E.tostring(scene.find('library[@id="'+ident+'"]'),encoding='unicode');obj['shared_runtime_library']=attrs['name'];changed.append(obj.name)
 role='Grass'if attrs['name']=='fluxara_driftlib_volcano_grass_roll_v38'else'Terrain'if attrs['name']=='fluxara_driftlib_volcano_rolling_terrain_v38'else None
 if role:
  proto=protos[role];obj.data=proto.data;obj['source_prototype']=proto.name;obj['source_model']=proto['source_model'];obj['asset_id']=proto['asset_id'];row['prototype']=proto.name;changedgeo.append(obj.name)
added=[]
for q in pre['cloudNewPlacements']:
 attrs=q['attrs'];proto=protos['Cloud'];obj=bpy.data.objects.new(attrs['id'],proto.data);col.objects.link(obj);obj.matrix_world=matrix(attrs);obj['source_prototype']=proto.name;obj['source_model']=proto['source_model'];obj['asset_id']=proto['asset_id'];obj['shared_runtime_library']=attrs['name'];obj['source_xml']=E.tostring(scene.find('library[@id="'+attrs['id']+'"]'),encoding='unicode');a['nativeSharedInstances'].append({'name':obj.name,'prototype':proto.name,'library':attrs['name'],'matrix':[list(v)for v in obj.matrix_world],'sourcePlacementId':attrs['id']});added.append(obj.name)
for n in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:bpy.data.texts[n].clear();bpy.data.texts[n].write((w/'candidate'/n).read_text())
for lib in (w/'shared-runtime').iterdir():
 a['runtimeLibrarySources'][lib.name]=str(lib)
 for n in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+n).write((lib/n).read_text())
for name,g in snap.items():
 if name not in changedgeo:assert geo(bpy.data.objects[name])==g,name
for name,m in matrices.items():
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
im=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
a['objects']+=newrows;a['newPrototypes']=newrows;a['newMaterialVariants']=[];a['changedNativeMatrices']=changed;a['changedNativeGeometry']=changedgeo;a['newCloudNativeInstances']=added;a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V38 isolated draft. Original stone pixels preserved. Three copied source variants create grass side skirts, roll only far terrain, and tint eight rounded sky clouds. Protected road/collision data retained; reference acceptance and production integration pending.';a['visualLibrary']=str(native/'Volcano Remake Shape Sky Variants.blend');bpy.data.libraries.write(a['visualLibrary'],{protos[role]for role in protos},fake_user=True,compress=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snap.items():
 if name not in changedgeo:assert geo(bpy.data.objects[name])==g,name
for name,m in matrices.items():
 if name not in changed:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
maxerr=0
for row in a['nativeSharedInstances']:
 obj=bpy.data.objects[row['name']];assert obj.data==bpy.data.objects[row['prototype']].data,row['name'];maxerr=max(maxerr,max(abs(obj.matrix_world[i][j]-row['matrix'][i][j])for i in range(4)for j in range(4)))
assert maxerr<1e-5
proof={'finalBlendOpens':True,'allPreviousNativeObjectsRetained':len(snap),'allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV37':len(set(snap)-set(changedgeo)),'allOtherNativeMatricesExactV37':len(set(snap)-set(changed)),'changedExistingSharedMatrices':len(changed),'changedSharedMeshUsers':len(changedgeo),'newCloudSharedInstances':len(added),'newSourcePrototypes':newrows,'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'sharedMeshPointersExactAfterReopen':True,'maxTransformError':maxerr,'stonePackedPixelsExact':True,'canonicalPending':True,'newMaterialsAndTextures':0,'runtimeAndReferenceAcceptanceSeparate':True};(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V38_NATIVE_REOPEN_AND_SHARED_GEOMETRY_VERIFIED',proof,flush=True)
