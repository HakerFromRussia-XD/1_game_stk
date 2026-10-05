from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v6';native=w/'native';native.mkdir(exist_ok=True)
reg=json.loads((r/'fidelity-v5-alpha/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['finalBlend']);bpy.context.preferences.filepaths.save_version=0
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
reg['finalBlend']=str(native/'Volcano Remake.blend');reg['status']='V6 isolated layout candidate; all prototype models/materials/textures reused unchanged from V5 Alpha.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(reg,indent=2));print('V6_NATIVE_READY',len(reg['objects']),flush=True)
