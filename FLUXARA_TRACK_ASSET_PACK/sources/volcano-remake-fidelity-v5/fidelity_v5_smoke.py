"""Three actual round cloud chains, without stretching spheres to the whole envelope."""
from pathlib import Path
import bpy,sys,json,shutil,math,random
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';c=w/'candidate';w.mkdir(exist_ok=True)
shutil.copytree(r/'fidelity-v4e/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
proof=[]
for name in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']:
 d=parse(r/'before'/name);old_tri=sum(len(b['indices'])//3 for b in d['buffers']);count=round(old_tri/20)
 lo=Vector((d['bounds'][0],d['bounds'][2],d['bounds'][1]));hi=Vector((d['bounds'][3],d['bounds'][5],d['bounds'][4]));ext=hi-lo;radius=min(ext)*.15
 texture=d['materials'][0][0];rng=random.Random(5333+old_tri);parts=[]
 for j in range(count):
  t=j/max(1,count-1);rad=radius if j in [0,count-1] else radius*rng.uniform(.80,1.0)
  p=(lo+Vector((radius,)*3)).lerp(hi-Vector((radius,)*3),t)
  if j not in [0,count-1]:
   for k in range(3):p[k]=max(lo[k]+rad,min(hi[k]-rad,p[k]+math.sin(t*math.pi)*rng.uniform(-radius*.75,radius*.75)))
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
  obj=bpy.context.object;obj.name='VRV5_'+Path(name).stem+'_Billow_'+str(j)
  unitlo=[min(v.co[k] for v in obj.data.vertices) for k in range(3)];unithi=[max(v.co[k] for v in obj.data.vertices) for k in range(3)]
  for v in obj.data.vertices:
   v.co=Vector(tuple(p[k]+((v.co[k]-unitlo[k])/(unithi[k]-unitlo[k])*2-1)*rad for k in range(3)))
  parts.append(obj)
 bpy.ops.object.select_all(action='DESELECT')
 for obj in parts:obj.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='VRV5_'+Path(name).stem;obj.location=(0,0,0)
 material=bpy.data.materials.get('VRV5_'+texture) or bpy.data.materials.new('VRV5_'+texture);material.use_nodes=True
 if not any(n.type=='TEX_IMAGE' for n in material.node_tree.nodes):
  image=material.node_tree.nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(c/texture));material.node_tree.links.new(image.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
 obj.data.materials.append(material);obj.data.uv_layers.new(name='UVMap')
 for polygon in obj.data.polygons:
  polygon.use_smooth=True
  for loop in polygon.loop_indices:
   vertex=obj.data.vertices[obj.data.loops[loop].vertex_index];obj.data.uv_layers['UVMap'].data[loop].uv=(.75 if vertex.co.z<(lo.z+hi.z)*.5 else .25,.5)
 bpy.ops.screen.spm_export(filepath=str(c/name),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=False,export_tangent=False)
 final=parse(c/name);error=max(abs(a-b)for a,b in zip(d['bounds'],final['bounds']));new_tri=sum(len(b['indices'])//3 for b in final['buffers'])
 assert error<.0001,(name,error);assert .8*old_tri<=new_tri<=1.2*old_tri
 proof.append({'model':name,'originalTriangles':old_tri,'triangles':new_tri,'billows':count,'boundsMaxError':error,'origin':[0,0,0],'localBoundsCenterPreserved':True,'newForm':'Overlapping near-spherical billows along the old envelope, without global anisotropic stretch','sourceSpm':str(r/'before'/name),'paletteReused':texture,'candidateBytes':(c/name).stat().st_size,'originalBytes':(r/'before'/name).stat().st_size})
 obj.hide_set(True);obj.hide_render=True
 bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(w/'Smoke Billow Sources.blend'))
(w/'smoke-changes.json').write_text(json.dumps(proof,indent=2));print('V5_SPHERICAL_SMOKE_READY',proof,flush=True)
