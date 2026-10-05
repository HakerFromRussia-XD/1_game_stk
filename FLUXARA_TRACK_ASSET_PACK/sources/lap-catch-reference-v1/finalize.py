import bpy,sys,json,math,shutil,hashlib,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector,Euler,Matrix
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';f=r/'candidate';out=r.parent/'fluxara-user-lap-catch-final';out.mkdir(exist_ok=True);tex=pack/'textures/lap-catch-reference-v1';mod=pack/'models/lap-catch-reference-v1';sources=pack/'sources/lap-catch-reference-v1'
for p in [tex,mod,sources]:p.mkdir(parents=True,exist_ok=True)
# Preserve all source/input evidence outside the one final track project.
shutil.copytree(r/'before',sources/'original-runtime',dirs_exist_ok=True);shutil.copytree(r/'references',sources/'references',dirs_exist_ok=True)
for p in r.iterdir():
 if p.suffix in ['.py','.js','.svg','.json']:shutil.copy2(p,sources/p.name)
archive=sources/'replaced-draft-runtime';archive.mkdir(exist_ok=True)
for p in out.iterdir():
 if p.is_file() and p.name!='Lap Catch.blend' and not (f/p.name).exists():
  shutil.copy2(p,archive/p.name);p.unlink()
for p in f.iterdir():
 if p.is_file():shutil.copy2(p,out/p.name)
app=repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app';global_files={p.name:p for p in (app/'data/textures').rglob('*') if p.is_file()};texture_sources={};cache={};registered=[];runtime_library_sources={}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
base=bpy.data.collections.new('Lap Catch Original Course');bpy.context.scene.collection.children.link(base);sc=bpy.data.collections.new('Lap Catch Shared Instances');bpy.context.scene.collection.children.link(sc);controls=bpy.data.collections.new('Lap Catch Protected Gameplay');bpy.context.scene.collection.children.link(controls);protos_col=bpy.data.collections.new('Lap Catch Asset Prototypes');bpy.context.scene.collection.children.link(protos_col)
def source_texture(name,folder):
 p=folder/name
 if not p.exists():p=global_files.get(name,global_files.get(name.replace('stk','fluxara_drift')))
 assert p and p.exists(),(name,folder)
 if name in texture_sources:assert texture_sources[name]['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),('Ambiguous source texture',name)
 target=tex/name
 if target.exists() and hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(target.read_bytes()).digest():
  old=sources/'replaced-draft-textures';old.mkdir(exist_ok=True);shutil.copy2(target,old/(hashlib.sha256(target.read_bytes()).hexdigest()[:12]+'-'+name))
 shutil.copy2(p,target)
 texture_sources[name]={'source':str(p),'packPath':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()};return target

def load_model(path,shared=False):
 if str(path) in cache:return cache[str(path)]
 before=set(bpy.data.objects);bpy.ops.screen.spm_import(filepath=str(path),extra_tex_path=str(tex));objects=list(set(bpy.data.objects)-before);rows=[]
 for j,o in enumerate(objects):
  if o.type!='MESH':continue
  # The importer's placeholder behavior is corrected by resolving every actual file explicitly.
  for m in o.data.materials:
   if m and m.use_nodes:
    for node in m.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      name=Path(node.image.filepath).name;target=source_texture(name,path.parent);node.image.filepath=str(target);node.image.reload()
      if path.parent.name=='fluxara_driftlib_castle_waterfall_v1':
       bsdf=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(node.outputs['Alpha'],bsdf.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
  for c in list(o.users_collection):c.objects.unlink(o)
  (protos_col if shared else base).objects.link(o);o.name='LC_Prototype_'+path.stem+'_'+str(j) if shared else 'LC_OriginalSurface_'+str(j).zfill(3);o['source_model']=str(path);o['protected_course_geometry']=not shared;o['asset_id']='lap-v1-'+hashlib.sha256((str(path)+str(j)).encode()).hexdigest()[:16]
  if shared:o.hide_set(True);o.hide_render=True
  o.data.calc_loop_triangles();rows.append(o)
  if shared:registered.append({'id':o['asset_id'],'name':o.name,'sourceModel':str(path),'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials if m]})
 cache[str(path)]=rows;return rows
load_model(f/'lap-catch_track.spm')

def transform(e):
 xyz=list(map(float,e.get('xyz','0 0 0').split()));hpr=list(map(float,e.get('hpr','0 0 0').split()));scale=list(map(float,e.get('scale','1 1 1').split()));rot=Euler(tuple(math.radians(-a) for a in [hpr[0],hpr[2],hpr[1]]),'XZY');return Matrix.Translation((xyz[0],xyz[2],xyz[1]))@rot.to_matrix().to_4x4()@Matrix.Diagonal((scale[0],scale[2],scale[1],1))
placements=[]
def place_lib(name,parent,prefix,depth=0):
 assert depth<8,name
 folder=repo/'iosApp/FluxaraResources/library'/name;root=E.parse(folder/'node.xml').getroot();runtime_library_sources[name]=str(folder)
 if bpy.data.texts.get(name+'/node.xml') is None:bpy.data.texts.new(name+'/node.xml').write((folder/'node.xml').read_text())
 models=[q for q in root.findall('object') if q.get('model') and q.get('interaction')!='physicsonly']
 for g in root.findall('./lod/group'):
  if list(g):models.append(list(g)[0])
 for q in models:
  mat=parent@transform(q)
  for proto in load_model(folder/q.get('model'),True):
   o=bpy.data.objects.new(prefix+'_'+q.get('id',q.get('model'))+'_'+proto.name,proto.data);sc.objects.link(o);o.matrix_world=mat;o['shared_runtime_library']=name;o['source_prototype']=proto.name;placements.append({'name':o.name,'prototype':proto.name,'library':name,'matrix':[list(row) for row in mat]})
 for q in root.findall('object'):
  if q.get('interaction')=='physicsonly':
   o=bpy.data.objects.new(prefix+'_physics_'+q.get('id','node'),None);controls.objects.link(o);o.matrix_world=parent@transform(q);o['protected_original_physics']=True;o['source_xml']=E.tostring(q,encoding='unicode');o.hide_render=True;o.hide_set(True)
 for q in root.findall('library'):place_lib(q.get('name'),parent@transform(q),prefix+'_'+q.get('id','nested'),depth+1)
scene=E.parse(f/'scene.xml').getroot()
for e in scene.findall('library'):place_lib(e.get('name'),transform(e),e.get('id','library'))
for i,e in enumerate(scene):
 if e.tag not in ['object','banana','item','small-nitro','big-nitro','default-start']:continue
 o=bpy.data.objects.new('LC_Gameplay_'+str(i)+'_'+e.get('id',e.tag),None);controls.objects.link(o);o['protected_gameplay']=True;o['source_xml']=E.tostring(e,encoding='unicode')
 if e.get('xyz'):o.matrix_world=transform(e)
 else:o.location=(float(e.get('x','0')),float(e.get('z','0')),float(e.get('y','0')))
 o.hide_render=True;o.hide_set(True)
for i,e in enumerate(scene.find('checks')):
 o=bpy.data.objects.new('LC_Check_'+str(i),None);controls.objects.link(o);o['protected_gameplay']=True;o['source_xml']=E.tostring(e,encoding='unicode');o.hide_set(True);o.hide_render=True
quads=[]
for e in E.parse(f/'quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));q.append(quads[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 quads.append(q)
vs=[(p[0],p[2],p[1]) for q in quads for p in q];faces=[tuple(i*4+j for j in range(4)) for i in range(len(quads))];me=bpy.data.meshes.new('LC_Protected_Quads');me.from_pydata(vs,[],faces);o=bpy.data.objects.new('LC_Protected_Quads',me);controls.objects.link(o);o['protected_gameplay']=True;o.hide_set(True);o.hide_render=True
for n in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:bpy.data.texts.new(n).write((f/n).read_text())
# Save all visual material setups, and only reusable scenery meshes (route/control geometry remains in the map).
usedmats=set(m for o in list(base.objects)+list(sc.objects) for m in o.data.materials if m);material_rows=[]
for m in usedmats:
 oldname=m.name;m.name='LCV1_'+m.name;material_rows.append({'id':'lap-v1-material-'+hashlib.sha256(m.name.encode()).hexdigest()[:12],'name':m.name,'oldName':oldname,'textures':sorted({Path(n.image.filepath).name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}) if m.use_nodes else []})
for row in registered:row['materials']=[m.name for m in bpy.data.objects[row['name']].data.materials if m]
lib=mod/'Lap Catch Visual Library.blend';bpy.data.libraries.write(str(lib),set(protos_col.objects)|usedmats,fake_user=True)
world=bpy.data.worlds.new('LC Sunny World');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.47,.7,.92,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8;bpy.context.scene.world=world
ld=bpy.data.lights.new('LC Afternoon Sun','SUN');ld.energy=2.0;ld.angle=math.radians(12);o=bpy.data.objects.new(ld.name,ld);bpy.context.scene.collection.objects.link(o);o.rotation_euler=(.5,-.45,-.5)

# Importer eagerly creates materials/images for unused SPM table slots. Keep only real mesh dependencies.
for m in list(bpy.data.materials):
 if m not in usedmats:bpy.data.materials.remove(m,do_unlink=True)
for image in list(bpy.data.images):
 if image.users==0:bpy.data.images.remove(image)
for image in bpy.data.images:
 if image.source=='FILE':assert Path(bpy.path.abspath(image.filepath)).is_file(),image.filepath
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Lap Catch.blend'))
(r/'asset-registration.json').write_text(json.dumps({'objects':registered,'materials':material_rows,'textures':texture_sources,'nativeSharedInstances':placements,'runtimeLibrarySources':runtime_library_sources,'visualLibrary':str(lib),'finalBlend':str(out/'Lap Catch.blend'),'protectedQuads':len(quads)},indent=2));print('FINAL_BLEND_READY',len(registered),len(material_rows),len(placements),len(texture_sources))
