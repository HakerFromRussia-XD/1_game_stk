from pathlib import Path
import bpy,copy,hashlib,json,math,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v39';native=w/'native';native.mkdir(exist_ok=True);assert(w/'preservation-verification.json').is_file();a=json.loads((r/'fidelity-v38/asset-registration.json').read_text());p=json.loads((w/'visual-batch-preflight.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')]);scene=E.parse(w/'candidate/scene.xml').getroot();pc=bpy.data.collections['Volcano Remake Asset Prototypes']
def geo(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(x.name if x else None for x in m.materials),tuple(p.material_index for p in m.polygons))
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};matrixsnap={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap};oldmain=parse(r/'fidelity-v38/candidate/volcano_track.spm');main=parse(w/'candidate/volcano_track.spm');changed=[]
# A single copied material assignment changes the original low floor's appearance; geometry and custom normals stay intact.
lakeusers=[o for o in bpy.data.objects if o.type=='MESH'and len(o.data.polygons)==2 and any(m and 'acid_lake'in m.name for m in o.data.materials)];assert len(lakeusers)==1,[o.name for o in lakeusers];o=lakeusers[0];mesh=o.data.copy();assert len(mesh.vertices)==4;mesh.materials.clear();mesh.materials.append(bpy.data.materials['VRV16_GrassLipVertexColor']);co=mesh.color_attributes.get('Color');assert co
for loop in mesh.loops:co.data[loop.index].color=tuple(x/255 for x in main['buffers'][3]['vertices'][loop.vertex_index]['color'])+(1,)
o.data=mesh;changed.append(o.name)
woodusers=[o for o in bpy.data.objects if o.type=='MESH'and len(o.data.polygons)==159 and any(m and 'WoodA'in m.name for m in o.data.materials)];assert len(woodusers)==1;obj=woodusers[0];m=obj.data.copy();assert len(m.vertices)==277;oldg=geo(obj);roofids=set(p['woodRoofOriginalVertexIds']);ids=p['woodRoofOriginalVertexIds'];roofverts={i:main['buffers'][20]['vertices'][j]for j,i in enumerate(ids)};rooftri={j for q in p['roofGroups']for j in q['triangles']};m.materials.append(bpy.data.materials['VRV36_TerracottaBrickRoof']);roofmi=len(m.materials)-1;uv=m.uv_layers.active;co=m.color_attributes.get('Color')
for poly in m.polygons:
 if poly.index in rooftri:poly.material_index=roofmi
 for li in poly.loop_indices:
  i=m.loops[li].vertex_index
  if i in roofids:v=roofverts[i];uv.data[li].uv=(v['uv'][0],1-v['uv'][1]);co.data[li].color=tuple(x/255 for x in v['color'])+(1,)
obj.data=m;changed.append(obj.name);assert geo(obj)[0:2]==oldg[0:2]and geo(obj)[3]==oldg[3]
# One shared source colour variant, referenced by the same eight cloud matrices.
cl=parse(p['newCloudModel']['path']);mesh=native_mesh('VRV39_CloudMesh',cl['buffers'][0],[bpy.data.materials['VRV16_GrassLipVertexColor']]);proto=bpy.data.objects.new('VRV39_Prototype_Cloud',mesh);pc.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v39-cloud';proto['source_model']=p['newCloudModel']['path'];row={'id':proto['asset_id'],'name':proto.name,'sourceModel':proto['source_model'],'sourceBuffer':0,'triangles':960,'materials':['VRV16_GrassLipVertexColor'],'sourcePoolObjectId':'volcano-fidelity-v38-cloud'}
for q in a['nativeSharedInstances']:
 if q['library']=='fluxara_driftlib_volcano_sky_cloud_v38':
  o=bpy.data.objects[q['name']];o.data=proto.data;q['prototype']=proto.name;q['library']='fluxara_driftlib_volcano_sky_cloud_v39';o['source_prototype']=proto.name;o['source_model']=proto['source_model'];o['asset_id']=proto['asset_id'];o['shared_runtime_library']=q['library'];o['source_xml']=E.tostring(scene.find('library[@id="'+q['sourcePlacementId']+'"]'),encoding='unicode');changed.append(o.name)
for name in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
lib=w/'shared-runtime/fluxara_driftlib_volcano_sky_cloud_v39';a['runtimeLibrarySources'][lib.name]=str(lib)
for name in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+name).write((lib/name).read_text())
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['changedNativeGeometry']=changed;a['changedNativeMatrices']=[];a['visualLibrary']=str(native/'Volcano Remake Warm Cloud Variant.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True);a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V39 isolated lighting/material draft: original stonepixels retained, green lowfloor uses warm vertexcolorswithoutnewtexture, four existingcones use existing tile-roof brick pixels andUV, eightclouds lighter. Alltrue roadgeometry/UV/colors/physics andworldtransforms retained. Overallreference/integration pending.'
for name,g in snap.items():
 if name not in changed:assert geo(bpy.data.objects[name])==g,name
for name,matrix in matrixsnap.items():assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==matrix,name
im=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snap.items():
 if name not in changed:assert geo(bpy.data.objects[name])==g,name
for name,matrix in matrixsnap.items():assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==matrix,name
for q in a['nativeSharedInstances']:assert bpy.data.objects[q['name']].data==bpy.data.objects[q['prototype']].data
proof={'finalBlendOpens':True,'allPreviousNativeObjectsRetained':len(snap),'allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV38':len(set(snap)-set(changed)),'allPreviousNativeMatricesExactV38':len(snap),'changedMeshUsers':changed,'trueDrivingSurfaceAttributesExactV38':True,'fourRoofNativePositionsNormalsAndPolygonsExactV38':True,'newSourcePrototypes':[row],'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'sharedMeshPointersExactAfterReopen':True,'stonePackedPixelsExact':True,'canonicalPending':True,'newMaterialsAndTextures':0,'runtimeAndReferenceAcceptanceSeparate':True};(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V39_NATIVE_REOPEN_AND_PRESERVATION_VERIFIED',len(snap),len(changed),flush=True)
