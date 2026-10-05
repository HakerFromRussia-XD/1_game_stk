from pathlib import Path
import bpy,json,sys,math,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';native=w/'native';native.mkdir(exist_ok=True);pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v10';mod.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v9/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
code=(r/'finalize_fidelity_v9.py').read_text();exec(code[code.index('def mesh_from_buffer'):code.index("updates=a[")]);image=bpy.data.images.load(str(w/'candidate/vr_moss_palette.jpg'),check_existing=False);image.pack();mat=bpy.data.materials.new('VRV10_CliffStone');mat.use_nodes=True;mat['asset_id']='volcano-fidelity-v10-cliff-material';bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Roughness'].default_value=1;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);new=[];updates=[]
for row in json.loads((w/'cliff-changes.json').read_text()):
 name=row['model'];d=parse(w/'candidate'/name);index=row['buffers'][0]['buffer'];buffer=d['buffers'][index]
 targets=[obj for obj in bpy.data.objects if obj.type=='MESH'and Path(obj.get('source_model','')).name==name and any(any(n.type=='TEX_IMAGE'and n.image and Path(n.image.filepath).name=='Rock13_col.jpg'for n in m.node_tree.nodes)for m in obj.data.materials if m and m.use_nodes)]
 assert targets,(name,'missing original cliff objects');mesh=mesh_from_buffer('VRV10_CliffMesh_'+Path(name).stem,buffer,[mat]);normals=[]
 for loop in mesh.loops:
  value=buffer['vertices'][loop.vertex_index]['normal'];n=[((value>>(10*k))&1023)for k in range(3)];n=[(v-1024 if v>511 else v)/511 for v in n];normals.append((n[0],n[2],n[1]))
 mesh.normals_split_custom_set(normals)
 for obj in targets:obj.data=mesh
 proto=bpy.data.objects.new('VRV10_Prototype_Cliff_'+Path(name).stem,mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v10-cliff-'+Path(name).stem;proto['source_model']=str(w/'candidate'/name);proto['source_buffer']=index
 q={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(w/'candidate'/name),'sourceBuffer':index,'triangles':len(buffer['indices'])//3,'materials':[mat.name]};new.append(q);updates.append({'model':name,'buffer':index,'objects':[o.name for o in targets],'prototype':proto.name,'uvConvention':'Blender u,1-SPM-v','customNormalsMatchSpm':True});(mod/name).write_bytes((w/'candidate'/name).read_bytes())
for obj in bpy.data.objects:
 if Path(obj.get('source_model','')).name in {q['model']for q in updates}:obj['source_model']=str(w/'candidate'/Path(obj['source_model']).name)
a['objects']+=new;a['materials'].append({'id':mat['asset_id'],'name':mat.name,'textures':['vr_moss_palette.jpg']});a['newPrototypes']=new;a['reusedPrototypeIds']=[q['id']for q in a['objects']if q not in new];a['visualLibrary']=str(mod/'Volcano Remake Cliff Library.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in new},fake_user=True,compress=True)
bpy.data.texts['materials.xml'].clear();bpy.data.texts['materials.xml'].write((w/'candidate/materials.xml').read_text())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'cliffBufferUpdates':updates,'status':'V10 isolated smooth stone-palette cliffs; source positions/indices/colours/bounds retained, packed decorative normals and UVs changed. No new texture files. Production unchanged.'});bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V10_NATIVE_READY',len(a['objects']),len(a['nativeSharedInstances']),flush=True)
