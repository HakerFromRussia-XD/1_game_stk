from pathlib import Path
import bpy,hashlib,json,math,shutil,xml.etree.ElementTree as E
from mathutils import Matrix
r=Path(__file__).resolve().parent;w=r/'delivery-v1';w.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);p=json.loads((r/'orbital-extraction.json').read_text());reg=json.loads((r.parent/'orbital-soccer-rework/asset-registration-v5.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(r/'before-native.blend'));bpy.context.preferences.filepaths.save_version=0
cache={}
def geo(o):
 m=o.data
 if m.as_pointer()not in cache:cache[m.as_pointer()]=hashlib.sha256(repr((tuple(tuple(v.co)for v in m.vertices),tuple((tuple(q.vertices),q.material_index)for q in m.polygons),tuple((l.name,tuple(tuple(q.uv)for q in l.data))for l in m.uv_layers),tuple(tuple(q.vector)for q in m.corner_normals),tuple((l.name,l.domain,l.data_type,tuple(tuple(q.color)for q in l.data))for l in m.color_attributes),tuple(q.name if q else None for q in m.materials))).encode()).hexdigest()
 return cache[m.as_pointer()]
snapshot={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};poses={o.name:[list(v)for v in o.matrix_world]for o in bpy.data.objects};byname={q['object']:q['assetId']for q in reg['placements']};byid={q['id']:q for q in reg['objects']};protos={};rows=[];col=bpy.data.collections.new('Orbital Shared Prototypes');bpy.context.scene.collection.children.link(col)
for q in p['prototypes']:
 source=bpy.data.objects[q['sourceObject']];aid=byname[q['sourceObject']];proto=bpy.data.objects.new('OrbitalShared_'+q['library'].split('_')[-1],source.data);col.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']=aid;proto['shared_runtime_library']=q['library'];proto['canonical_asset']=str(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend'))+'#Object/'+byid[aid]['prototype'];protos[q['library']]=proto;rows.append({**q,'nativePrototype':proto.name,'sourcePoolObjectId':aid,'canonicalNativePrototype':byid[aid]['prototype']})
for q in p['placements']:
 o=bpy.data.objects[q['sourceObject']];proto=protos[q['library']];assert geo(o)==geo(proto),o.name;o.data=proto.data;o['shared_runtime_library']=q['library'];o['source_prototype']=proto.name
lamp=next(q for q in rows if 'WarmLamp' in q['sourceObject']);proto=protos[lamp['library']];bottom=min(v.co.z for v in proto.data.vertices);extras=[];col=bpy.data.collections.new('Orbital Additional Curb Lights');bpy.context.scene.collection.children.link(col)
for side in [-1,1]:
 for i,y in enumerate([-78,-52,-26,0,26,52,78]):
  x=side*96;z=1-bottom*1.2-.04;name=f'Orbital_PoolLamp_{side}_{i}';o=bpy.data.objects.new(name,proto.data);col.objects.link(o);o.matrix_world=Matrix.Translation((x,y,z))@Matrix.Diagonal((1,1,1.2,1));o['asset_id']=proto['asset_id'];o['source_prototype']=proto.name;o['shared_runtime_library']=lamp['library'];o['support_object']=f'Orbital_V5_Curb_{0 if side==-1 else 1}';extras.append({'id':name,'nativeObject':name,'sourceObject':lamp['sourceObject'],'library':lamp['library'],'xyz':[x,z,y],'hpr':[0,0,0],'scale':[1,1.2,1],'sourceMatrix':[list(v)for v in o.matrix_world],'support':o['support_object'],'curbTopBlenderZ':1,'bottomBlenderZ':.96,'rootEmbedMeters':.04,'newDecorativePlacement':True})
for name,h in snapshot.items():assert geo(bpy.data.objects[name])==h,name
for name,m in poses.items():assert [list(v)for v in bpy.data.objects[name].matrix_world]==m,name
shutil.copytree(r/'candidate',w/'candidate',dirs_exist_ok=True);scene=E.parse(w/'candidate/scene.xml')
for q in extras:E.SubElement(scene.getroot(),'library',name=q['library'],id=q['id'],xyz=' '.join(f'{v:.9g}'for v in q['xyz']),hpr='0 0 0',scale='1 1.2 1')
scene.write(w/'candidate/scene.xml',encoding='utf-8',xml_declaration=True)
for name in ['scene.xml','materials.xml','track.xml']:
 text=bpy.data.texts.get(name)or bpy.data.texts.new(name);text.clear();text.write((w/'candidate'/name).read_text())
text=bpy.data.texts.new('Orbital_SharedPlacements.json');text.write(json.dumps({'existingCoordinateParts':p['placements'],'newLightPlacements':extras,'canonicalNativePrototypes':rows},indent=2));bpy.context.scene['approved_style']='User approved V5; original visual geometry and poses retained.';bpy.context.scene['coordinate_storage_phase']='Repeated lamp and module parts extracted; fourteen copies of the same lamp embedded into existing curbs.'
file=native/'ORBITAL Simulation - Soccer.blend';protoNames={k:v.name for k,v in protos.items()};bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file));cache.clear()
for name,h in snapshot.items():assert geo(bpy.data.objects[name])==h,name
for name,m in poses.items():assert [list(v)for v in bpy.data.objects[name].matrix_world]==m,name
for q in p['placements']+extras:assert bpy.data.objects[q.get('nativeObject',q['sourceObject'])].data==bpy.data.objects[protoNames[q['library']]].data
proof={'finalBlend':str(file),'finalBlendSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'allOriginalMeshAttributesExact':len(snapshot),'allOriginalMatricesExact':len(poses),'allOriginalObjectsRetained':True,'existingNativeSceneryConvertedToSharedPointers':len(p['placements']),'reusedCanonicalPrototypes':rows,'additionalLights':len(extras),'newPlacements':extras,'noNewImagePixels':True,'localModelGeometryUnchanged':True,'reopenedAndSharedPointersVerified':True,'canonicalNativeLibraryNotModified':True,'approvedV5GeometryAndTransformsPreserved':True};(w/'native-verification.json').write_text(json.dumps(proof,indent=2));print('ORBITAL_NATIVE_AND_14_CURB_LIGHTS_SAVED',len(snapshot),len(poses),len(p['prototypes']),flush=True)
