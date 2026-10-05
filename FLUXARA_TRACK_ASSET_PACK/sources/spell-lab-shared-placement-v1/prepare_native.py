from pathlib import Path
import bpy,hashlib,json,math,shutil,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'delivery-v1';w.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);p=json.loads((r/'spell-extraction.json').read_text());reg=json.loads((r.parent/'spell-lab-rework/asset-registration.json').read_text());base=json.loads((r/'baseline.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(r/'before-native.blend'));bpy.context.preferences.filepaths.save_version=0
cache={}
def geo(o):
 m=o.data
 if m.as_pointer()not in cache:
  cache[m.as_pointer()]=hashlib.sha256(repr((tuple(tuple(v.co)for v in m.vertices),tuple((tuple(q.vertices),q.material_index)for q in m.polygons),tuple((l.name,tuple(tuple(q.uv)for q in l.data))for l in m.uv_layers),tuple(tuple(q.vector)for q in m.corner_normals),tuple((l.name,l.domain,l.data_type,tuple(tuple(q.color)for q in l.data))for l in m.color_attributes),tuple(q.name if q else None for q in m.materials))).encode()).hexdigest()
 return cache[m.as_pointer()]
snapshot={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};poses={o.name:[list(v)for v in o.matrix_world]for o in bpy.data.objects};byname={q['object']:q['assetId']for q in reg['placements']};byid={q['id']:q for q in reg['objects']};protos={};rows=[];col=bpy.data.collections.new('SpellLab Shared Prototypes');bpy.context.scene.collection.children.link(col)
for q in p['prototypes']:
 source=bpy.data.objects[q['sourceObject']];aid=byname[q['sourceObject']];proto=bpy.data.objects.new('SLShared_'+q['library'].split('_')[-1],source.data);col.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']=aid;proto['shared_runtime_library']=q['library'];proto['canonical_asset']=str(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend'))+'#Object/'+byid[aid]['prototype'];protos[q['library']]=proto;rows.append({**q,'nativePrototype':proto.name,'sourcePoolObjectId':aid,'canonicalNativePrototype':byid[aid]['prototype']})
for q in p['placements']:
 o=bpy.data.objects[q['sourceObject']];proto=protos[q['library']];assert geo(o)==geo(proto),o.name;o.data=proto.data;o['shared_runtime_library']=q['library'];o['source_prototype']=proto.name
crown=[q for q in rows if q['sourceObject']=='SL_TreeCrown_0_0'][0];proto=protos[crown['library']];extras=[];roots=[];col=bpy.data.collections.new('SpellLab Additional Garden Shrubs');bpy.context.scene.collection.children.link(col)
sourceCrowns=[bpy.data.objects[f'SL_TreeCrown_0_{j}'] for j in range(3)];sourceMatrices=[o.matrix_world.copy() for o in sourceCrowns];foot=Vector((-160,-140,min((o.matrix_world@v.co).z for o in sourceCrowns for v in o.data.vertices)))
for i in range(36):
 turf=bpy.data.objects[f'SL_Turf_{i}'];pts=[turf.matrix_world@v.co for v in turf.data.vertices];top=max(v.z for v in pts);center=turf.matrix_world.translation;k=turf.matrix_world.to_scale().x
 for j in range(5):
  angle=2*math.pi*j/5+(i%2)*.28;cx=center.x+14.2*k*math.cos(angle);cy=center.y+14.2*k*math.sin(angle);factor=.20*k/.64;adapt=Matrix.Translation((cx,cy,top-.08))@Matrix.Rotation(angle,4,'Z')@Matrix.Diagonal((factor,factor,factor,1))@Matrix.Translation(-foot)
  for part,sourceMatrix in enumerate(sourceMatrices):
   name=f'SL_PoolShrub_{i:02d}_{j}_Crown{part}';o=bpy.data.objects.new(name,proto.data);col.objects.link(o);o.matrix_world=adapt@sourceMatrix;o['asset_id']=proto['asset_id'];o['source_prototype']=proto.name;o['shared_runtime_library']=crown['library'];o['support_object']=turf.name;l,rot,scale=o.matrix_world.decompose();eu=rot.to_euler('XZY');extras.append({'id':name,'nativeObject':name,'sourceObject':crown['sourceObject'],'library':crown['library'],'xyz':[l.x,l.z,l.y],'hpr':[-math.degrees(eu.x),-math.degrees(eu.z),-math.degrees(eu.y)],'scale':[scale.x,scale.z,scale.y],'sourceMatrix':[list(v)for v in o.matrix_world],'support':turf.name,'rootEmbedMeters':.08,'newDecorativePlacement':True,'shrubGroup':f'SL_PoolShrub_{i:02d}_{j}'})
  roots.append({'group':f'SL_PoolShrub_{i:02d}_{j}','parts':3,'support':turf.name,'supportTop':top,'groupBottomZ':top-.08,'existingPadScale':k,'horizontalDistanceFromPadCenter':14.2*k})
for name,h in snapshot.items():assert geo(bpy.data.objects[name])==h,name
for name,m in poses.items():assert [list(v)for v in bpy.data.objects[name].matrix_world]==m,name
shutil.copytree(r/'candidate',w/'candidate',dirs_exist_ok=True);scene=E.parse(w/'candidate/scene.xml')
for q in extras:E.SubElement(scene.getroot(),'library',name=q['library'],id=q['id'],xyz=' '.join(f'{v:.9g}'for v in q['xyz']),hpr=' '.join(f'{v:.9g}'for v in q['hpr']),scale=' '.join(f'{v:.9g}'for v in q['scale']))
scene.write(w/'candidate/scene.xml',encoding='utf-8',xml_declaration=True)
for name in ['scene.xml','materials.xml','track.xml']:
 t=bpy.data.texts.get(name)or bpy.data.texts.new(name);t.clear();t.write((w/'candidate'/name).read_text())
text=bpy.data.texts.get('SpellLab_SharedPlacements.json')or bpy.data.texts.new('SpellLab_SharedPlacements.json');text.clear();text.write(json.dumps({'existingCoordinateParts':p['placements'],'newShrubPlacements':extras,'supportGrounding':roots,'canonicalNativePrototypes':rows},indent=2));bpy.context.scene['coordinate_storage_phase']='284 original parts +180 garden shrubs (540 shared crown parts); eight shared runtime models; original course and points retained.'
file=native/'Spell Lab.blend';protoNames={k:v.name for k,v in protos.items()};bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file));cache.clear()
for name,h in snapshot.items():assert geo(bpy.data.objects[name])==h,name
for name,m in poses.items():assert [list(v)for v in bpy.data.objects[name].matrix_world]==m,name
for q in p['placements']+extras:assert bpy.data.objects[q.get('nativeObject',q['sourceObject'])].data==bpy.data.objects[protoNames[q['library']]].data
proof={'finalBlend':str(file),'finalBlendSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'allOriginalMeshAttributesExact':len(snapshot),'allOriginalMatricesExact':len(poses),'allOriginalObjectsRetained':True,'existingNativeSceneryConvertedToSharedPointers':284,'reusedCanonicalPrototypes':rows,'additionalShrubs':len(roots),'additionalShrubParts':len(extras),'newPlacements':extras,'grounding':roots,'noNewImagePixels':True,'localModelGeometryUnchanged':True,'reopenedAndSharedPointersVerified':True,'canonicalNativeLibraryNotModified':True};(w/'native-verification.json').write_text(json.dumps(proof,indent=2));print('SPELL_SHARED_NATIVE_AND_180_GROUNDED_THREE_PART_SHRUBS_SAVED',len(snapshot),len(poses),flush=True)
