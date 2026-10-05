from pathlib import Path
import json,math,random,sys,shutil,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v12';w.mkdir(exist_ok=True);old=r/'fidelity-v11/candidate';c=w/'candidate';shutil.copytree(old,c,dirs_exist_ok=True);limit=int(sys.argv[1])if len(sys.argv)>1 else 24
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
m=parse(c/'volcano_track.spm');green=m['buffers'][3];assert m['materials'][green['material']][0]=='vr_moss_palette.jpg';road=[b for b in m['buffers']if m['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','gravel.png']]
def triangles(b):return [[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
protected=[p for b in road for p in triangles(b)];flat=[]
for p in triangles(green):
 u=[p[1][k]-p[0][k]for k in range(3)];v=[p[2][k]-p[0][k]for k in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n))
 if length and abs(n[1])/length>.85:flat.append((p,length/2))
def bary(x,z,p):
 ax,_,az=p[0];bx,_,bz=p[1];cx,_,cz=p[2];det=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz)
 if abs(det)<1e-8:return None
 a=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/det;b=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/det
 return (a,b,1-a-b)
def segdist(x,z,a,b):
 dx,dz=b[0]-a[0],b[2]-a[2];l=dx*dx+dz*dz;t=max(0,min(1,((x-a[0])*dx+(z-a[2])*dz)/l))if l else 0;return math.hypot(x-a[0]-t*dx,z-a[2]-t*dz)
def trdist(x,z,p):
 weights=bary(x,z,p)
 if weights and min(weights)>=0:return 0
 return min(segdist(x,z,p[i],p[(i+1)%3])for i in range(3))
def greenheight(x,z,y):
 for p,_ in flat:
  weights=bary(x,z,p)
  if weights and min(weights)>=-.00001:
   height=sum(weights[k]*p[k][1]for k in range(3))
   if abs(height-y)<1.4:return height
 return None
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def point_triangle_distance(q,t):
 a,b,c=t;ab=sub(b,a);ac=sub(c,a);cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
 if dot(cross,cross)<1e-16:
  distances=[]
  for start,end in [(a,b),(b,c),(c,a)]:
   delta=sub(end,start);length=dot(delta,delta);u=max(0,min(1,dot(sub(q,start),delta)/length))if length else 0;distances.append(math.dist(q,[start[k]+u*delta[k]for k in range(3)]))
  return min(distances)
 ap=sub(q,a);d1,d2=dot(ab,ap),dot(ac,ap)
 if d1<=0 and d2<=0:return math.dist(q,a)
 bp=sub(q,b);d3,d4=dot(ab,bp),dot(ac,bp)
 if d3>=0 and d4<=d3:return math.dist(q,b)
 vc=d1*d4-d3*d2
 if vc<=0 and d1>=0 and d3<=0:
  v=d1/(d1-d3);return math.dist(q,[a[k]+v*ab[k]for k in range(3)])
 cp=sub(q,c);d5,d6=dot(ab,cp),dot(ac,cp)
 if d6>=0 and d5<=d6:return math.dist(q,c)
 vb=d5*d2-d1*d6
 if vb<=0 and d2>=0 and d6<=0:
  v=d2/(d2-d6);return math.dist(q,[a[k]+v*ac[k]for k in range(3)])
 va=d3*d6-d5*d4
 if va<=0 and d4-d3>=0 and d5-d6>=0:
  v=(d4-d3)/((d4-d3)+(d5-d6));return math.dist(q,[b[k]+v*(c[k]-b[k])for k in range(3)])
 total=va+vb+vc
 if abs(total)<1e-12:return min(math.dist(q,p)for p in t)
 v,u=vb/total,vc/total;return math.dist(q,[a[k]+v*ab[k]+u*ac[k]for k in range(3)])
folder=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_round_bush_green_v2');shared=parse(folder/'fluxara_driftlib_round_bush_green_v2_main.spm');shared_vertices=[v['position']for b in shared['buffers']for v in b['vertices']];base_radius=max(math.hypot(v[0],v[2])for v in shared_vertices);base_y=shared['bounds'][1];centre_y=(shared['bounds'][1]+shared['bounds'][4])/2
rng=random.Random(12026);proposals=[];choices=[p for p,area in flat];weights=[area for p,area in flat];reject={'road':0,'footprint':0,'elevation':0};lo=[min(v[k]for p in protected for v in p)for k in range(3)];hi=[max(v[k]for p in protected for v in p)for k in range(3)]
for i in range(9000):
 p=rng.choices(choices,weights=weights,k=1)[0];a,b=rng.random(),rng.random()
 if a+b>1:a,b=1-a,1-b
 point=[a*p[0][k]+b*p[1][k]+(1-a-b)*p[2][k]for k in range(3)];x,y,z=point;scale=rng.uniform(3.2,6.2);sy=rng.uniform(2.8,4.2);radius=base_radius*scale;sphere_radius=max(math.sqrt(scale*scale*(v[0]*v[0]+v[2]*v[2])+sy*sy*(v[1]-centre_y)**2)for v in shared_vertices);centre=[x,y+(centre_y-base_y)*sy-.12,z]
 if math.sqrt(sum(max(lo[k]-centre[k],centre[k]-hi[k],0)**2 for k in range(3)))>75:reject['road']+=1;continue
 distance=min(point_triangle_distance(centre,t)for t in protected)
 if distance<sphere_radius+3.5 or distance>75:reject['road']+=1;continue
 foot=[]
 for k in range(8):
  h=greenheight(x+math.cos(k*math.pi/4)*radius*.7,z+math.sin(k*math.pi/4)*radius*.7,y)
  if h is not None:foot.append(h)
 if len(foot)<5:reject['footprint']+=1;continue
 nearest=min(protected,key=lambda p:trdist(x,z,p));near_y=sum(p[1]for p in nearest)/3
 if not -8<y-near_y<70:reject['elevation']+=1;continue
 proposals.append({'xyz':[x,y-base_y*sy-.12,z],'hpr':[0,rng.uniform(-180,180),0],'scale':[scale,sy,scale],'groundHeight':y,'radius':radius,'boundingSphereRadius':sphere_radius,'boundingSphereCentre':centre,'minimumProtectedRoadDistance3D':distance,'roadClearanceBeyondBoundingSphere':distance-sphere_radius,'groundFootprintSamples':foot,'score':abs(distance-15)+rng.uniform(0,8)})
selected=[]
for row in sorted(proposals,key=lambda q:q['score']):
 if all(math.hypot(row['xyz'][0]-p['xyz'][0],row['xyz'][2]-p['xyz'][2])>row['radius']+p['radius']+1 for p in selected):selected.append(row)
 if len(selected)==limit:break
print('PROPOSAL_DIAGNOSTIC',reject,len(proposals),len(selected),flush=True)
assert len(selected)>=12,('Insufficient suitable crests',len(selected),len(proposals))
scene=E.parse(c/'scene.xml')
for i,row in enumerate(selected):
 row.update({'id':f'VRV12_CrestBush_{i:03}','library':'fluxara_driftlib_round_bush_green_v2','pooledPrototypeId':'volcano-fidelity-v4e-beeb9c6d7ade8d6c','placementKind':'Existing shared bush model; coordinate placement only'})
 E.SubElement(scene.getroot(),'library',id=row['id'],name=row['library'],**{k:' '.join(f'{v:.8f}'for v in row[k])for k in ['xyz','hpr','scale']})
scene.write(c/'scene.xml',encoding='unicode')
def canonical(e):return (e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(ch)for ch in e])
base=E.parse(old/'scene.xml').getroot();new=E.parse(c/'scene.xml').getroot()
for e in list(new):
 if e.get('id','').startswith('VRV12_CrestBush_'):new.remove(e)
assert canonical(base)==canonical(new);assert all(p.read_bytes()==(old/p.name).read_bytes()for p in c.iterdir()if p.is_file()and p.name!='scene.xml')
budget=json.loads((r/'fidelity-v11/budget.json').read_text());budget['candidateTrackBytes']=sum(p.stat().st_size for p in c.iterdir()if p.is_file());budget['newBytesIncludingNewSharedRuntime']=budget['candidateTrackBytes']+budget['newSharedRuntimeBytes'];budget['savedBytesAgainstPrevious']=budget['previousTrackBytes']-budget['newBytesIncludingNewSharedRuntime'];budget['candidateTriangles']+=len(selected)*180;assert budget['savedBytesAgainstPrevious']>0;budget['newCoordinateBushInstances']=len(selected);budget['newSharedRuntimeFiles']=0;budget['triangleChangePercentAgainstOriginal']=(budget['candidateTriangles']/budget['originalTriangles']-1)*100
(w/'greenery-placements.json').write_text(json.dumps({'placements':selected,'proposalsPassingTerrainAndRoadChecks':len(proposals),'greenTriangleCountWithSlopeBelow32Degrees':len(flat),'protectedTriangleCount':len(protected),'sharedModel':str(folder/'fluxara_driftlib_round_bush_green_v2_main.spm'),'sharedModelSha256':hashlib.sha256((folder/'fluxara_driftlib_round_bush_green_v2_main.spm').read_bytes()).hexdigest(),'allExistingModelAndTextureBytesUnchanged':True,'newMeshTextureFiles':0},indent=2));(w/'budget.json').write_text(json.dumps(budget,indent=2));(w/'preservation.json').write_text(json.dumps({'allRuntimeFilesExceptSceneByteIdenticalToV11':True,'onlyNewDecorativeLibraryPlacementsAdded':len(selected),'existingSceneElementsAndTransformsExactV11':True,'protectedCourseAndGameplayControlsUnchanged':True,'minimumRoadMarginMetres':min(q['roadClearanceBeyondBoundingSphere']for q in selected),'greenTerrainFootprintChecksPassed':True,'roadClearanceMethod':'Minimum 3D distance from enclosing sphere centre to every road and wood triangle, minus enclosing sphere radius. Safety margin at least 3.5 metres.','allModelsWithTexturesWeightChangePercent':0,'productionIntegrated':False},indent=2));print('V12_SHARED_GREENERY_READY',len(selected),len(proposals),budget['newBytesIncludingNewSharedRuntime'],flush=True)
