from pathlib import Path
import bpy,json,math,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v35';native=w/'native';native.mkdir(exist_ok=True)
assert (w/'existing-seam-changes.json').is_file() # Native early draft; independent clearance and runtime acceptance separate.
a=json.loads((r/'fidelity-v32/asset-registration.json').read_text());p=json.loads((r/'fidelity-v34/valley-preflight.json').read_text());support=json.loads((r/'fidelity-v34/castle-supports.json').read_text());split=json.loads((r/'fidelity-v33/mass-replacement-preflight.json').read_text());scene=E.parse(w/'candidate/scene.xml').getroot()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
def matrix(attrs):
 xyz=list(map(float,attrs['xyz'].split()));scale=list(map(float,attrs['scale'].split()));assert attrs['hpr'] in ['0 0 0','0.00000000 0.00000000 0.00000000'] or float(attrs['hpr'].split()[0])==float(attrs['hpr'].split()[2])==0
 yaw=math.radians(float(attrs['hpr'].split()[1]));return Matrix.Translation(Vector((xyz[0],xyz[2],xyz[1])))@Matrix.Rotation(-yaw,4,'Z')@Matrix.Diagonal((scale[0],scale[2],scale[1],1))
changed=[]
for q in p['cliffBodyPlacements']:
 attrs=q['after'];row=next(x for x in a['nativeSharedInstances']if x.get('sourcePlacementId')==attrs['id']);obj=bpy.data.objects[row['name']];obj.matrix_world=matrix(attrs);row['matrix']=[list(v)for v in obj.matrix_world];obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode');changed.append(obj.name)
seam35=json.loads((w/'existing-seam-changes.json').read_text());seamgeo=[];capmatrices=[]
for group in seam35['groups']:
 for role,attrs in zip(['Stone','Grass'],group['partsAfter']):
  row=next(x for x in a['nativeSharedInstances']if x.get('sourcePlacementId')==attrs['id']);obj=bpy.data.objects[row['name']];proto=bpy.data.objects['VRV32_Prototype_SealedStoneBody' if role=='Stone' else 'VRV32_Prototype_SealedGrassCap'];obj.data=proto.data;row['prototype']=proto.name;row['library']=attrs['name'];obj['source_prototype']=proto.name;obj['source_model']=proto['source_model'];obj['asset_id']=proto['asset_id'];obj['shared_runtime_library']=attrs['name'];obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode');seamgeo.append(obj.name)
  if role=='Grass':obj.matrix_world=matrix(attrs);row['matrix']=[list(v)for v in obj.matrix_world];capmatrices.append(obj.name)
a['changedExistingSeamGeometryObjects']=seamgeo;a['changedExistingGrassMatrices']=capmatrices
stone=bpy.data.materials['VRV4E_Rock13_col.jpg']
walls=[o for o in bpy.data.objects if o.name.startswith('VR_OriginalSurface_') and o.type=='MESH' and len(o.data.polygons)==2210 and stone in list(o.data.materials)]
assert len(walls)==1,[o.name for o in walls];wall=walls[0];assert max(abs(wall.matrix_world[i][j]-Matrix.Identity(4)[i][j])for i in range(4)for j in range(4))<1e-6
main=parse(w/'candidate/volcano_track.spm');wall.data=native_mesh('VRV35_RetainedWallsMesh',main['buffers'][split['mainWallBuffer']],[stone]);wall['source_model']=str(w/'candidate/volcano_track.spm')
path=w/'candidate'/split['physicsProxyFile'];proxy=bpy.data.objects.new('VRV33_OriginalLargeWallCollision',native_mesh('VRV33_ExactLargeWallCollisionMesh',parse(path)['buffers'][0],[stone]));next(x for x in bpy.data.collections if 'Protected'in x.name).objects.link(proxy);proxy.hide_set(True);proxy.hide_render=True;proxy['source_model']=str(path);proxy['source_xml']=E.tostring(scene.find('object[@id="VRV33_OriginalLargeWallCollision"]'),encoding='unicode');proxy['protected_course_geometry']=True
a['nativeOriginalObjects'].append({'name':proxy.name,'model':path.name,'matrix':[list(v)for v in proxy.matrix_world],'sourceXml':proxy['source_xml']})
added=[]
for q in support['newCoordinateSupports']:
 attrs=q['support'];proto=bpy.data.objects['VRV32_Prototype_SealedStoneBody'];obj=bpy.data.objects.new(attrs['id'],proto.data);bpy.data.collections['Volcano Remake Shared Instances'].objects.link(obj);obj.matrix_world=matrix(attrs);obj['source_prototype']=proto.name;obj['source_model']=proto['source_model'];obj['asset_id']=proto['asset_id'];obj['shared_runtime_library']=attrs['name'];obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode')
 a['nativeSharedInstances'].append({'name':obj.name,'prototype':proto.name,'library':attrs['name'],'matrix':[list(v)for v in obj.matrix_world],'sourcePlacementId':attrs['id']});added.append(obj.name)
floor=scene.find('object[@id="VRV34_LavaValley"]');static=[q for q in a['nativeStaticObjects']if q['model']=='Lavafield.spm'];assert len(static)==3
newrows=[]
for i,q in enumerate(static):
 old=bpy.data.objects[q['name']];proto=bpy.data.objects.new(f'VRV35_Prototype_LavaValley_{i}',old.data);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']=f'volcano-fidelity-v35-reused-lava-valley-{i}';proto['source_model']=str(w/'candidate/Lavafield.spm');proto['source_buffer']=[2,1,0][i]
 obj=bpy.data.objects.new(f'VRV35_LavaValley_{i}',proto.data);bpy.data.collections['Volcano Remake Shared Instances'].objects.link(obj);obj.matrix_world=matrix(floor.attrib);obj['source_model']=proto['source_model'];obj['source_prototype']=proto.name;obj['asset_id']=proto['asset_id'];obj['source_xml']=E.tostring(floor,encoding='unicode')
 a['nativeSharedInstances'].append({'name':obj.name,'prototype':proto.name,'library':'map-local-reuse-Lavafield','matrix':[list(v)for v in obj.matrix_world],'sourcePlacementId':floor.get('id')});added.append(obj.name)
 newrows.append({'id':proto['asset_id'],'name':proto.name,'sourceModel':proto['source_model'],'sourceBuffer':[2,1,0][i],'sourceNativeStaticObject':old.name,'triangles':len(old.data.polygons),'materials':[m.name for m in old.data.materials],'sourcePoolObjectId':'volcano-fidelity-v3-model-e45f7ddeca7c','role':'Direct reuse of existing map-local Lavafield buffer and current shared lava texture alias. A coordinate instance below all protected road vertices; original field and source geometry, normals, UVs, colors and pixels unchanged.'})
a['objects']+=newrows;a['newPrototypes']=newrows;a['reusedPrototypes']=[];a['newMaterialVariants']=[];a['reusedMaterialVariants']=[];a['changedValleyBodyMatrices']=changed;a['newValleyNativeObjects']=added;a['changedLargeWallNativeObject']=wall.name;a['exactLargeWallCollisionNativeObject']=proxy.name
for name in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:
 bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v35';mod.mkdir(exist_ok=True)
a['visualLibrary']=str(mod/'Volcano Remake Reused Lava Valley Library.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows},fake_user=True,compress=True)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V35 matched82 grass/stone interfaces and separated cliff masses with original large-wall physics retained, reused lava valley below protected road,82 extended stone feet and15 reused castle supports. Source stone pixels and source local model dimensions retained; independent source clearance passed. Native/runtime/pool/reference checks separate; isolated draft, production integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V35_NATIVE_VALLEY_AND_CASTLE_SUPPORTS_SAVED',wall.name,len(changed),len(added),len(a['objects']),flush=True)
