from pathlib import Path
import bpy,copy,hashlib,json,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v42/asset-registration.json').read_text());p=json.loads((w/'preservation-verification.json').read_text());old=json.loads((r/'fidelity-v14/asset-registration.json').read_text())
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
def geo(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(p.vertices)for p in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers),tuple(tuple(n.vector)for n in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(x.name if x else None for x in m.materials),tuple(q.material_index for q in m.polygons))
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};poses={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snap}
removeids={x['id']for x in p['removedDecorativePlacements']};removed=[q for q in a['nativeSharedInstances']if q.get('sourcePlacementId')in removeids];assert len(removed)==len(removeids)
for q in removed:bpy.data.objects.remove(bpy.data.objects[q['name']],do_unlink=True)
a['nativeSharedInstances']=[q for q in a['nativeSharedInstances']if q not in removed]
resetids={x['after']['id']for x in p['resetBushPlacements']};oldrows={q['name']:q for q in old['nativeSharedInstances']};reset=[]
scene=E.parse(w/'candidate/scene.xml').getroot()
for q in a['nativeSharedInstances']:
 if q.get('sourcePlacementId')in resetids:
  o=bpy.data.objects[q['name']];o.matrix_world=Matrix(oldrows[q['name']]['matrix']);q['matrix']=[list(v)for v in o.matrix_world];o['source_xml']=E.tostring(scene.find('library[@id="'+q['sourcePlacementId']+'"]'),encoding='unicode');reset.append(o.name)
assert len(reset)==104
d=parse(p['newField']);merged={'vertices':[],'indices':[],'material':0};counts=[]
for b in d['buffers']:
 offset=len(merged['vertices']);merged['vertices']+=copy.deepcopy(b['vertices']);merged['indices']+=[offset+i for i in b['indices']];counts.append(len(b['indices'])//3)
mesh=native_mesh('VRV43_OriginalContinuousTerrainMesh',merged,[bpy.data.materials['VRV4E_Rock13_col.jpg'],bpy.data.materials['VRV4E_vr_moss_palette.jpg']])
for poly in mesh.polygons:poly.material_index=int(counts[0]<=poly.index<sum(counts[:2]))
proto=bpy.data.objects.new('VRV43_Prototype_ContinuousTerrain',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v43-continuous-terrain';proto['source_model']=p['newField']
user_name='VR_OriginalSurface_012';user=bpy.data.objects[user_name];user.data=mesh;user['source_prototype']=proto.name;user['source_model']=p['newField'];user['asset_id']=proto['asset_id'];user['shared_runtime_library']=p['newFieldPlacement']['name']
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':p['newField'],'sourceBuffers':[0,1,2],'triangles':sum(counts),'materials':[m.name for m in mesh.materials],'sourcePoolObjectId':'volcano-fidelity-v14-central-rock','role':'Original V14 continuous cliff and grass surfaces restored as one shared ghost mesh; existing V42 main-cliff triangles excluded. Original local coordinates, dimensions, normals and material boundaries retained.'}
for q in a['nativeSharedInstances']:
 if q['name']==user_name:q.update({'prototype':proto.name,'library':p['newFieldPlacement']['name']})
for name,g in snap.items():
 if name in [q['name']for q in removed]:continue
 if name!=user_name:assert geo(bpy.data.objects[name])==g,name
 if name not in reset:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
for name in ['scene.xml','materials.xml']:bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
lib=Path(p['newField']).parent;a['runtimeLibrarySources'][lib.name]=str(lib)
for name in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+name).write((lib/name).read_text())
a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['changedNativeGeometry']=[user_name];a['changedNativeMatrices']=reset;a['removedDecorativeNativeInstances']=[q['name']for q in removed];a['visualLibrary']=str(native/'Volcano Remake Continuous Terrain Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True);a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V43 continuous V14 landscape restoration. Protected course and all original physical geometry unchanged. Scattered floating landscape copies removed; source bush placements restored. Candidate runtime/reference review pending.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snap.items():
 if name in a['removedDecorativeNativeInstances']:assert name not in bpy.data.objects;continue
 if name!=user_name:assert geo(bpy.data.objects[name])==g,name
 if name not in reset:assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
for q in a['nativeSharedInstances']:assert bpy.data.objects[q['name']].data==bpy.data.objects[q['prototype']].data,q['name']
stone=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(stone.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
proof={'finalBlendOpens':True,'removedDecorativeInstances':len(removed),'allRetainedNativeGeometryExactV42ExceptRestoredTerrain':len(snap)-len(removed)-1,'allOtherNativeMatricesExactV42':len(snap)-len(removed)-len(reset),'restoredBushMatricesExactV14':len(reset),'newSourcePrototypes':[row],'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'sharedMeshPointersExactAfterReopen':True,'stonePackedPixelsExact':True,'canonicalPending':True,'newMaterials':0,'newRasterPixels':False,'triangleMaterialCounts':counts}
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V43_NATIVE_CONTIGUOUS_LANDSCAPE_REOPEN_VERIFIED',proof,flush=True)
