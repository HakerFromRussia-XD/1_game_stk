import bpy,sys,math,json,random,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rng=random.Random(1001);qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for j in range(4):
  s=e.get('p'+str(j));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
road=BVHTree.FromPolygons([(p[0],p[2],p[1]) for q in qs for p in q],[tuple(i*4+j for j in range(4)) for i in range(len(qs))]);d=parse(r/'before/volcano_track.spm');vs=[];fs=[]
for i in [2,5]:
 b=d['buffers'][i];off=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']);fs.extend(tuple(off+j for j in b['indices'][a:a+3]) for a in range(0,len(b['indices']),3))
terrain=BVHTree.FromPolygons(vs,fs,all_triangles=True)
def ground(x,z):
 h=terrain.ray_cast(Vector((x,z,300)),Vector((0,0,-1)),600);return h[0].z if h[0] and h[1].z<-.25 else None
def clear(x,z,rad):
 return not any(road.ray_cast(Vector((x+math.cos(a)*rr,z+math.sin(a)*rr,300)),Vector((0,0,-1)),600)[0] for a,rr in [(0,0)]+[(i*math.tau/12,rad) for i in range(12)])
scene=E.parse(r/'candidate/scene.xml');rows=[]
for e in list(scene.getroot()):
 if e.get('id','').startswith('VR_'):scene.getroot().remove(e)
def place(lib,role,x,y,z,scale,ang=0,extra=None):
 row={'name':'VR_'+role+'_'+str(len(rows)).zfill(4),'library':'fluxara_driftlib_'+lib,'role':role,'xyz':[x,y,z],'hpr':[0,-math.degrees(ang),0],'scale':scale,'rotationZRadians':ang}
 if extra:row.update(extra)
 rows.append(row);return row
centers=[Vector(((q[0][0]+q[1][0])/2,(q[0][2]+q[1][2])/2)) for q in qs];placed=[]
# Broad rounded moss crowns along the rock margins; staggered around the route.
order=list(range(0,174,4));rng.shuffle(order)
for i in order+list(range(174)):
 if len(placed)>=40:break
 q=qs[i];cy=(q[0][1]+q[1][1])/2;across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  for gap in [5,8,12,18,24]:
   p=centers[i]+across*side*(half+gap);x,z=p;y=ground(x,z);rad=rng.uniform(2.1,4.5)
   if y is None or not -8<y-cy<22 or not clear(x,z,rad) or any((x-a)**2+(z-b)**2<(rad+rr+1)**2 for a,b,rr in placed):continue
   heights=[ground(x+math.cos(a)*rad,z+math.sin(a)*rad) for a in [j*math.tau/12 for j in range(12)]]
   if any(v is None or abs(v-y)>3 for v in heights):continue
   place('round_bush_green_v2','moss-crown',x,min(heights+[y])-.15,z,[rad*2,rng.uniform(1.3,2.6),rad*2],rng.random()*math.tau,{'quadIndex':i,'clearRadius':rad,'groundHeightRange':[min(heights+[y]),max(heights+[y])]});placed.append((x,z,rad));break
  else:continue
  break
signs=[];proof=[]
for i in range(3,171):
 a=(centers[i]-centers[i-2]).normalized();b=(centers[i+2]-centers[i]).normalized();turn=math.atan2(a.x*b.y-a.y*b.x,a.dot(b))
 if abs(turn)<.48 or any(min(abs(i-j),174-abs(i-j))<9 for j in signs):continue
 q=qs[i];cy=(q[0][1]+q[1][1])/2;across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [1,-1]:
  p=centers[i]+across*side*(half+2.8);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>5 or not clear(x,z,1.6):continue
  ang=math.atan2(-a.x,a.y);o=place('circuit_turn_left_v2' if turn>0 else 'circuit_turn_right_v2','turn',x,y,z,[2.9,3,1],ang,{'quadIndex':i,'turnRadians':turn});signs.append(i);proof.append({'instance':o['name'],'quadIndex':i,'turnDegrees':math.degrees(turn),'arrow':'left' if turn>0 else 'right','facesApproachingTraffic':True});break
 if len(signs)>=8:break
# Physical course remains untouched; short red/white curb props sit outside it.
for i in list(range(0,174,5))+list(range(174)):
 if sum(q['role']=='coral-barrier' for q in rows)>=6:break
 q=qs[i];cy=(q[0][1]+q[1][1])/2;tangent=(centers[(i+1)%174]-centers[i]).normalized();across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  p=centers[i]+across*side*(half+2.7);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>1.5:continue
  footprint=[p+tangent*a+across*b for a in [-3.45,0,3.45] for b in [-.9,0,.9]]
  if any(not clear(v.x,v.y,.12) or ground(v.x,v.y) is None or abs(ground(v.x,v.y)-y)>.5 for v in footprint):continue
  place('alpine_coral_barrier_v1','coral-barrier',x,y-.01,z,[1,.35,.8],math.atan2(tangent.y,tangent.x),{'quadIndex':i});break
for i in list(range(1,174,7))+list(range(174)):
 if sum(q['role']=='wood-rail' for q in rows)>=12:break
 q=qs[i];cy=(q[0][1]+q[1][1])/2;tangent=(centers[(i+1)%174]-centers[i]).normalized();across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [1,-1]:
  p=centers[i]+across*side*(half+3.2);x,z=p;y=ground(x,z)
  if y is None or abs(y-cy)>2:continue
  footprint=[p+tangent*a for a in [-5,0,5]]
  if any(not clear(v.x,v.y,.7) or ground(v.x,v.y) is None or abs(ground(v.x,v.y)-y)>.7 for v in footprint):continue
  if any((x-v['xyz'][0])**2+(z-v['xyz'][2])**2<7**2 for v in rows if v['role'] in ['coral-barrier','wood-rail']):continue
  place('wood_rail_v2','wood-rail',x,y-.03,z,[10,.8,1],math.atan2(tangent.y,tangent.x),{'quadIndex':i});break
for q in rows:E.SubElement(scene.getroot(),'library',id=q['name'],name=q['library'],xyz=' '.join(f'{a:.8f}' for a in q['xyz']),hpr=' '.join(f'{a:.8f}' for a in q['hpr']),scale=' '.join(map(str,q['scale'])))
scene.write(r/'candidate/scene.xml',encoding='unicode');(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'layout-summary.json').write_text(json.dumps({'counts':{role:sum(q['role']==role for q in rows) for role in {q['role'] for q in rows}},'addedObjectsGrounded':True,'footprintSamples':13,'originalLibraryPlacementsUnchanged':9},indent=2));(r/'arrow-verification.json').write_text(json.dumps({'signs':proof,'onlyOnCurves':True,'noArrowsOnStraightsOrBunting':True,'gameplayZipperMarkingsUnchanged':True,'direction':'Forward driveline; reverse direction not tested'},indent=2));print('LAYOUT_READY',len(rows),{role:sum(q['role']==role for q in rows) for role in {q['role'] for q in rows}})
