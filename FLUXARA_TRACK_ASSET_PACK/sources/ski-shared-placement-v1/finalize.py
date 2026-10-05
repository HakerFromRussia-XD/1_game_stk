import bpy,sys,json,math,shutil,hashlib,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector,Matrix,Euler
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';tex=pack/'textures/ski-shared-placement-v1';mod=pack/'models/ski-shared-placement-v1';sources=pack/'sources/ski-shared-placement-v1';out=r.parent/'fluxara-user-ski-dash-final'
for p in [tex,mod,sources]:p.mkdir(parents=True,exist_ok=True)
shutil.copytree(r/'before',sources/'original-runtime',dirs_exist_ok=True);shutil.copy2(r/'before-native.blend',sources/'original-native.blend');a=json.load(open(r/'ski-extraction.json'));bpy.ops.wm.open_mainfile(filepath=str(r/'before-native.blend'));bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm
try:io_scene_spm.register()
except ValueError:pass
col=bpy.data.collections.new('Ski Dash Shared Coordinate Instances');bpy.context.scene.collection.children.link(col);protos=bpy.data.collections.new('Ski Dash Runtime Pool Prototypes');bpy.context.scene.collection.children.link(protos);registered=[];textures={};usedmats=set();models={};nativeInstances=[]
# Keep all existing visual image pixels physically reusable, and keep legacy IDs.
for image in bpy.data.images:
 if image.source!='FILE':continue
 if image.packed_file:
  data=bytes(image.packed_file.data);p=tex/Path(image.filepath).name;p.write_bytes(data)
 elif Path(bpy.path.abspath(image.filepath)).is_file():
  old=Path(bpy.path.abspath(image.filepath));p=tex/old.name;shutil.copy2(old,p)
 else:raise AssertionError(('Missing original native image',image.name,image.filepath))
# Original 71 firs are replaced with actual exported geometry at the same transforms.
oldparts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('SkiDash_ClifftopFir_','SkiDash_RelocatedFir_'))];assert len(oldparts)==142
for o in oldparts:bpy.data.objects.remove(o,do_unlink=True)
for q in a['placements']:
 if q.get('sourceObject') and not q.get('existingCoordinateInstance'):bpy.data.objects.remove(bpy.data.objects[q['sourceObject']],do_unlink=True)
for q in a['prototypes']:
 path=Path(q['model']);dst=mod/'runtime-library'/path.parent.name;shutil.copytree(path.parent,dst,dirs_exist_ok=True);before=set(bpy.data.objects);bpy.ops.screen.spm_import(filepath=str(path),extra_tex_path=str(r/'new-textures'));rows=[]
 for i,o in enumerate(set(bpy.data.objects)-before):
  if o.type!='MESH':continue
  for m in o.data.materials:
   if not m:continue
   m.name='SKS2MAT_'+m.name;usedmats.add(m)
   if m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image:
      name=Path(n.image.filepath).name;src=r/'new-textures'/name;assert src.is_file(),name;p=tex/name;shutil.copy2(src,p);image=bpy.data.images.load(str(p),check_existing=False);n.image=image;image.pack();textures[name]={'source':str(src),'packPath':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
  for c in list(o.users_collection):c.objects.unlink(o)
  protos.objects.link(o);o.name='SKS2_Prototype_'+q['library']+'_'+str(i);o.hide_set(True);o.hide_render=True;o['asset_id']='ski-shared-v1-object-'+hashlib.sha256(o.name.encode()).hexdigest()[:12];o['source_model']=str(path);models.setdefault(q['library'],[]).append(o);o.data.calc_loop_triangles();registered.append({'id':o['asset_id'],'name':o.name,'sourceModel':str(dst/path.name),'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials if m]})
for q in a['placements']+a['extraCoordinatePlacements']:
 xyz=q['xyz'];hpr=q['hpr'];scale=q['scale'];rot=Euler(tuple(math.radians(-v) for v in [hpr[0],hpr[2],hpr[1]]),'XZY');matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@rot.to_matrix().to_4x4()@Matrix.Diagonal((scale[0],scale[2],scale[1],1))
 for proto in models[q['library']]:
  o=bpy.data.objects.new('SKS2_'+q['id']+'_'+proto.name.rsplit('_',1)[-1],proto.data);col.objects.link(o);o.matrix_world=matrix;o['shared_runtime_library']=q['library'];o['source_prototype']=proto.name;o['source_placement_id']=q['id'];nativeInstances.append({'name':o.name,'prototype':proto.name,'library':q['library'],'matrix':[list(v) for v in matrix]})
for name in ['scene.xml','materials.xml','track.xml','navmesh.xml']:
 t=bpy.data.texts.get(name) or bpy.data.texts.new(name);t.clear();t.write((r/'candidate'/name).read_text())
for p in (r/'candidate').iterdir():
 if p.is_file():shutil.copy2(p,out/p.name)
# Remove only promoted runtime files from final delivery, originals remain in source archive.
for name in [q['original'] for q in a['textures']]+['ski-dash-branchless-fir-v12.spm']:
 p=out/name
 if p.exists():p.unlink()
materials=[{'id':'ski-shared-v1-material-'+hashlib.sha256(m.name.encode()).hexdigest()[:12],'name':m.name,'textures':sorted({Path(n.image.filepath).name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}) if m.use_nodes else []} for m in usedmats];lib=mod/'Ski Dash Shared Visual Library.blend';bpy.data.libraries.write(str(lib),set(protos.objects)|usedmats,fake_user=True)
for image in list(bpy.data.images):
 if image.users==0:bpy.data.images.remove(image);continue
 if image.source=='FILE' and not image.packed_file and not Path(bpy.path.abspath(image.filepath)).is_file():
  local=tex/Path(image.filepath).name;assert local.is_file(),image.filepath;image.filepath=str(local);image.reload()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Ski Dash.blend'))
(r/'asset-registration.json').write_text(json.dumps({'objects':registered,'materials':materials,'textures':textures,'nativeSharedInstances':nativeInstances,'visualLibrary':str(lib),'finalBlend':str(out/'Ski Dash.blend'),'originalUnrelatedNativeObjectsPreserved':True},indent=2));print('SKI_FINAL_BLEND_READY',len(registered),len(materials),len(nativeInstances),flush=True)
