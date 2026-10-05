import bpy,sys,math,json,shutil,xml.etree.ElementTree as E
from pathlib import Path
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';name='fluxara_driftlib_alpine_snow_column_v1';dest=pack/'models/summit-run-reference-v1/runtime-library'/name;dest.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
m=bpy.data.materials.new('SR Alpine Rock and Snow Palette');m.use_nodes=True;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(pack/'textures/dp-motorsports-reference-v2/dp_palette.png'));m.node_tree.links.new(t.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
vs=[];fs=[];colors=[];N=8
for z,rad in [(0,.40),(.48,.47),(.88,.36)]:
 for i in range(N):
  a=i*math.tau/N;rr=rad*(1+.08*math.sin(i*2.7));vs.append((rr*math.cos(a)+z*.045,rr*math.sin(a)-z*.025,z+.012*math.cos(i*1.7)))
for j in range(2):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i));colors.append(0 if i%3 else 8)
fs.append(tuple(range(16,24)));colors.append(0)
# An irregular cap follows the rock shoulders. Its low edge is deliberately uneven.
start=len(vs)
for z,rad in [(.79,.405),(.965,.355)]:
 for i in range(N):
  a=i*math.tau/N;vs.append((rad*math.cos(a)+.04,rad*math.sin(a)-.02,z+.045*math.sin(i*2.3)))
for i in range(N):fs.append((start+i,start+(i+1)%N,start+N+(i+1)%N,start+N+i));colors.append(13)
fs.append(tuple(start+N+i for i in range(N)));colors.append(13)
mesh=bpy.data.meshes.new('SR_AlpineColumnMesh');mesh.from_pydata(vs,[],fs);mesh.materials.append(m);uv=mesh.uv_layers.new(name='UVMap')
for p,c in zip(mesh.polygons,colors):
 for j in p.loop_indices:uv.data[j].uv=((c%4+.5)/4,1-(c//4+.5)/4)
o=bpy.data.objects.new('SR_AlpineSnowColumn_Prototype',mesh);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o;mesh.calc_loop_triangles()
bpy.ops.screen.spm_export(filepath=str(dest/'alpine_snow_column_main.spm'),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=True,export_tangent=False)
scene=E.Element('scene');E.SubElement(scene,'object',id='AlpineSnowColumn',type='animation',model='alpine_snow_column_main.spm',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'})
E.ElementTree(scene).write(dest/'node.xml',encoding='unicode');E.ElementTree(E.Element('materials')).write(dest/'materials.xml',encoding='unicode');shutil.copytree(dest,repo/'iosApp/FluxaraResources/library'/name,dirs_exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(r/'Alpine Snow Column.blend'))
a=json.load(open(r/'new-shared-runtime.json'));a['libraries']=[q for q in a['libraries'] if q['library']!=name]+[{'library':name,'path':str(dest),'bytes':sum(p.stat().st_size for p in dest.iterdir() if p.is_file()),'triangles':len(mesh.loop_triangles),'reuseTier':'authored','source':'Figma 378:49 snow-capped roadside rock columns; existing alpine mesa prototypes are over 2700 triangles each and do not fit this small detail budget','textureSource':str(pack/'textures/dp-motorsports-reference-v2/dp_palette.png')}];(r/'new-shared-runtime.json').write_text(json.dumps(a,indent=2));print('COLUMN_EXPORTED',len(mesh.loop_triangles))
