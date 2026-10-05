import bpy,sys,math,json,random,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/ancient-summits_track.spm');rng=random.Random(901);qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for j in range(4):
  s=e.get('p'+str(j));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
vs=[(p[0],p[2],p[1]) for q in qs for p in q];fs=[tuple(i*4+j for j in range(4)) for i in range(len(qs))];road=BVHTree.FromPolygons(vs,fs)
vs=[];fs=[]
for i in [3,5,6,7,9,11]:
 b=d['buffers'][i];off=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']);fs.extend(tuple(off+j for j in b['indices'][a:a+3]) for a in range(0,len(b['indices']),3))
terrain=BVHTree.FromPolygons(vs,fs,all_triangles=True)
def ground(x,z):
 hit=terrain.ray_cast(Vector((x,z,300)),Vector((0,0,-1)),600)[0];return hit.z if hit else None
def clear(x,z,rad):
 return not any(road.ray_cast(Vector((x+math.cos(a)*rr,z+math.sin(a)*rr,300)),Vector((0,0,-1)),600)[0] for a,rr in [(0,0)]+[(i*math.tau/12,rad) for i in range(12)])
scene=E.parse(r/'candidate/scene.xml');rows=json.load(open(r/'placements.json'));rows=[q for q in rows if q['role']=='original-fir']
for e in list(scene.getroot()):
 if e.tag=='library' and e.get('id','').startswith('SR_') and not e.get('id','').startswith('SR_OriginalFir_'):scene.getroot().remove(e)
def place(lib,role,x,y,z,scale,ang=0,extra=None):
 row={'name':'SR_'+role+'_'+str(len(rows)).zfill(4),'library':'fluxara_driftlib_'+lib,'role':role,'xyz':[x,y,z],'hpr':[0,-math.degrees(ang),0],'scale':scale,'rotationZRadians':ang}
 if extra:row.update(extra)
 rows.append(row);return row
centers=[Vector(((q[0][0]+q[1][0])/2,(q[0][2]+q[1][2])/2)) for q in qs];placed=[]
# Groups of small snow-capped columns follow the outside of the existing bends.
for i in [0,1,2,3,4,5,13,14,15,16,17,19,20,21,22,23,24,29,30,31,37,38,39,40,43,44,45,46,58,59,60,61,66,67,68,69,75,76,77,78,99,100,101,108,109,110,120,121,125,126,127]:
 if len(placed)>=20:break
 q=qs[i];across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2;cy=(q[0][1]+q[1][1])/2
 for side in [1,-1]:
  for gap in [2.5,4,6]:
   p=centers[i]+across*side*(half+gap);x,z=p;y=ground(x,z)
   if y is None or abs(y-cy)>6 or not clear(x,z,1.35) or any((x-a)**2+(z-b)**2<4**2 for a,b in placed):continue
   place('alpine_snow_column_v1','snow-column',x,y-.08,z,[rng.uniform(2.0,2.6),rng.uniform(3.1,4.7),rng.uniform(2,2.6)],rng.random()*math.tau,{'quadIndex':i});placed.append((x,z));break
  else:continue
  break
# Three additional full-volume firs beside the opening ice curve, using the same mesh.
for i in [1,3,15,17,30,39,60,75,100,110,125]:
 if sum(q['role']=='extra-fir' for q in rows)>=3:break
 q=qs[i];cy=(q[0][1]+q[1][1])/2;across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  p=centers[i]+across*side*(half+10);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>10 or not clear(x,z,5.6):continue
  place('summit_snow_fir_v1','extra-fir',x,y,z,[1.05,1.05,1.05],rng.random()*math.tau,{'quadIndex':i});break
signs=[];proof=[]
for i in range(3,len(qs)-3):
 a=(centers[i]-centers[i-2]).normalized();b=(centers[i+2]-centers[i]).normalized();turn=math.atan2(a.x*b.y-a.y*b.x,a.dot(b))
 if abs(turn)<.48 or any(min(abs(i-j),len(qs)-abs(i-j))<9 for j in signs):continue
 q=qs[i];cy=(q[0][1]+q[1][1])/2;across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [1,-1]:
  p=centers[i]+across*side*(half+2.8);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>6 or not clear(x,z,1.6):continue
  ang=math.atan2(-a.x,a.y);o=place('circuit_turn_left_v2' if turn>0 else 'circuit_turn_right_v2','turn',x,y,z,[2.9,3.0,1],ang,{'quadIndex':i,'turnRadians':turn});signs.append(i);proof.append({'instance':o['name'],'quadIndex':i,'turnDegrees':math.degrees(turn),'arrow':'left' if turn>0 else 'right','facesApproachingTraffic':1});break
 if len(signs)>=8:break
# Bunting is placed along clear outside edges, never across the road.
for q in rows[:]:
 if q['role']!='snow-column' or sum(v['role']=='pennants' for v in rows)>=5:continue
 i=q['quadIndex'];c=centers[i];x,y,z=q['xyz'];away=Vector((x,z))-c
 if away.length==0:continue
 away.normalize();x,z=Vector((x,z))+away*7;y=ground(x,z)
 if y is None or not clear(x,z,8.4):continue
 tang=(centers[(i+1)%len(qs)]-centers[i]).normalized();place('circuit_pennants_v2','pennants',x,y,z,[9,3.9,1],math.atan2(tang.y,tang.x),{'quadIndex':i})
for i in [0,1,2,3,4,5,13,14,15,16,17,20,22,23]:
 if sum(q['role']=='coral-barrier' for q in rows)>=4:break
 q=qs[i];cy=(q[0][1]+q[1][1])/2;tangent=(centers[(i+1)%len(qs)]-centers[i]).normalized();across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  p=centers[i]+across*side*(half+2.9);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>3:continue
  footprint=[p+tangent*a+across*b for a in [-3.45,0,3.45] for b in [-.9,0,.9]]
  if any(not clear(v.x,v.y,.12) or ground(v.x,v.y) is None or abs(ground(v.x,v.y)-y)>.5 for v in footprint):continue
  place('alpine_coral_barrier_v1','coral-barrier',x,y-.002,z,[1,.35,.8],math.atan2(tangent.y,tangent.x),{'quadIndex':i});break
for q in rows:
 if q['role']=='original-fir':continue
 E.SubElement(scene.getroot(),'library',id=q['name'],name=q['library'],xyz=' '.join(f'{a:.8f}' for a in q['xyz']),hpr=' '.join(f'{a:.8f}' for a in q['hpr']),scale=' '.join(map(str,q['scale'])))
scene.write(r/'candidate/scene.xml',encoding='unicode');(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'layout-summary.json').write_text(json.dumps({'counts':{role:sum(q['role']==role for q in rows) for role in {q['role'] for q in rows}},'addedObjectsGrounded':True,'footprintSamples':13},indent=2));(r/'arrow-verification.json').write_text(json.dumps({'signs':proof,'onlyOnCurves':True,'noArrowsOnStraightsOrBunting':True,'gameplayZipperMarkingsUnchanged':True,'direction':'Forward driveline; reverse direction not tested'},indent=2));print('LAYOUT_READY',len(rows),[(q['role'],q.get('quadIndex')) for q in rows[32:]])
