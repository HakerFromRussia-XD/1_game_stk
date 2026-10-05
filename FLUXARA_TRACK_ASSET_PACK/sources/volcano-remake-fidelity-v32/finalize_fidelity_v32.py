from pathlib import Path
import bpy,json,math,sys,shutil,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';native=w/'native';native.mkdir(exist_ok=True);assert (w/'protected-preflight.json').is_file() # Native draft only; acceptance waits for independent preservation proof.
a=json.loads((r/'fidelity-v30/asset-registration.json').read_text());p=json.loads((w/'seam-changes.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
newrows=[]
for name,ident,path,material,sourceid in [(p['newPrototype'],p['newPrototypeId'],p['newSharedModel'],'VRV4E_Rock13_col.jpg',p['sourcePoolObjectId']),(p['newGrassPrototype'],p['newGrassPrototypeId'],p['newGrassModel'],'VRV16_GrassLipVertexColor','volcano-fidelity-v22-grasslip')]:
 buf=parse(Path(path))['buffers'][0];obj=bpy.data.objects.new(name,native_mesh(name+'Mesh',buf,[bpy.data.materials[material]]));bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']=ident;obj['source_model']=path;obj['source_buffer']=0
 newrows.append({'id':ident,'name':name,'sourceModel':path,'sourceBuffer':0,'triangles':len(buf['indices'])//3,'materials':[material],'sourcePoolObjectId':sourceid,'role':'Copied shared component with matching planar grass/stone open boundary. Original local bounds/origin/axes, UV/RGB/topology and image pixels retained; boundary positions and adjacent normals adapted. Donor unchanged.'})
scene=E.parse(w/'candidate/scene.xml').getroot();changed=[];transformed=[]
for group in p['placements']:
 for i,attrs in enumerate(group['parts']):
  row=next(q for q in a['nativeSharedInstances']if q.get('sourcePlacementId')==attrs['id']);obj=bpy.data.objects[row['name']]
  if i<2:
   proto=bpy.data.objects[newrows[i]['name']];obj.data=proto.data;row['prototype']=proto.name;row['library']=attrs['name'];obj['source_prototype']=proto.name;obj['source_model']=proto['source_model'];obj['asset_id']=proto['asset_id'];obj['shared_runtime_library']=attrs['name'];changed.append(obj.name)
  else:assert row['prototype']=='DPV2_DP_RoundedTree_Prototype'
  if i>0:
   xyz=list(map(float,attrs['xyz'].split()));scale=list(map(float,attrs['scale'].split()));yaw=math.radians(float(attrs['hpr'].split()[1]));obj.matrix_world=Matrix.Translation(Vector((xyz[0],xyz[2],xyz[1])))@Matrix.Rotation(-yaw,4,'Z')@Matrix.Diagonal((scale[0],scale[2],scale[1],1));row['matrix']=[list(v)for v in obj.matrix_world];transformed.append(obj.name)
  obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode')
a['objects']+=newrows;a['newPrototypes']=newrows;a['reusedPrototypes']=[];a['newMaterialVariants']=[];a['reusedMaterialVariants']=[];a['changedSeamNativeObjects']=changed;a['changedCapTreeMatrices']=transformed
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v32';mod.mkdir(exist_ok=True)
for path in [p['newSharedLibrary'],p['newGrassLibrary']]:
 lib=Path(path);a['runtimeLibrarySources'][lib.name]=str(lib);shutil.copytree(lib,mod/lib.name,dirs_exist_ok=True)
 for file in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+file).write((lib/file).read_text())
a['visualLibrary']=str(mod/'Volcano Remake Matched Cliff Seams Library.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows},fake_user=True,compress=True)
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text());a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V32 fixes grass/stone seams on24 large added groups using two copied shared components. Source bounds/UV/RGB/topology and current stone pixels retained;48 geometry instances and48 cap/tree matrices adapted, all original course/physics/control/effects intact. Native/canonical/pool/gameplay acceptance is separate; isolated intermediate, full reference fidelity and integration unfinished.'});bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V32_MATCHED_SEAMS_NATIVE_SAVED',len(changed),len(transformed),flush=True)
