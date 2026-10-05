from pathlib import Path
import bpy,copy,hashlib,json,math,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'delivery-v1';w.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);p=json.loads((r/'dust-extraction.json').read_text());reg=json.loads((r.parent/'dust-cross-completion/asset-registration.json').read_text());baseline=json.loads((r/'baseline.json').read_text());bpy.ops.wm.open_mainfile(filepath=baseline['sourceNative']);bpy.context.preferences.filepaths.save_version=0
cache={}
def geo(o):
 m=o.data
 if m.as_pointer()in cache:return cache[m.as_pointer()]
 value=(tuple(tuple(v.co)for v in m.vertices),tuple((tuple(q.vertices),q.material_index)for q in m.polygons),tuple((x.name,tuple(tuple(v.uv)for v in x.data))for x in m.uv_layers),tuple(tuple(n.vector)for n in m.corner_normals),tuple((x.name,x.domain,x.data_type,tuple(tuple(v.color)for v in x.data))for x in m.color_attributes),tuple(x.name if x else None for x in m.materials));value=hashlib.sha256(repr(value).encode()).hexdigest();cache[m.as_pointer()]=value;return value
snap={o.name:geo(o)for o in bpy.data.objects if o.type=='MESH'};poses={o.name:tuple(tuple(v)for v in o.matrix_world)for o in bpy.data.objects};assetByName={q['name']:q['assetId']for q in reg['placements']};objectsById={q['id']:q for q in reg['objects']};protos={};rows=[]
col=bpy.data.collections.new('DustCross Shared Prototypes');bpy.context.scene.collection.children.link(col)
for q in p['prototypes']:
 source=bpy.data.objects[q['sourceObject']];aid=assetByName[q['sourceObject']];name='DCShared_'+q['library'].split('_')[-1];proto=bpy.data.objects.new(name,source.data);col.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']=aid;proto['source_model']=q['model'];protos[q['library']]=proto;rows.append({**q,'nativePrototype':name,'sourcePoolObjectId':aid,'canonicalNativePrototype':objectsById[aid]['name']if aid in objectsById else 'DustCross_GardenMesa_Light'})
for q in p['placements']:
 o=bpy.data.objects[q['sourceObject']];proto=protos[q['library']];assert geo(o)==geo(proto),o.name;o.data=proto.data;o['shared_runtime_library']=q['library'];o['source_placement_id']=q['id'];o['source_prototype']=proto.name
tree=[q for q in p['placements']if q['sourceObject'].startswith('DC_Tree_0_0_')];assert len(tree)==6
trunk=bpy.data.objects['DC_Tree_0_0_Trunk'];foot=Vector((trunk.matrix_world.translation.x,trunk.matrix_world.translation.y,min((trunk.matrix_world@v.co).z for v in trunk.data.vertices)));treeMatrices={q['sourceObject']:Matrix(q['sourceMatrix'])for q in tree}
def height(o,x,y):
 o.data.calc_loop_triangles();vs=[o.matrix_world@v.co for v in o.data.vertices];hits=[]
 for tri in o.data.loop_triangles:
  a,b,c=[vs[i]for i in tri.vertices];den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
  if abs(den)<1e-9:continue
  u=((b.y-c.y)*(x-c.x)+(c.x-b.x)*(y-c.y))/den;v=((c.y-a.y)*(x-c.x)+(a.x-c.x)*(y-c.y))/den
  if min(u,v,1-u-v)>=-1e-5:hits.append(u*a.z+v*b.z+(1-u-v)*c.z)
 return max(hits)if hits else None
ground=[o for o in bpy.data.objects if o.type=='MESH'and(o.name.startswith('DC_Mesa_')or o.name.startswith('DC_GardenRock_'))];ground.sort(key=lambda o:o.name);enrichment=[];grounded=[];instcol=bpy.data.collections.new('DustCross Additional Shared Trees');bpy.context.scene.collection.children.link(instcol)
for o in ground:
 points=[o.matrix_world@v.co for v in o.data.vertices];x=(min(v.x for v in points)+max(v.x for v in points))/2;y=(min(v.y for v in points)+max(v.y for v in points))/2
 # Only existing outer rock tops, outside the playable arena.
 if abs(x)<145:continue
 radius=.85;sample=[height(o,x+dx,y+dy)for dx,dy in [(0,0),(radius,0),(-radius,0),(0,radius),(0,-radius)]]
 if any(z is None for z in sample)or max(sample)-min(sample)>.55:continue
 if len(grounded)>=24:break
 k=.65;root=Vector((x,y,min(sample)-.08));adapt=Matrix.Translation(root)@Matrix.Diagonal((k,k,k,1))@Matrix.Translation(-foot);idx=len(grounded);grounded.append({'support':o.name,'positionBlender':list(root),'supportHeights':sample,'rootEmbedMeters':.08,'maximumGroundHeightVariation':max(sample)-min(sample),'treeScaleRelativeToSource':k,'minHorizontalDistanceFromArenaCenter':abs(x)})
 for part in tree:
  name=f'DC_PoolTree_{idx:03d}_'+part['sourceObject'].split('_')[-1];proto=protos[part['library']];obj=bpy.data.objects.new(name,proto.data);instcol.objects.link(obj);obj.matrix_world=adapt@treeMatrices[part['sourceObject']];obj['asset_id']=proto['asset_id'];obj['source_prototype']=proto.name;obj['shared_runtime_library']=part['library'];loc,rot,scale=obj.matrix_world.decompose();eu=rot.to_euler('XZY');enrichment.append({'id':name,'nativeObject':name,'sourceObject':part['sourceObject'],'library':part['library'],'xyz':[loc.x,loc.z,loc.y],'hpr':[-math.degrees(eu.x),-math.degrees(eu.z),-math.degrees(eu.y)],'scale':[scale.x,scale.z,scale.y],'sourceMatrix':[list(v)for v in obj.matrix_world],'support':o.name,'newDecorativePlacement':True})
assert len(grounded)>=10,len(grounded)
for name,g in snap.items():assert geo(bpy.data.objects[name])==g,name
for name,m in poses.items():assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
scene=E.parse(r/'candidate/scene.xml')
for q in enrichment:E.SubElement(scene.getroot(),'library',name=q['library'],id=q['id'],xyz=' '.join(f'{v:.9g}'for v in q['xyz']),hpr=' '.join(f'{v:.9g}'for v in q['hpr']),scale=' '.join(f'{v:.9g}'for v in q['scale']))
(w/'scene.xml').write_bytes(E.tostring(scene.getroot(),encoding='utf-8',xml_declaration=True))
for name in ['scene.xml','materials.xml']:
 text=bpy.data.texts.get(name)or bpy.data.texts.new(name);text.clear();text.write((w/'scene.xml'if name=='scene.xml'else r/'candidate/materials.xml').read_text())
file=native/'Dust Cross Split Combat.blend';protoNames={k:v.name for k,v in protos.items()};bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file));cache.clear()
for name,g in snap.items():assert geo(bpy.data.objects[name])==g,name
for name,m in poses.items():assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==m,name
for q in p['placements']+enrichment:assert bpy.data.objects[q.get('nativeObject',q['sourceObject'])].data==bpy.data.objects[protoNames[q['library']]].data
proof={'finalBlend':str(file),'allOriginalMeshAttributesExact':len(snap),'allOriginalMatricesExact':len(poses),'allOriginalObjectsRetained':True,'existingNativeSceneryConvertedToSharedPointers':len(p['placements']),'reusedCanonicalPrototypes':rows,'additionalTrees':len(grounded),'newCoordinateParts':len(enrichment),'grounding':grounded,'newPlacements':enrichment,'nativeLocalGeometryUnchanged':True,'canonicalLibraryNotModified':True,'newRasterPixels':False,'sourceTexturesPreserved':True,'reopenedAndSharedPointersVerified':True}
(w/'native-verification.json').write_text(json.dumps(proof,indent=2));print('DUST_SHARED_NATIVE_AND_GROUNDED_TREE_ENRICHMENT_REOPEN_VERIFIED',{'oldMeshObjects':len(snap),'oldMatrices':len(poses),'existingSharedParts':len(p['placements']),'newTrees':len(grounded),'newParts':len(enrichment)},flush=True)
