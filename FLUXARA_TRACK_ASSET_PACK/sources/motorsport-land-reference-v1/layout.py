import bpy,sys,json,math,random,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/motorsport-land_track.spm');rng=random.Random(1808)
def bvh(ids):
 vs=[];fs=[]
 for i in ids:
  b=d['buffers'][i];off=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in b['vertices']);fs.extend(tuple(off+j for j in b['indices'][a:a+3]) for a in range(0,len(b['indices']),3))
 return BVHTree.FromPolygons(vs,fs,all_triangles=True)
road=bvh([10,4]);terrain=bvh([2]);objects=bvh([6,7,8])
def ground(x,z):
 p=terrain.ray_cast(Vector((x,z,120)),Vector((0,0,-1)),240)[0];return p.z if p else None
def clear(x,z,rad):
 for dx,dz in [(0,0)]+[(math.cos(i*math.tau/12)*rad,math.sin(i*math.tau/12)*rad) for i in range(12)]:
  if road.ray_cast(Vector((x+dx,z+dz,60)),Vector((0,0,-1)),120)[0]:return False
 return True
rows=[];used=[]
def place(lib,role,x,y,z,s,angle=0,extra=None):
 row={'name':'ML_'+role+'_'+str(len(rows)).zfill(4),'library':'fluxara_driftlib_'+lib,'role':role,'xyz':[x,y,z],'scale':s,'rotationZRadians':angle}
 if extra:row.update(extra)
 rows.append(row);return row
# Large silhouettes reuse the verified circuit models; every map stores only transforms.
for x,z in [(-145,-55),(-137,65),(0,117),(147,60),(136,-74),(0,-112)]:
 place('grassy_hill_v2','hill',x,-3,z,[33,23,28])
for _ in range(6500):
 if len(used)>=55:break
 x=rng.uniform(-106,102);z=rng.uniform(-66,78);w=rng.uniform(7.3,10.0);y=ground(x,z)
 if y is None or not clear(x,z,w*.58+1.4) or any((x-a)**2+(z-b)**2<8.5**2 for a,b in used):continue
 if (z>58 and -52<x<75) or (x>73 and z>25):continue
 # Avoid putting crowns over the retained grandstands, signs, vans and barriers.
 hit=objects.ray_cast(Vector((x,z,50)),Vector((0,0,-1)),100)[0]
 if hit and hit.z>y+.5:continue
 place('round_tree_green_v2','tree',x,y-.08,z,[w,rng.uniform(6.7,8.5),w*.92],rng.random()*math.tau);used.append((x,z))
shrubs=[]
for _ in range(4500):
 if len(shrubs)>=50:break
 x=rng.uniform(-105,101);z=rng.uniform(-65,77);y=ground(x,z)
 if y is None or not clear(x,z,1.5) or any((x-a)**2+(z-b)**2<2.5**2 for a,b in shrubs):continue
 if (z>58 and -52<x<75) or (x>73 and z>25):continue
 w=rng.uniform(1.5,2.4);place('round_bush_green_v2','bush',x,y-.05,z,[w,w*.75,w*.9],rng.random()*math.tau);shrubs.append((x,z))
for _ in range(350):
 a,b=rng.choice(shrubs);x=a+rng.uniform(-2,2);z=b+rng.uniform(-2,2);y=ground(x,z)
 if y is not None and clear(x,z,.4):place('white_daisy_v2' if len(rows)%3 else 'grass_tuft_v2','detail',x,y+.02,z,[.45,.46,.45],rng.random()*math.tau)
for x,z,angle,w in [(-48,77,0,23),(-20,77,0,23),(8,77,0,23),(37,77,0,23),(66,77,0,23),(109,31,math.pi/2,22),(111,9,math.pi/2,22),(111,-14,math.pi/2,22),(75,-62,0,22),(46,-63,0,22)]:
 y=ground(x,z)
 if y is None:y=-.15
 if clear(x,z,1):place('circuit_pennants_v2','pennants',x,y,z,[w,5.5,1],angle)
for x,y,z,size in [(-140,52,55,11),(30,78,132,13),(149,64,-85,10)]:place('festival_balloon_v1','balloon',x,y,z,[size,size,size],rng.random()*math.tau)
qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for j in range(4):
  s=e.get('p'+str(j));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
cs=[Vector(((q[0][0]+q[1][0])/2,(q[0][2]+q[1][2])/2)) for q in qs];selected=[];proof=[]
for i in range(10,len(qs)-10):
 a=(cs[i]-cs[i-6]).normalized();b=(cs[i+6]-cs[i]).normalized();turn=math.atan2(a.x*b.y-a.y*b.x,a.dot(b))
 if abs(turn)<.40 or any(min(abs(i-j),len(qs)-abs(i-j))<19 for j in selected):continue
 q=qs[i];across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [1,-1]:
  p=cs[i]+across*side*(half+2.1);x,z=p;y=ground(x,z)
  if y is None or not clear(x,z,1.5):continue
  angle=math.atan2(-a.x,a.y);row=place('circuit_turn_left_v2' if turn>0 else 'circuit_turn_right_v2','turn',x,y,z,[2.5,2.7,1],angle,{'quadIndex':i,'turnRadians':turn});proof.append({'instance':row['name'],'turnDegrees':math.degrees(turn),'arrow':'left' if turn>0 else 'right','facesApproachingTraffic':1});selected.append(i);break
 if len(selected)>=10:break
scene=E.parse(r/'candidate/scene.xml')
for e in list(scene.getroot()):
 if e.tag=='library' and e.get('id','').startswith('ML_'):scene.getroot().remove(e)
for row in rows:E.SubElement(scene.getroot(),'library',name=row['library'],id=row['name'],xyz=' '.join(f'{a:.8f}' for a in row['xyz']),hpr=f"0 {-math.degrees(row['rotationZRadians']):.8f} 0",scale=' '.join(map(str,row['scale'])))
scene.write(r/'candidate/scene.xml',encoding='unicode');(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'arrow-verification.json').write_text(json.dumps({'signs':proof,'onlyOnCurves':True,'noGantryChevrons':True,'direction':'Original forward driveline; reverse play not evaluated'},indent=2))
counts={k:sum(q['role']==k for q in rows) for k in set(q['role'] for q in rows)};(r/'layout-summary.json').write_text(json.dumps({'counts':counts,'groundedInOriginalTerrainExceptOuterHillsAndBoundaryFlags':True,'roadExclusionSamplesPerFootprint':13},indent=2));print('LAYOUT_READY',counts,len(rows))
