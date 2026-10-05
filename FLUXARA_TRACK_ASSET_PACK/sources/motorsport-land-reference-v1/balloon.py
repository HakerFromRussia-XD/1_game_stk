import bpy,math,sys,shutil,xml.etree.ElementTree as E,json
from pathlib import Path
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';dest=pack/'models/motorsport-land-reference-v1/runtime-library/fluxara_driftlib_festival_balloon_v1';dest.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
m=bpy.data.materials.new('ML Festival Palette');m.use_nodes=True;n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(pack/'textures/dp-motorsports-reference-v2/dp_palette.png'));m.node_tree.links.new(n.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10);o=bpy.context.object;o.name='ML_FestivalBalloon_Prototype'
for v in o.data.vertices:
 v.co.x*=.48;v.co.y*=.48;v.co.z=.68+v.co.z*.49
o.data.materials.append(m);uv=o.data.uv_layers[0]
for p in o.data.polygons:
 a=math.atan2(p.center.y,p.center.x);c=[1,9,2,0][int((a+math.pi)/math.tau*16)%4];p.use_smooth=True
 for k in p.loop_indices:uv.data[k].uv=((c%4+.5)/4,1-(c//4+.5)/4)
parts=[o]
def paint(q,c):
 q.data.materials.append(m);uv=q.data.uv_layers[0] if q.data.uv_layers else q.data.uv_layers.new()
 for p in q.data.polygons:
  for k in p.loop_indices:uv.data[k].uv=((c%4+.5)/4,1-(c//4+.5)/4)
 parts.append(q)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.06));q=bpy.context.object;q.scale=(.22,.22,.14);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);paint(q,7)
for x,y in [(-.09,-.09),(-.09,.09),(.09,-.09),(.09,.09)]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=4,radius=.012,depth=.14,location=(x,y,.17));paint(bpy.context.object,3)
bpy.ops.object.select_all(action='DESELECT')
for q in parts:q.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.data.calc_loop_triangles()
bpy.ops.screen.spm_export(filepath=str(dest/'festival_balloon_main.spm'),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=True,export_tangent=False)
scene=E.Element('scene');E.SubElement(scene,'object',id='FestivalBalloon',type='animation',model='festival_balloon_main.spm',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'})
E.ElementTree(scene).write(dest/'node.xml',encoding='unicode');E.ElementTree(E.Element('materials')).write(dest/'materials.xml',encoding='unicode');shutil.copytree(dest,repo/'iosApp/FluxaraResources/library'/dest.name,dirs_exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Festival Balloon.blend'));(r/'new-shared-runtime.json').write_text(json.dumps({'libraries':[{'library':dest.name,'folder':str(dest),'model':'festival_balloon_main.spm','triangles':len(o.data.loop_triangles),'bytes':sum(p.stat().st_size for p in dest.iterdir() if p.is_file())}],'source':'Native low-poly balloon, based on Figma 390:124; reuses existing circuit palette'},indent=2));print('BALLOON_EXPORTED',len(o.data.loop_triangles))
