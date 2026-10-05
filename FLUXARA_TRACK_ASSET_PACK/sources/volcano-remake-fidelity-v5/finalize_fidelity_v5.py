from pathlib import Path
import bpy,sys,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';mod=pack/'models/volcano-remake-fidelity-v5';sources=pack/'sources/volcano-remake-fidelity-v5';native=w/'native'
for p in [mod,sources,native]:p.mkdir(exist_ok=True)
reg=json.loads((r/'fidelity-v4e/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
collection=bpy.data.collections['Volcano Remake Asset Prototypes'];newrows=[]
for row in json.loads((w/'smoke-changes.json').read_text()):
 name=row['model'];path=w/'candidate'/name;parsed=parse(path);vertices=[];faces=[];face_materials=[];slot_names=[]
 for b in parsed['buffers']:
  texture=parsed['materials'][b['material']][0];matname=next(q['name']for q in reg['materials']if texture in q['textures'])
  if matname not in slot_names:slot_names.append(matname)
  offset=len(vertices);vertices.extend(b['vertices']);faces.extend(tuple(offset+i for i in reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3));face_materials.extend([slot_names.index(matname)]*(len(b['indices'])//3))
 mesh=bpy.data.meshes.new('VRV5_'+Path(name).stem+'_Billows');mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1])for v in vertices],[],faces);mesh.uv_layers.new(name='UVMap')
 for matname in slot_names:mesh.materials.append(bpy.data.materials[matname])
 for polygon,mi in zip(mesh.polygons,face_materials):
  polygon.material_index=mi;polygon.use_smooth=True
  for loop in polygon.loop_indices:mesh.uv_layers['UVMap'].data[loop].uv=vertices[mesh.loops[loop].vertex_index]['uv']
 matched=[]
 for obj in list(bpy.data.objects):
  if obj.type=='MESH' and Path(obj.get('source_model','')).name==name:
   old=obj.data
   for linked in list(bpy.data.objects):
    if linked.type=='MESH' and linked.data==old:linked.data=mesh
   obj['source_model']=str(path);matched.append(obj.name)
 assert matched,name
 obj=bpy.data.objects.new('VRV5_Cloud_'+Path(name).stem,mesh);collection.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']='volcano-fidelity-v5-cloud-'+Path(name).stem.lower();obj['source_model']=str(path);mesh.calc_loop_triangles();assert len(mesh.loop_triangles)==row['triangles']
 q={'id':obj['asset_id'],'name':obj.name,'sourceModel':str(path),'triangles':len(mesh.loop_triangles),'materials':slot_names,'role':'Authored overlapping near-spherical smoke billows; preserved source envelope and unchanged scene animation.','nativeSourceObjectsUpdated':matched};newrows.append(q);reg['objects'].append(q);shutil.copy2(path,mod/name)
for row in reg['nativeOriginalObjects']:
 if Path(row['model']).name in {q['model']for q in json.loads((w/'smoke-changes.json').read_text())}:row['model']=Path(row['model']).name
reg['finalBlend']=str(native/'Volcano Remake.blend');reg['visualLibrary']=str(mod/'Volcano Remake Cloud Library.blend');reg['reusedPrototypeIds']=[q['id']for q in reg['objects']if not q['id'].startswith('volcano-fidelity-v5-')];reg['newPrototypes']=newrows;reg['status']='Candidate V5; production unchanged.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend']);bpy.data.libraries.write(reg['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows}|{bpy.data.materials[n]for q in newrows for n in q['materials']},fake_user=True)
(w/'asset-registration.json').write_text(json.dumps(reg,indent=2));shutil.copy2(w/'Smoke Billow Sources.blend',sources/'Smoke Billow Sources.blend')
print('V5_NATIVE_READY',len(reg['objects']),len(newrows),flush=True)
