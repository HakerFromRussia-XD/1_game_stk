from pathlib import Path
import bpy,sys,json,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';mod=pack/'models/volcano-remake-fidelity-v5-alpha';sources=pack/'sources/volcano-remake-fidelity-v5-alpha';native=w/'native'
for p in [mod,sources,native]:p.mkdir(exist_ok=True)
reg=json.loads((r/'fidelity-v4e/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
collection=bpy.data.collections['Volcano Remake Asset Prototypes'];newrows=[]
original_smoke=next(bpy.data.materials[q['name']] for q in reg['materials'] if 'vr_volcanic_smoke.png' in q['textures'])
material=original_smoke.copy();material.name='VRV5A_Smoke'
image=next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE');bsdf=material.node_tree.nodes.get('Principled BSDF')
attribute=material.node_tree.nodes.new('ShaderNodeVertexColor');attribute.layer_name='Color'
multiply=material.node_tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
material.node_tree.links.new(image.outputs['Color'],multiply.inputs[1]);material.node_tree.links.new(attribute.outputs['Color'],multiply.inputs[2]);material.node_tree.links.new(multiply.outputs['Color'],bsdf.inputs['Base Color']);material.node_tree.links.new(image.outputs['Alpha'],bsdf.inputs['Alpha']);material.surface_render_method='DITHERED';material.use_backface_culling=False
reg['materials']=[q for q in reg['materials'] if q['name']!=original_smoke.name]+[{'id':'volcano-fidelity-v5a-material-smoke','name':material.name,'oldName':'V4E smoke material','textures':['vr_volcanic_smoke.png']}]
old_effect_rows=[q for q in reg['objects']if '-effect-'in q['id']];reg['objects']=[q for q in reg['objects']if '-effect-'not in q['id']]

for row in json.loads((w/'tint-changes.json').read_text()):
 name=row['model'];path=w/'candidate'/name;parsed=parse(path);vertices=[];faces=[];face_materials=[];slot_names=[]
 for b in parsed['buffers']:
  texture=parsed['materials'][b['material']][0];matname=material.name
  if matname not in slot_names:slot_names.append(matname)
  offset=len(vertices);vertices.extend(b['vertices']);faces.extend(tuple(offset+i for i in reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3));face_materials.extend([slot_names.index(matname)]*(len(b['indices'])//3))
 mesh=bpy.data.meshes.new('VRV5A_'+Path(name).stem+'_Billows');mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1])for v in vertices],[],faces);mesh.uv_layers.new(name='UVMap');mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
 for matname in slot_names:mesh.materials.append(bpy.data.materials[matname])
 for polygon,mi in zip(mesh.polygons,face_materials):
  polygon.material_index=mi;polygon.use_smooth=True
  for loop in polygon.loop_indices:
   v=vertices[mesh.loops[loop].vertex_index];mesh.uv_layers['UVMap'].data[loop].uv=v['uv'];mesh.color_attributes['Color'].data[loop].color_srgb=tuple(x/255 for x in v['color'])+(1,)
 matched=[]
 for obj in list(bpy.data.objects):
  if obj.type=='MESH' and Path(obj.get('source_model','')).name==name:
   old=obj.data
   for linked in list(bpy.data.objects):
    if linked.type=='MESH' and linked.data==old:linked.data=mesh
   obj['source_model']=str(path);matched.append(obj.name)
 # Unused AshCloudEffect still receives a reusable prototype.
 obj=bpy.data.objects.new('VRV5A_Cloud_'+Path(name).stem,mesh);collection.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']='volcano-fidelity-v5a-cloud-'+Path(name).stem.lower();obj['source_model']=str(path);mesh.calc_loop_triangles();assert len(mesh.loop_triangles)==row['triangles']
 q={'id':obj['asset_id'],'name':obj.name,'sourceModel':str(path),'triangles':len(mesh.loop_triangles),'materials':slot_names,'role':'Transparent smoke: original core geometry restored, other cards reused from V4E; uniform vertex tint and alpha blending.','nativeSourceObjectsUpdated':matched};newrows.append(q);reg['objects'].append(q);shutil.copy2(path,mod/name)
for row in reg['nativeOriginalObjects']:
 if Path(row['model']).name in {q['model']for q in json.loads((w/'tint-changes.json').read_text())}:row['model']=Path(row['model']).name
# Update the three decorative instances and their native motion curves from the new scene.
import xml.etree.ElementTree as E,math
from mathutils import Matrix,Euler
scene=E.parse(w/'candidate/scene.xml').getroot();modified={q['id']for q in json.loads((w/'layout-changes.json').read_text())}
for row in reg['nativeOriginalObjects']:
 old=E.fromstring(row['sourceXml'])
 if old.get('id') not in modified:continue
 xml=next(e for e in scene.findall('object')if e.get('id')==old.get('id'));obj=bpy.data.objects[row['name']]
 xyz=list(map(float,xml.get('xyz').split()));hpr=list(map(float,xml.get('hpr').split()));scale=list(map(float,xml.get('scale').split()));rotation=Euler(tuple(math.radians(-a)for a in[hpr[0],hpr[2],hpr[1]]),'XZY');matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@rotation.to_matrix().to_4x4()@Matrix.Diagonal((scale[0],scale[2],scale[1],1))
 obj.animation_data_clear();obj.rotation_mode='XZY';channels={'LocX':('location',0,1),'LocY':('location',2,1),'LocZ':('location',1,1),'RotX':('rotation_euler',0,-math.pi/180),'RotY':('rotation_euler',2,-math.pi/180),'RotZ':('rotation_euler',1,-math.pi/180),'ScaleX':('scale',0,1),'ScaleY':('scale',2,1),'ScaleZ':('scale',1,1)}
 for curve in xml.findall('curve'):
  if curve.get('channel') not in channels:continue
  attr,axis,factor=channels[curve.get('channel')]
  for point in curve.findall('p'):
   frame,value=map(float,point.get('c').split());getattr(obj,attr)[axis]=value*factor;obj.keyframe_insert(data_path=attr,index=axis,frame=frame)
  fc=next(f for f in obj.animation_data.action.fcurves if f.data_path==attr and f.array_index==axis)
  for keyframe,point in zip(fc.keyframe_points,curve.findall('p')):
   keyframe.interpolation='BEZIER'if curve.get('interpolation')=='bezier'else'LINEAR'
   if keyframe.interpolation=='BEZIER':
    keyframe.handle_left_type='FREE';keyframe.handle_right_type='FREE'
    for key,target in [('h1','handle_left'),('h2','handle_right')]:
     frame,value=map(float,point.get(key,point.get('c')).split());setattr(keyframe,target,(frame,value*factor))
  if curve.get('extend')=='cyclic':fc.modifiers.new('CYCLES')
 obj.matrix_world=matrix;row['matrix']=[list(v)for v in matrix];row['sourceXml']=E.tostring(xml,encoding='unicode');obj['source_xml']=row['sourceXml']
for filename in ['scene.xml','materials.xml']:
 bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
reg['finalBlend']=str(native/'Volcano Remake.blend');reg['visualLibrary']=str(mod/'Volcano Remake Cloud Library.blend');reg['reusedPrototypeIds']=[q['id']for q in reg['objects']if not q['id'].startswith('volcano-fidelity-v5a-')];reg['newPrototypes']=newrows;reg['status']='Candidate V5; production unchanged.'
for row in old_effect_rows:
 obj=bpy.data.objects.get(row['name'])
 if obj:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend']);bpy.data.libraries.write(reg['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows}|{bpy.data.materials[n]for q in newrows for n in q['materials']},fake_user=True)
(w/'asset-registration.json').write_text(json.dumps(reg,indent=2))
print('V5_ALPHA_NATIVE_READY',len(reg['objects']),len(newrows),flush=True)
