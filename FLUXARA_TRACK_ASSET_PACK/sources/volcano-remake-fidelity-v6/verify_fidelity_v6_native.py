from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v6';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v6/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v6/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v6/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
reg=json.loads((w/'asset-registration.json').read_text());checks=[]
for row in reg['newPrototypes']:
 obj=bpy.data.objects[row['name']];d=parse(row['sourceModel']);b=d['buffers'][0];assert len(obj.data.vertices)==len(b['vertices'])
 assert max(abs(x-y)for v,src in zip(obj.data.vertices,b['vertices'])for x,y in zip(v.co,(src['position'][0],src['position'][2],src['position'][1])))<1e-6
 faces=[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)];assert [tuple(p.vertices)for p in obj.data.polygons]==faces
 assert all(tuple(obj.data.uv_layers['UVMap'].data[loop].uv)==b['vertices'][obj.data.loops[loop].vertex_index]['uv']for loop in range(len(obj.data.loops)))
 assert all(tuple(round(x*255)for x in obj.data.color_attributes['Color'].data[loop].color_srgb[:3])==(145,119,159)for loop in range(len(obj.data.loops)))
 obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==row['triangles'];checks.append({'name':obj.name,'triangles':row['triangles'],'positionsUvsIndicesMatchSpm':True})
p=w/'final-blend-verification.json';a=json.loads(p.read_text());a['newCloudPrototypes']=checks;p.write_text(json.dumps(a,indent=2));print('V6_NATIVE_GEOMETRY_VERIFIED',flush=True)
from mathutils import Matrix,Euler
import math,xml.etree.ElementTree as E
road=parse(w/'candidate/volcano_track.spm');roadbuf=next(b for b in road['buffers']if road['materials'][b['material']][0]=='track01.png');ceiling=max(v['position'][1]for v in roadbuf['vertices'])+3.5
channels={'LocX':('location',0,1),'LocY':('location',2,1),'LocZ':('location',1,1),'RotX':('rotation_euler',0,-math.pi/180),'RotY':('rotation_euler',2,-math.pi/180),'RotZ':('rotation_euler',1,-math.pi/180),'ScaleX':('scale',0,1),'ScaleY':('scale',2,1),'ScaleZ':('scale',1,1)}
effects={q['model']for q in json.loads((r/'fidelity-v5-alpha/tint-changes.json').read_text())};placements=[]
for row in reg['nativeOriginalObjects']:
    xml=E.fromstring(row['sourceXml'])
    if xml.get('model')not in effects:continue
    obj=bpy.data.objects[row['name']];values=dict(zip(['LocX','LocY','LocZ'],map(float,xml.get('xyz').split())));values.update(zip(['RotX','RotY','RotZ'],map(float,xml.get('hpr').split())));values.update(zip(['ScaleX','ScaleY','ScaleZ'],map(float,xml.get('scale').split())))
    lower=values['LocY'];max_scales=[abs(values[k])for k in ['ScaleX','ScaleY','ScaleZ']]
    for cv in xml.findall('curve'):
        channel=cv.get('channel');attr,axis,factor=channels[channel];fc=next(f for f in obj.animation_data.action.fcurves if f.data_path==attr and f.array_index==axis);points=cv.findall('p');assert len(points)==len(fc.keyframe_points)
        controls=[]
        for kp,point in zip(fc.keyframe_points,points):
            frame,value=map(float,point.get('c').split());assert abs(kp.co.x-frame)<.002 and abs(kp.co.y-value*factor)<.002
            assert kp.interpolation=='BEZIER'
            for key,target in [('h1','handle_left'),('h2','handle_right')]:
                frame,value=map(float,point.get(key,point.get('c')).split());handle=getattr(kp,target);assert abs(handle.x-frame)<.002 and abs(handle.y-value*factor)<.002
            controls.extend(float(point.get(key,point.get('c')).split()[1])for key in ['c','h1','h2'])
        assert cv.get('extend')=='cyclic';mods=[m for m in fc.modifiers if m.type=='CYCLES'];assert len(mods)==1 and mods[0].mode_before=='REPEAT'and mods[0].mode_after=='REPEAT'
        first=float(points[0].get('c').split()[0]);last=float(points[-1].get('c').split()[0]);frame=first+(bpy.context.scene.frame_current-first)%(last-first)
        a,b=next((a,b)for a,b in zip(points,points[1:])if float(a.get('c').split()[0])<=frame<=float(b.get('c').split()[0]));ps=[tuple(map(float,a.get('c').split())),tuple(map(float,a.get('h2').split())),tuple(map(float,b.get('h1').split())),tuple(map(float,b.get('c').split()))]
        def bz(t,axis):return sum(ps[i][axis]*[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3][i]for i in range(4))
        lo,hi=0.,1.
        for step in range(60):
            mid=(lo+hi)/2
            if bz(mid,0)<frame:lo=mid
            else:hi=mid
        values[channel]=bz((lo+hi)/2,1)
        if channel=='LocY':lower=min(controls)
        if channel in ['ScaleX','ScaleY','ScaleZ']:max_scales[['ScaleX','ScaleY','ScaleZ'].index(channel)]=max(abs(v)for v in controls)
    rotation=Euler(tuple(math.radians(-values[k])for k in ['RotX','RotZ','RotY']),'XZY');expected=Matrix.Translation((values['LocX'],values['LocZ'],values['LocY']))@rotation.to_matrix().to_4x4()@Matrix.Diagonal((values['ScaleX'],values['ScaleZ'],values['ScaleY'],1));error=max(abs(obj.matrix_world[i][j]-expected[i][j])for i in range(4)for j in range(4));assert error<.002,(xml.get('id'),error)
    if xml.findall('curve'):
        # Per-axis maximum scales and the actual local vertex sphere bound all rotations.
        radius=max(math.sqrt(sum((v.co[k]*max_scales[axis])**2 for k,axis in [(0,0),(1,2),(2,1)]))for v in obj.data.vertices);minimum=lower-radius
    else:minimum=min((expected@v.co).z for v in obj.data.vertices)
    assert minimum>ceiling,(xml.get('id'),minimum,ceiling)
    placements.append({'id':xml.get('id'),'model':xml.get('model'),'nativeFrame':bpy.context.scene.frame_current,'nativePoseMatrixMaxError':error,'allCurveKeysHandlesAndCyclesMatchXml':True,'minimumHeightConservative':minimum,'roadCeilingWithMargin':ceiling,'scope':'Original local mesh; static transformed bounds or Bezier control hull with per-axis scaled bounding sphere for all animated rotations.'})
assert len(placements)==11
data=json.loads((w/'final-blend-verification.json').read_text());data['smokePlacementsAboveRoad']=placements;(w/'final-blend-verification.json').write_text(json.dumps(data,indent=2));print('V6_ALL_SMOKE_PLACEMENTS_VERIFIED',len(placements),flush=True)
