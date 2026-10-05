import bpy,json,sys,random,math,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
f=r/'candidate/fluxara-canyon';src=r/'before/fluxara-canyon';d=parse(src/'fluxara_canyon_decor.spm');img=bpy.data.images.load(str(src/'fluxara_canyon_atlas.png'));pixels=list(img.pixels);w,h=img.size;vs=[];faces=[]
def normaly(n):
 a=(n>>10)&1023;return (a-1024 if a>511 else a)/511
for b in d['buffers']:
 if d['materials'][b['material']][0]!='fluxara_canyon_atlas.png':continue
 for t in range(0,len(b['indices']),3):
  tri=[b['vertices'][i] for i in b['indices'][t:t+3]]
  if sum(normaly(v.get('normal',0)) for v in tri)/3<.6:continue
  uv=tri[0].get('uv')
  if not uv:continue
  # Image pixels in Blender are bottom-origin; SPM exporter flips UV V.
  i=(max(0,min(h-1,int((1-uv[1])*h)))*w+max(0,min(w-1,int(uv[0]*w))))*4;rr,g,bb,aa=pixels[i:i+4]
  if not (g>rr*1.08 and g>bb*1.04 and aa>.95):continue
  start=len(vs);vs.extend((v['position'][0],v['position'][2],v['position'][1]) for v in tri);faces.append((start,start+2,start+1))
assert faces;ground=BVHTree.FromPolygons(vs,faces,all_triangles=True)
quads=[]
for e in E.parse(src/'quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  v=e.get('p'+str(k));q.append(quads[int(v.split(':')[0])][int(v.split(':')[1])] if ':' in v else tuple(map(float,v.split())))
 quads.append(q)
def inside(x,z,q):
 signs=[]
 for i in range(4):
  a,b=q[i],q[(i+1)%4];signs.append((b[0]-a[0])*(z-a[2])-(b[2]-a[2])*(x-a[0]))
 return min(signs)>=0 or max(signs)<=0
rng=random.Random(1041);rows=[];footprints=[]
for qi in range(3,len(quads)-3,4):
 q=quads[qi];center=Vector((sum(p[0] for p in q)/4,sum(p[2] for p in q)/4,sum(p[1] for p in q)/4));a=Vector(((q[0][0]+q[1][0])/2,(q[0][2]+q[1][2])/2,0));b=Vector(((q[2][0]+q[3][0])/2,(q[2][2]+q[3][2])/2,0));direction=(b-a).normalized();side=Vector((-direction.y,direction.x,0))
 for sg in [-1,1]:
  for off in [9,12,16,20,26,34,44,60]:
   point=center+side*sg*off;radius=1.1;samples=[]
   for j in range(13):
    ang=2*math.pi*(j-1)/12;v=point+Vector((0,0,0)) if j==0 else point+Vector((radius*math.cos(ang),radius*math.sin(ang),0));hit,n,_,_=ground.ray_cast(Vector((v.x,v.y,center.z+28)),Vector((0,0,-1)),34)
    if hit is None or n.z<.4:break
    samples.append(hit.z)
   if len(samples)!=13 or max(samples)-min(samples)>1.2:continue
   y=min(samples)-.05
   if any(math.hypot(point.x-p['xyz'][0],point.y-p['xyz'][2])<3 for p in rows):continue
   if any(inside(point.x+dx,point.y+dz,quad) and min(p[1] for p in quad)-.5<=y<=max(p[1] for p in quad)+3.5 for quad in quads for dx,dz in [(0,0),(radius,0),(-radius,0),(0,radius),(0,-radius)]):continue
   row={'id':'Canyon_SharedEnrichment_'+str(len(rows)).zfill(3),'library':'fluxara_driftlib_round_bush_green_v2','role':'Small green roadside shrub','xyz':[point.x,y,point.y],'hpr':[0,rng.uniform(-180,180),0],'scale':[2.2,1.3,2.2],'quadIndex':qi,'groundHeightRange':[min(samples),max(samples)],'footprintSamples':13,'radius':radius};rows.append(row);break
  if len(rows)>=40:break
 if len(rows)>=40:break
assert len(rows)>=1,len(rows)
x=E.parse(f/'scene.xml');root=x.getroot()
for e in list(root):
 if e.get('id','').startswith('Canyon_SharedEnrichment_'):root.remove(e)
for p in rows:E.SubElement(root,'library',name=p['library'],id=p['id'],xyz=' '.join(f'{v:.8f}' for v in p['xyz']),hpr=' '.join(f'{v:.8f}' for v in p['hpr']),scale=' '.join(f'{v:.8f}' for v in p['scale']))
x.write(f/'scene.xml',encoding='utf-8',xml_declaration=True);(r/'canyon-enrichment.json').write_text(json.dumps({'greenSupportTriangles':len(faces),'newCoordinateInstances':len(rows),'newRuntimeMeshBytes':0,'newTextureBytes':0,'placements':rows,'scope':'Thirteen footprint samples on original green upward-facing surfaces; not continuous collision proof'},indent=2));print('CANYON_ENRICHMENT_READY',len(rows),len(faces),flush=True)
