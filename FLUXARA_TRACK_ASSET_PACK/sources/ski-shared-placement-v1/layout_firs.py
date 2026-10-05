import bpy,sys,json,random,math,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
bpy.ops.wm.open_mainfile(filepath=str(r/'before-native.blend'));bpy.context.view_layer.update();root=E.parse(r/'candidate/scene.xml');old=E.parse(r/'before/scene.xml').getroot();a=json.load(open(r/'ski-extraction.json'));name='fluxara_driftlib_ski_branchless_fir_v12';fir=parse(r/'before/ski-dash-branchless-fir-v12.spm');nv=E.parse(r/'before/navmesh.xml').getroot();vertices=[(float(e.get('x')),float(e.get('y')),float(e.get('z'))) for e in nv.find('vertices')];navfaces=[list(map(int,e.get('indices').split())) for e in nv.find('faces')];polys=[[vertices[i] for i in face] for face in navfaces];navbounds=[([min(q[k] for q in face) for k in range(3)],[max(q[k] for q in face) for k in range(3)]) for face in polys]
existing=[(list(map(float,e.get('xyz').split())),float(e.get('scale').split()[0])) for e in old.findall('object') if e.get('model')=='ski-dash-branchless-fir-v12.spm'];rows=[];rng=random.Random(2052)
for cap in sorted([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('SkiDash_SnowCliff_','SkiDash_EdgeCliff_')) and o.name.endswith('_Cap')],key=lambda o:o.name):
 vs=[cap.matrix_world@v.co for v in cap.data.vertices];cap.data.calc_loop_triangles();faces=[tuple(t.vertices) for t in cap.data.loop_triangles];tree=BVHTree.FromPolygons(vs,faces,all_triangles=True);xmin,xmax=min(p.x for p in vs),max(p.x for p in vs);ymin,ymax=min(p.y for p in vs),max(p.y for p in vs);top=max(p.z for p in vs)+1;added=0
 for attempt in range(220):
  x,y=rng.uniform(xmin,xmax),rng.uniform(ymin,ymax);s=rng.uniform(.4,.57);radius=4.08*s;support=[]
  for j in range(13):
   ang=2*math.pi*(j-1)/12;dx,dy=(0,0) if j==0 else (radius*math.cos(ang),radius*math.sin(ang));hit,n,_,_=tree.ray_cast(Vector((x+dx,y+dy,top)),Vector((0,0,-1)),150)
   if hit is None or abs(n.z)<.45:break
   support.append(hit.z)
  if len(support)!=13 or max(support)-min(support)>1.8:continue
  z=support[0]-.08
  if any(math.hypot(x-p[0],y-p[2])<4.1*(s+es)+.65 and abs(z-p[1])<6 for p,es in existing):continue
  b=fir['bounds'];lo=[x+b[0]*s,z+b[1]*s,y+b[2]*s];hi=[x+b[3]*s,z+b[4]*s,y+b[5]*s]
  if any(lo[0]<=nb[1][0]+.7 and hi[0]>=nb[0][0]-.7 and lo[2]<=nb[1][2]+.7 and hi[2]>=nb[0][2]-.7 and lo[1]<=nb[1][1]+3.5 and hi[1]>=nb[0][1]-.5 for nb in navbounds):continue
  row={'id':'SkiDash_SharedEnrichment_'+str(len(rows)).zfill(3),'library':name,'xyz':[x,z,y],'hpr':[0,0,0],'scale':[s,s,s],'support':cap.name,'footprintSamples':13,'groundHeightRange':[min(support),max(support)],'boundsOutsideExpandedNavmesh':True};rows.append(row);existing.append((row['xyz'],s));added+=1
  if added>=2:break
 if len(rows)>=18:break
assert rows, 'No safe supported placement'
for p in rows:E.SubElement(root.getroot(),'library',name=p['library'],id=p['id'],xyz=' '.join(f'{v:.8f}' for v in p['xyz']),hpr='0 0 0',scale=' '.join(f'{v:.8f}' for v in p['scale']))
root.write(r/'candidate/scene.xml',encoding='utf-8',xml_declaration=True);a['extraCoordinatePlacements']=rows;a['newTreeInstances']=len(rows);a['newGeometryOrTextureBytesForEnrichment']=0;a['newInstanceTriangles']=len(rows)*sum(len(b['indices'])//3 for b in fir['buffers']);a['candidateTrackBytes']=sum(f.stat().st_size for f in (r/'candidate').iterdir() if f.is_file());a['totalCandidateBytes']=a['candidateTrackBytes']+a['allNewSharedBytes'];a['weightNotIncreased']=a['totalCandidateBytes']<=a['sourceBytes'];assert a['weightNotIncreased'];(r/'ski-extraction.json').write_text(json.dumps(a,indent=2));(r/'ski-enrichment.json').write_text(json.dumps({'placements':rows,'newInstances':len(rows),'newMeshBytes':0,'newTextureBytes':0,'navmeshFaces':len(polys),'boundsClearance':.7,'heightClearance':3.5,'scope':'13 footprint ground rays and whole actual mesh AABB outside expanded original navmesh envelopes; runtime view pending'},indent=2));print('SKI_ENRICHMENT_READY',len(rows),a['sourceBytes']-a['totalCandidateBytes'],flush=True)
