import bpy,sys,math,json,shutil,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';name='fluxara_driftlib_summit_cascade_v1';dest=pack/'models/summit-run-reference-v1/runtime-library'/name;dest.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/ancient-summits_track.spm');b=d['buffers'][9];vs=[(v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']];fs=[tuple(b['indices'][i:i+3]) for i in range(0,len(b['indices']),3)];surface=BVHTree.FromPolygons(vs,fs,all_triangles=True);points=[]
for i in range(13):
 y=36+40*i/12
 for z in [-60,-68]:
  p,n,_,_=surface.ray_cast(Vector((-45,z,y)),Vector((-1,0,0)),150);assert p is not None,('No cliff surface',i,z,y)
  points.append((p.x+.065,z,y))
root=Vector(((points[0][0]+points[1][0])/2,-64,36));bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
me=bpy.data.meshes.new('SR_CliffCascadeMesh');me.from_pydata([Vector((p[0],p[1],p[2]))-root for p in points],[],[(i*2,(i+1)*2,(i+1)*2+1,i*2+1) for i in range(12)]);uv=me.uv_layers.new(name='UVMap')
for face in me.polygons:
 for k in face.loop_indices:
  index=me.loops[k].vertex_index;uv.data[k].uv=(index%2,index//2/12)
flow=pack/'textures/lap-catch-reference-v1/fluxara_water_flow.png';assert flow.is_file();shutil.copy2(flow,dest/flow.name);m=bpy.data.materials.new('SR Cascade Flow');m.use_nodes=True;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(flow));bs=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(t.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False;me.materials.append(m);o=bpy.data.objects.new('SR_SurfaceConformingCascade_Prototype',me);bpy.context.scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.screen.spm_export(filepath=str(dest/'summit_cascade_main.spm'),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=True,export_tangent=False)
node=E.Element('scene');q=E.SubElement(node,'object',id='SummitCascade',model='summit_cascade_main.spm',type='animation',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'});E.SubElement(q,'animated-texture',name=flow.name,dx='0',dy='.12');E.ElementTree(node).write(dest/'node.xml',encoding='unicode');mats=E.Element('materials');E.SubElement(mats,'material',name=flow.name,shader='alphablend',ignore='Y',**{'disable-z-write':'Y','backface-culling':'N'});E.ElementTree(mats).write(dest/'materials.xml',encoding='unicode');shutil.copytree(dest,repo/'iosApp/FluxaraResources/library'/name,dirs_exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(r/'Summit Cascade.blend'))
scene=E.parse(r/'candidate/scene.xml')
for q in list(scene.getroot()):
 if q.get('id')=='SR_Cascade_001':scene.getroot().remove(q)
xyz=[root.x,root.z,root.y];E.SubElement(scene.getroot(),'library',id='SR_Cascade_001',name=name,xyz=' '.join(map(str,xyz)),hpr='0 0 0',scale='1 1 1');scene.write(r/'candidate/scene.xml',encoding='unicode');rows=[q for q in json.load(open(r/'placements.json')) if q['name']!='SR_Cascade_001'];rows.append({'name':'SR_Cascade_001','library':name,'role':'cascade','xyz':xyz,'hpr':[0,0,0],'scale':[1,1,1],'rotationZRadians':0});(r/'placements.json').write_text(json.dumps(rows,indent=2))
a=json.load(open(r/'new-shared-runtime.json'));a['libraries']=[q for q in a['libraries'] if q['library']!=name]+[{'library':name,'path':str(dest),'bytes':sum(p.stat().st_size for p in dest.iterdir() if p.is_file()),'source':'Reference waterfall geometry conformed to the existing snow-cliff surface; pooled flow texture reused','reuseTier':'authored','triangles':24,'textureSource':str(flow)}];(r/'new-shared-runtime.json').write_text(json.dumps(a,indent=2));layout=json.load(open(r/'layout-summary.json'));layout['counts']['cascade']=1;(r/'layout-summary.json').write_text(json.dumps(layout,indent=2));(r/'waterfall-conformance.json').write_text(json.dumps({'mountainGeometryChanged':False,'surfaceOffset':.065,'worldVertices':points,'root':xyz,'triangles':24,'sourceTexture':str(flow),'sourceReference':'Figma 378:49','scope':'Decorative stream along existing cliff face outside the driving envelope'},indent=2));print('CASCADE_EXPORTED',xyz)
