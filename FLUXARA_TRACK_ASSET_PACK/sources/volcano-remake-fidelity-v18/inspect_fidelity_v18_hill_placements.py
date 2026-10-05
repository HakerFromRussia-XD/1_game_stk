from pathlib import Path
import sys,math,json,random,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v18';w.mkdir(exist_ok=True);c=r/'fidelity-v17/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
code=(r/'build_fidelity_v12_greenery.py').read_text();exec(code[code.index('def bary'):code.index('folder=Path')]);d=parse(c/'volcano_track.spm');triangles=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)];greens=[b for b in d['buffers']if d['materials'][b['material']][0]=='vr_moss_palette.jpg'];flat=[]
for b in greens:
 for p in triangles(b):
  u=sub(p[1],p[0]);v=sub(p[2],p[0]);n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);l=math.sqrt(dot(n,n))
  if l and abs(n[1])/l>.75:flat.append((p,l/2))
cell=40;terrain_grid=collections.defaultdict(list)
for p,area in flat:
 for gx in range(math.floor(min(v[0]for v in p)/cell),math.floor(max(v[0]for v in p)/cell)+1):
  for gz in range(math.floor(min(v[2]for v in p)/cell),math.floor(max(v[2]for v in p)/cell)+1):terrain_grid[(gx,gz)].append((p,area))
def height(x,z,y):
 vals=[]
 for p,area in terrain_grid[(math.floor(x/cell),math.floor(z/cell))]:
  ww=bary(x,z,p)
  if ww and min(ww)>=-1e-5:
   h=sum(ww[k]*p[k][1]for k in range(3));vals.append(h)
 if vals:return min(vals,key=lambda h:abs(h-y))
protected=[t for b in d['buffers']if d['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png']for t in triangles(b)];scene=E.parse(c/'scene.xml').getroot()
for e in scene.findall('object'):
 if e.get('driveable')=='true'and e.get('model')and e.get('hpr')=='0.0 -0.0 0.0':
  xyz=list(map(float,e.get('xyz').split()));sc=list(map(float,e.get('scale').split()))
  for b in parse(c/e.get('model'))['buffers']:protected +=[[tuple(v[k]*sc[k]+xyz[k]for k in range(3))for v in t]for t in triangles(b)]
boxes=[([min(v[k]for v in p)for k in range(3)],[max(v[k]for v in p)for k in range(3)],p)for p in protected]
def closest(q):
 scores=sorted((sum(max(a[k]-q[k],q[k]-z[k],0)**2 for k in range(3)),i)for i,(a,z,t)in enumerate(boxes));best=1e20
 for low,i in scores:
  if low>=best*best:break
  best=min(best,point_triangle_distance(q,boxes[i][2]))
 return best
lib=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_grassy_hill_v2');hd=parse(lib/'fluxara_driftlib_grassy_hill_v2_main.spm');hv=[v['position']for b in hd['buffers']for v in b['vertices']];rng=random.Random(18026);reject=collections.Counter();proposals=[]
for i in range(6000):
 p,area=rng.choices(flat,weights=[area for p,area in flat],k=1)[0];aa,bb=rng.random(),rng.random()
 if aa+bb>1:aa,bb=1-aa,1-bb
 x,y,z=[aa*p[0][k]+bb*p[1][k]+(1-aa-bb)*p[2][k]for k in range(3)];sx=rng.uniform(4,24);sz=rng.uniform(4,22);sy=rng.uniform(3,10);yaw=rng.uniform(-180,180);theta=math.radians(yaw)
 u=sub(p[1],p[0]);v=sub(p[2],p[0]);nn=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
 if nn[1]<0:nn=[-q for q in nn]
 length=math.sqrt(dot(nn,nn));nn=[q/length for q in nn];ll=math.sqrt(dot(u,u));uu=[q/ll for q in u];vv=[uu[1]*nn[2]-uu[2]*nn[1],uu[2]*nn[0]-uu[0]*nn[2],uu[0]*nn[1]-uu[1]*nn[0]];uu0=uu;vv0=vv;uu=[uu0[k]*math.cos(theta)-vv0[k]*math.sin(theta)for k in range(3)];vv=[uu0[k]*math.sin(theta)+vv0[k]*math.cos(theta)for k in range(3)];sample=[];differences=[]
 def transformed(vx,vy,vz):return [uu[k]*vx*sx+nn[k]*vy*sy+vv[k]*vz*sz for k in range(3)]
 for vx,vy,vz in hv:
  if vy<.0001:
   dx,dy,dz=transformed(vx,vy,vz);h=height(x+dx,z+dz,y+dy);sample.append(h);differences.append(None if h is None else h-(y+dy))
 if any(h is None or abs(h)>sy*.45 for h in differences):reject['footprint_or_slope']+=1;continue
 base=y+min(differences)-.4
 if base+nn[1]*sy<y+2:reject['buried_peak']+=1;continue
 center=[x+nn[0]*sy*.5,base+nn[1]*sy*.5,z+nn[2]*sy*.5];sr=max(math.sqrt((v[0]*sx)**2+((v[1]-.5)*sy)**2+(v[2]*sz)**2)for v in hv);dist=closest(center)
 if dist<sr+3.5 or dist>160:reject['road']+=1;continue
 radius=max(math.hypot(v[0]*sx,v[2]*sz)for v in hv)
 if any(math.hypot(x-float(e.get('xyz').split()[0]),z-float(e.get('xyz').split()[2]))<radius+6 for e in scene.findall('library')if'castle'in e.get('name','')):reject['castle']+=1;continue
 proposals.append({'xyz':[x,base,z],'hpr':[math.degrees(math.atan2(nn[2],vv[2])),math.degrees(math.asin(max(-1,min(1,-uu[2])))),math.degrees(math.atan2(uu[1],uu[0]))],'rotationColumns':[uu,nn,vv],'scale':[sx,sy,sz],'groundFootprintHeights':sample,'footprintMethod':'Every source base vertex transformed with slope-aligned rotation; all base vertices buried at least 0.4m below observed green terrain','groundHeightAtCenter':y,'footprintBaseBuriedMeters':min(differences)-(base-y),'sourceFaceNormal':nn,'horizontalRadius':radius,'boundingSphereCentre':center,'boundingSphereRadius':sr,'minimumProtectedRoadDistance3D':dist,'roadClearanceBeyondBoundingSphere':dist-sr,'score':abs(dist-35)+rng.uniform(0,15)})
selected=[]
for row in sorted(proposals,key=lambda q:q['score']):
 if all(math.hypot(row['xyz'][0]-p['xyz'][0],row['xyz'][2]-p['xyz'][2])>row['horizontalRadius']+p['horizontalRadius']for p in selected):selected.append(row)
 if len(selected)==64:break
out={'proposals':proposals,'selected':selected,'rejectCounts':dict(reject),'flatTriangles':len(flat),'protectedTriangles':len(protected),'sharedModel':str(lib/'fluxara_driftlib_grassy_hill_v2_main.spm'),'sourcePoolObjectId':'lap-v1-5e6c75bde5183e13'};(w/'hill-placement-inspection.json').write_text(json.dumps(out,indent=2));print('V18_HILL_PLACEMENTS_INSPECTED',len(proposals),len(selected),dict(reject),flush=True)
