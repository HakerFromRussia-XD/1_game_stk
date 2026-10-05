from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v5-alpha/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v5-alpha/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v5-alpha/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
reg=json.loads((w/'asset-registration.json').read_text());checks=[]
for row in reg['newPrototypes']:
 obj=bpy.data.objects[row['name']];d=parse(row['sourceModel']);b=d['buffers'][0];assert len(obj.data.vertices)==len(b['vertices'])
 assert max(abs(x-y)for v,src in zip(obj.data.vertices,b['vertices'])for x,y in zip(v.co,(src['position'][0],src['position'][2],src['position'][1])))<1e-6
 faces=[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)];assert [tuple(p.vertices)for p in obj.data.polygons]==faces
 assert all(tuple(obj.data.uv_layers['UVMap'].data[loop].uv)==b['vertices'][obj.data.loops[loop].vertex_index]['uv']for loop in range(len(obj.data.loops)))
 assert all(tuple(round(x*255)for x in obj.data.color_attributes['Color'].data[loop].color_srgb[:3])==(145,119,159)for loop in range(len(obj.data.loops)))
 obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==row['triangles'];checks.append({'name':obj.name,'triangles':row['triangles'],'positionsUvsIndicesMatchSpm':True})
p=w/'final-blend-verification.json';a=json.loads(p.read_text());a['newCloudPrototypes']=checks;p.write_text(json.dumps(a,indent=2));print('V5_ALPHA_NATIVE_VERIFIED',flush=True)

from mathutils import Vector
from math import sqrt
import xml.etree.ElementTree as E
scene=E.parse(w/'candidate/scene.xml').getroot();road=parse(w/'candidate/volcano_track.spm');roadbuf=next(b for b in road['buffers']if road['materials'][b['material']][0]=='track01.png');ceiling=max(v['position'][1]for v in roadbuf['vertices'])+3.5;bounds=[]
for row in reg['nativeOriginalObjects']:
 xml=E.fromstring(row['sourceXml'])
 if xml.get('model')not in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']:continue
 obj=bpy.data.objects[row['name']];rest_min=min((obj.matrix_world@v.co).z for v in obj.data.vertices);error=max(abs(obj.matrix_world[i][j]-row['matrix'][i][j])for i in range(4)for j in range(4));assert rest_min>ceiling
 if xml.get('model')!='PyroclasticFlow.spm':assert error<.002
 result={'model':xml.get('model'),'restMinimumHeight':rest_min,'roadClearanceCeiling':ceiling,'nativeStaticRestPoseMatchesXml':xml.get('model')!='PyroclasticFlow.spm'}
 if xml.get('model')=='PyroclasticFlow.spm':
  from mathutils import Matrix,Euler
  import math
  values={'LocX':float(xml.get('xyz').split()[0]),'LocY':float(xml.get('xyz').split()[1]),'LocZ':float(xml.get('xyz').split()[2]),'RotX':float(xml.get('hpr').split()[0]),'RotY':float(xml.get('hpr').split()[1]),'RotZ':float(xml.get('hpr').split()[2]),'ScaleX':float(xml.get('scale').split()[0]),'ScaleY':float(xml.get('scale').split()[1]),'ScaleZ':float(xml.get('scale').split()[2])}
  channels={'LocX':('location',0,1),'LocY':('location',2,1),'LocZ':('location',1,1),'RotX':('rotation_euler',0,-math.pi/180),'RotY':('rotation_euler',2,-math.pi/180),'RotZ':('rotation_euler',1,-math.pi/180),'ScaleX':('scale',0,1),'ScaleY':('scale',2,1),'ScaleZ':('scale',1,1)}
  for cv in xml.findall('curve'):
   channel=cv.get('channel');attr,axis,factor=channels[channel];fc=next(f for f in obj.animation_data.action.fcurves if f.data_path==attr and f.array_index==axis);points=cv.findall('p');assert len(points)==len(fc.keyframe_points)
   for kp,point in zip(fc.keyframe_points,points):
    frame,value=map(float,point.get('c').split());assert abs(kp.co.x-frame)<.002 and abs(kp.co.y-value*factor)<.002
    if cv.get('interpolation')=='bezier':
     for key,target in [('h1','handle_left'),('h2','handle_right')]:
      frame,value=map(float,point.get(key,point.get('c')).split());handle=getattr(kp,target);assert abs(handle.x-frame)<.002 and abs(handle.y-value*factor)<.002
   assert cv.get('extend')=='cyclic' and cv.get('interpolation')=='bezier'
   mods=[m for m in fc.modifiers if m.type=='CYCLES'];assert len(mods)==1 and mods[0].mode_before=='REPEAT' and mods[0].mode_after=='REPEAT'
   assert all(k.interpolation=='BEZIER' for k in fc.keyframe_points)
   first=float(points[0].get('c').split()[0]);last=float(points[-1].get('c').split()[0]);frame=first+(bpy.context.scene.frame_current-first)%(last-first)
   pair=next((a,b)for a,b in zip(points,points[1:])if float(a.get('c').split()[0])<=frame<=float(b.get('c').split()[0]))
   controls=[tuple(map(float,pair[0].get('c').split())),tuple(map(float,pair[0].get('h2').split())),tuple(map(float,pair[1].get('h1').split())),tuple(map(float,pair[1].get('c').split()))]
   def bezier(t,axis):return sum(controls[i][axis]*[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3][i]for i in range(4))
   lo,hi=0.,1.
   for step in range(60):
    mid=(lo+hi)/2
    if bezier(mid,0)<frame:lo=mid
    else:hi=mid
   values[channel]=bezier((lo+hi)/2,1)
  rotation=Euler(tuple(math.radians(-values[k])for k in ['RotX','RotZ','RotY']),'XZY');expected=Matrix.Translation((values['LocX'],values['LocZ'],values['LocY']))@rotation.to_matrix().to_4x4()@Matrix.Diagonal((values['ScaleX'],values['ScaleZ'],values['ScaleY'],1));pose_error=max(abs(obj.matrix_world[i][j]-expected[i][j])for i in range(4)for j in range(4));assert pose_error<.002
  result['nativeCurrentCyclicAnimatedPoseMatchesXmlCurves']=True;result['nativeEvaluatedFrame']=bpy.context.scene.frame_current;result['animatedPoseMaxMatrixError']=pose_error;result['allNativeCurveKeysAndHandlesMatchXml']=True
  radius=max(sqrt(sum(x*x for x in v.co))for v in obj.data.vertices);ys=[float(p.get(k).split()[1])for cv in xml.findall('curve')if cv.get('channel')=='LocY'for p in cv.findall('p')for k in['c','h1','h2']if p.get(k)];scales=[abs(float(p.get(k).split()[1]))for cv in xml.findall('curve')if cv.get('channel')in['ScaleX','ScaleY','ScaleZ']for p in cv.findall('p')for k in['c','h1','h2']if p.get(k)];lower=min(ys)-radius*max(scales);assert lower>ceiling;result['allAnimatedRotationsConservativeMinimumHeight']=lower;result['basis']='Bezier control convex hull and bounding sphere; no road overlap for these three effects.'
 bounds.append(result)
assert len(bounds)==3
result=json.loads((w/'final-blend-verification.json').read_text());result['threeSmokeEffectsAboveRoad']=bounds;(w/'final-blend-verification.json').write_text(json.dumps(result,indent=2));print('V5_ALPHA_ROAD_CLEARANCE_VERIFIED',bounds,flush=True)
