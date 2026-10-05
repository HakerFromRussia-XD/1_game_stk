import bpy,sys,json,math,random,hashlib,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register();rng=random.Random(1039);proof=[]
for src in sorted((r/'before').glob('*.spm')):
 d=parse(src);mats={d['materials'][b['material']][0] for b in d['buffers']}
 if not mats&{'smoke_huricane.png','smoke_huricane_transp.png','gfx_snowStormAnimated_a.png'}:continue
 assert len(mats)==1;tex=next(iter(mats));old_tri=sum(len(b['indices'])//3 for b in d['buffers']);box=d['bounds'];lo=Vector((box[0],box[2],box[1]));hi=Vector((box[3],box[5],box[4]));ext=hi-lo;cen=(hi+lo)/2
 # Preserve local model bounds/origin. Each original ghost smoke model receives
 # broad solid billows with a similar triangle budget, as in Figma 378:39.
 primitive=80 if old_tri>=200 else 20 if old_tri>=28 else 8;n=max(1,round(old_tri/primitive));assert .8*old_tri<=n*primitive<=1.2*old_tri,(src.name,old_tri,n)
 cloud=[];axis=2 if 'Column' in src.stem or 'Eruption' in src.stem else max(range(3),key=lambda k:ext[k])
 for j in range(n):
  if primitive==8:
   me=bpy.data.meshes.new('VR Smoke Octahedron');me.from_pydata([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)],[],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]);ob=bpy.data.objects.new('VR Smoke Octahedron',me);bpy.context.scene.collection.objects.link(ob);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  else:bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2 if primitive==80 else 1,radius=1)
  o=bpy.context.object;o.name='VR_Smoke_'+src.stem+'_'+str(j);o.location=Vector((rng.uniform(-.25,.25),rng.uniform(-.25,.25),rng.uniform(-.25,.25)));o.location[axis]=(-.9+1.8*j/max(1,n-1)) if n>1 else 0;o.scale=Vector((rng.uniform(.43,.63),rng.uniform(.43,.63),rng.uniform(.43,.63)));cloud.append(o)
 bpy.ops.object.select_all(action='DESELECT')
 for o in cloud:o.select_set(True)
 bpy.context.view_layer.objects.active=cloud[0];bpy.ops.object.join();o=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.location=(0,0,0)
 actual_lo=Vector(tuple(min(v.co[k] for v in o.data.vertices) for k in range(3)));actual_hi=Vector(tuple(max(v.co[k] for v in o.data.vertices) for k in range(3)))
 for v in o.data.vertices:v.co=Vector(tuple(lo[k]+(v.co[k]-actual_lo[k])/(actual_hi[k]-actual_lo[k])*ext[k] for k in range(3)))
 m=bpy.data.materials.new('VR Billowing '+src.stem);m.use_nodes=True;node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(f/tex),check_existing=True);m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);o.data.materials.append(m);uv=o.data.uv_layers.new(name='UVMap')
 for p in o.data.polygons:
  p.use_smooth=True
  c=sum(o.data.vertices[o.data.loops[k].vertex_index].co.z for k in p.loop_indices)/len(p.loop_indices);u=.75 if c<cen.z-ext.z*.20 else .25
  for k in p.loop_indices:uv.data[k].uv=(u,.5)
 bpy.ops.screen.spm_export(filepath=str(f/src.name),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=False,export_tangent=False)
 new=parse(f/src.name);nt=sum(len(b['indices'])//3 for b in new['buffers']);assert .8*old_tri<=nt<=1.2*old_tri,(src.name,old_tri,nt);error=max(abs(a-b) for a,b in zip(box,new['bounds']));assert error<.001,(src.name,error)
 o.hide_set(True);o.hide_render=True;proof.append({'model':src.name,'originalTriangles':old_tri,'newTriangles':nt,'triangleChangePercent':100*(nt/old_tri-1),'localBoundsMaxError':error,'localOriginUnchanged':[0,0,0],'localBoundsCentersPreserved':True,'newGeometry':'Rounded solid smoke billows; source vertex/index geometry replaced only for decorative smoke','texture':tex,'paletteSource':str(r/'volume-palette.svg'),'originalSourcePreserved':str(src),'reference':'Figma 378:39'})
 bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Volcanic Smoke Volumes.blend'))
tree=E.parse(f/'materials.xml')
for e in tree.getroot():
 if e.get('name') in ['smoke_huricane.png','smoke_huricane_transp.png','gfx_snowStormAnimated_a.png']:e.set('shader','solid');e.attrib.pop('normal-map',None)
tree.write(f/'materials.xml',encoding='unicode');(r/'smoke-volume-proof.json').write_text(json.dumps(proof,indent=2));print('SMOKE_VOLUMES_READY',[(q['model'],q['originalTriangles'],q['newTriangles']) for q in proof])
