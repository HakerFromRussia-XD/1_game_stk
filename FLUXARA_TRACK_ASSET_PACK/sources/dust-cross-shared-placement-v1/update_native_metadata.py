from pathlib import Path
import bpy,hashlib,json
r=Path(__file__).resolve().parent;w=r/'delivery-v1';p=w/'native-verification.json';n=json.loads(p.read_text());file=Path(n['finalBlend']);bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.preferences.filepaths.save_version=0
def geometry_hash(o):
 m=o.data;return hashlib.sha256(repr((tuple(tuple(v.co)for v in m.vertices),tuple((tuple(q.vertices),q.material_index)for q in m.polygons),tuple((u.name,tuple(tuple(v.uv)for v in u.data))for u in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((c.name,c.domain,c.data_type,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes),tuple(x.name if x else None for x in m.materials))).encode()).hexdigest()
cache={}
def h(o):
 if o.data.as_pointer()not in cache:cache[o.data.as_pointer()]=geometry_hash(o)
 return cache[o.data.as_pointer()]
snapshot={o.name:h(o)for o in bpy.data.objects if o.type=='MESH'};matrices={o.name:tuple(tuple(v)for v in o.matrix_world)for o in bpy.data.objects}
for name in ['track.xml','scene.xml','materials.xml']:
 text=bpy.data.texts.get(name)or bpy.data.texts.new(name);text.clear();text.write((w/'candidate'/name).read_text())
text=bpy.data.texts.get('DustCross_SharedPlacements.json')or bpy.data.texts.new('DustCross_SharedPlacements.json');text.clear();text.write(json.dumps({'existingCoordinates':572,'newTreeCoordinates':n['newPlacements'],'newTreeGrounding':n['grounding'],'canonicalPrototypes':n['reusedCanonicalPrototypes']},indent=2))
bpy.context.scene['shared_placement_phase']='572 existing object coordinates plus 108 new parts forming18 grounded trees. Canonical native assets directly reused.'
for q in n['reusedCanonicalPrototypes']:bpy.data.objects[q['nativePrototype']]['canonical_asset']=str(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend'))+'#Object/'+q['canonicalNativePrototype']
bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file));cache.clear()
for name,g in snapshot.items():assert h(bpy.data.objects[name])==g,name
for name,m in matrices.items():assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
for name in ['track.xml','scene.xml','materials.xml']:assert bpy.data.texts[name].as_string()==(w/'candidate'/name).read_text()
n['sourceSceneAndPreviewMetadataEmbedded']=True;n['allMeshAttributesAndMatricesRetainedAfterMetadataUpdate']=True;n['finalBlendSha256']=hashlib.sha256(file.read_bytes()).hexdigest();p.write_text(json.dumps(n,indent=2));print('DUST_FINAL_NATIVE_METADATA_AND_GEOMETRY_REOPEN_VERIFIED',len(snapshot),len(matrices),flush=True)
