from pathlib import Path
import copy,hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v36';c=w/'candidate';assert not (w/'plant-grounding.json').exists();res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot()
def triangles(buf):return [[buf['vertices'][i]['position']for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)]
def world(v,p,s,y):
 co,si=math.cos(y),math.sin(y);return (p[0]+co*v[0]*s[0]+si*v[2]*s[2],p[1]+v[1]*s[1],p[2]-si*v[0]*s[0]+co*v[2]*s[2])
def params(e):
 p=list(map(float,e.get('xyz').split()));s=list(map(float,e.get('scale').split()));h=list(map(float,e.get('hpr').split()));assert h[0]==h[2]==0;return p,s,math.radians(h[1])
def bounds(tt):return [min(v[k]for v in tt)for k in range(3)]+[max(v[k]for v in tt)for k in range(3)]
def boxdist(a,b):return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
main=parse(c/'volcano_track.spm');road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in root.findall('object'):
 if e.get('driveable')=='true'and e.get('model'):
  p,s,y=params(e);road +=[[world(v,p,s,y)for v in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
assert len(road)==2032;boxes=[bounds(t)for t in road]
def sphere_margin(center,radius):
 best=1e9;box=list(center)*2
 for t,b in zip(road,boxes):
  if boxdist(box,b)<best:best=min(best,point_triangle_distance(center,t))
 return best-radius
def load(lib):
 node=E.parse(res/'library'/lib/'node.xml').getroot().find('object');assert node.get('interaction')=='ghost'and node.get('xyz')=='0 0 0'and node.get('scale')=='1 1 1';return parse(res/'library'/lib/node.get('model'))
gd=load('fluxara_driftlib_volcano_grass_cap_v32');local=triangles(gd['buffers'][0]);surfaces=[]
for e in root.findall('library'):
 if e.get('name')=='fluxara_driftlib_volcano_grass_cap_v32':
  p,s,y=params(e);tt=[[world(v,p,s,y)for v in t]for t in local];surfaces.append({'id':e.get('id'),'p':p,'s':s,'y':y,'triangles':tt,'boxes':[bounds(t)for t in tt]})
assert len(surfaces)==82
def heights(surface,x,z):
 vals=[]
 for t,b in zip(surface['triangles'],surface['boxes']):
  if not(b[0]-1e-7<=x<=b[3]+1e-7 and b[2]-1e-7<=z<=b[5]+1e-7):continue
  a,bb,d=t;den=(bb[2]-d[2])*(a[0]-d[0])+(d[0]-bb[0])*(a[2]-d[2])
  if abs(den)<1e-12:continue
  u=((bb[2]-d[2])*(x-d[0])+(d[0]-bb[0])*(z-d[2]))/den;v=((d[2]-a[2])*(x-d[0])+(a[0]-d[0])*(z-d[2]))/den
  if min(u,v,1-u-v)>=-1e-7:vals.append(u*a[1]+v*bb[1]+(1-u-v)*d[1])
 return max(vals)if vals else None
rows=[];occupied=[]
for role,lib,count in [('Bush','fluxara_driftlib_round_bush_green_v2',104),('Mound','fluxara_driftlib_volcano_green_mound_v18',32)]:
 model=load(lib);points=[v['position']for b in model['buffers']for v in b['vertices']];center=[(model['bounds'][k]+model['bounds'][k+3])/2 for k in range(3)];elements=[e for e in root.findall('library')if e.get('name')==lib];assert len(elements)==count
 for e in elements:
  old=copy.deepcopy(e.attrib)
  if role=='Mound':e.set('hpr','0 '+e.get('hpr').split()[1]+' 0')
  op,os,oy=params(e);best=None
  candidates=sorted(surfaces,key=lambda g:math.hypot(g['p'][0]-op[0],g['p'][2]-op[2])+.4*abs(g['p'][1]+.75*g['s'][1]-op[1]))
  for surface in candidates:
   p,s,y=surface['p'],surface['s'],surface['y']
   size=max(3.5,min(5.5,os[0]*.7))if role=='Bush'else max(2.5,min(4.5,min(s[0],s[2])*1.2))
   scale=[size,size,size]if role=='Bush'else[size,4.5,size];radiusXZ=max(math.hypot(v[0]*scale[0],v[2]*scale[2])for v in points)
   positions=[(op[0],op[2])]+[(q[0],q[2])for q in [world((a,0,b),p,s,y)for a,b in [(0,0),(.7,0),(-.7,0),(0,.6),(0,-.6),(.5,.5),(-.5,-.5)]]]
   for x,z in positions:
    if any(math.hypot(x-q[0],z-q[2])<.55*(radiusXZ+q[3])for q in occupied):continue
    hs=[heights(surface,x,z)]+[heights(surface,x+radiusXZ*math.cos(a),z+radiusXZ*math.sin(a))for a in [2*math.pi*k/8 for k in range(8)]]
    if any(h is None for h in hs):continue
    py=hs[0]-model['bounds'][1]*scale[1]-.15 if role=='Bush'else min(hs)-.10
    pos=[x,py,z];wc=world(center,pos,scale,oy);radius=max(math.dist(world(v,pos,scale,oy),wc)for v in points);margin=sphere_margin(wc,radius)
    if margin<=.15:continue
    score=math.hypot(x-op[0],z-op[2])+.5*abs(py-op[1]);item=(score,pos,scale,surface['id'],hs,margin,wc,radius,radiusXZ)
    if best is None or score<best[0]:best=item
   if best is not None and math.hypot(p[0]-op[0],p[2]-op[2])>best[0]+12:break
  assert best is not None,(role,e.attrib)
  score,pos,scale,ground,hs,margin,wc,radius,rx=best;e.set('xyz',' '.join(f'{v:.8f}'for v in pos));e.set('scale',' '.join(f'{v:.8f}'for v in scale));occupied.append([pos[0],pos[1],pos[2],rx]);rows.append({'role':role,'before':old,'after':dict(e.attrib),'supportingGrassPlacementId':ground,'sampledTopHeights':hs,'boundingSphereCenter':wc,'boundingSphereRadius':radius,'boundingSphereRoadMarginMeters':margin,'grounding':'Bush base0.15m buried at actual center triangle; full crown XZ footprint samples inside same supported cap.'if role=='Bush'else 'Mound base0.10m below lowest cap height across center and8rim samples; original source model reused.'});print('V36_PLANT_GROUNDED',role,e.get('id'),margin,flush=True)
tree.write(c/'scene.xml',encoding='unicode');proof={'bushes':104,'mounds':32,'placements':rows,'sourceSPMGeometryTexturesUnchanged':True,'supportedGrassInstances':82,'protectedRoadTriangles':len(road),'minimumBoundingSphereRoadMarginMeters':min(q['boundingSphereRoadMarginMeters']for q in rows),'newMeshTextureBytes':0,'newAddedDecorativeInstanceTransforms':True,'originalSourceDonorsUnchanged':True,'stage':'Grounding/source sphere safety check; independent verification and native/runtime separate.'};(w/'plant-grounding.json').write_text(json.dumps(proof,indent=2));print('V36_ALL_PLANTS_GROUNDED',len(rows),proof['minimumBoundingSphereRoadMarginMeters'],flush=True)
