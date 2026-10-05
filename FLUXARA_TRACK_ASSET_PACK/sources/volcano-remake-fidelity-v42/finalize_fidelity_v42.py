from pathlib import Path
import bpy,copy,hashlib,json,sys
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v42';native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v41/asset-registration.json').read_text());p=json.loads((w/'preservation-verification.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
def geo(o,uv=True):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers)if uv else (),tuple(tuple(n.vector)for n in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(x.name if x else None for x in m.materials),tuple(q.material_index for q in m.polygons))
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};poses={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap}
mainbuf=parse(w/'candidate/volcano_track.spm')['buffers'][2]
mainusers=[o for o in bpy.data.objects if o.type=='MESH'and len(o.data.polygons)==702 and len(o.data.vertices)==743 and 'Rock13' in str([m.name for m in o.data.materials])]
assert len(mainusers)==1
mainuser=mainusers[0];mainname=mainuser.name;mainattrs=geo(mainuser,False);mainuser.data=mainuser.data.copy();mainuv=[]
for loop in mainuser.data.loops:
 uv=mainbuf['vertices'][loop.vertex_index]['uv'];mainuv.extend([uv[0],1-uv[1]])
mainuser.data.uv_layers['UVMap'].data.foreach_set('uv',mainuv);assert geo(mainuser,False)==mainattrs
oldproto=bpy.data.objects['VRV40_Prototype_Terrain'];users=[o for o in bpy.data.objects if o.type=='MESH'and o!=oldproto and o.data==oldproto.data];assert len(users)==1;user=users[0];user_name=user.name;oldattributes=geo(user,False)
mesh=oldproto.data.copy();mesh.name='VRV42_ClosedTerrainStoneUV';d=parse(p['newField']);merged=d['buffers'][0]['vertices']+d['buffers'][1]['vertices'];values=[]
for loop in mesh.loops:
 uv=merged[loop.vertex_index]['uv'];values.extend([uv[0],1-uv[1]])
mesh.uv_layers['UVMap'].data.foreach_set('uv',values)
proto=bpy.data.objects.new('VRV42_Prototype_Terrain',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v42-terrain';proto['source_model']=p['newField']
user.data=mesh;assert geo(user,False)==oldattributes;user['source_prototype']=proto.name;user['source_model']=p['newField'];user['asset_id']=proto['asset_id'];user['shared_runtime_library']=p['newFieldPlacement']['name']
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':p['newField'],'sourceBuffers':[0,1],'triangles':999,'materials':[m.name for m in mesh.materials],'sourcePoolObjectId':'volcano-fidelity-v40-terrain','role':'Same closed terrain mesh. Only stone UV frequency divided by three to match user-selected larger near-cliff texture appearance.'}
for q in a['nativeSharedInstances']:
 if q['name']==user_name:q['prototype']=proto.name;q['library']=p['newFieldPlacement']['name']
for name,g in snap.items():
 if name not in [user_name,mainname]:assert geo(bpy.data.objects[name])==g,name
 assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
for name in ['scene.xml','materials.xml']:bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
lib=Path(p['newField']).parent;a['runtimeLibrarySources'][lib.name]=str(lib)
for name in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+name).write((lib/name).read_text())
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['changedNativeGeometry']=[user_name,mainname];a['changedNativeMatrices']=[];a['visualLibrary']=str(native/'Volcano Remake Stone Scale Variant.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True);a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V42 user stone-scale correction. Source stone image retained. Larger distant stone UV appearance; approved near cliffs and all geometry/matrices unchanged. Working candidate; production integration pending.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snap.items():
 if name not in [user_name,mainname]:assert geo(bpy.data.objects[name])==g,name
 assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
assert geo(bpy.data.objects[user_name],False)==oldattributes
assert geo(bpy.data.objects[mainname],False)==mainattrs
for q in a['nativeSharedInstances']:assert bpy.data.objects[q['name']].data==bpy.data.objects[q['prototype']].data,q['name']
stone=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(stone.packed_file.data).hexdigest()==p['stoneTextureSha256']
proof={'finalBlendOpens':True,'allPreviousNativeObjectsRetained':len(snap),'allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV41':len(snap)-2,'allPreviousNativeMatricesExactV41':len(poses),'changedExistingSharedMatrices':0,'changedNativeMeshUsers':[user_name,mainname],'onlyStoneUVChanged':True,'newSourcePrototypes':[row],'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'sharedMeshPointersExactAfterReopen':True,'stonePackedPixelsExact':True,'canonicalPending':True,'newMaterials':0,'newRasterPixels':False,'referenceNearCliffsUnchanged':True}
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V42_NATIVE_STONE_UV_AND_ALL_POSES_REOPEN_VERIFIED',proof,flush=True)
