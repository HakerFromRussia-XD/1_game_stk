from pathlib import Path
import math,random,shutil,struct,sys,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v4d';c=w/'candidate'
shutil.copytree(r/'fidelity-v4c/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
names=['AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm'];rows=[]
for name in names:
 d=parse(r/'before'/name);lo=d['bounds'][:3];hi=d['bounds'][3:];ext=[hi[i]-lo[i] for i in range(3)];center=[(hi[i]+lo[i])/2 for i in range(3)]
 tris=sum(len(b['indices'])//3 for b in d['buffers']);assert tris%4==0
 count=tris//4;axes=sorted(range(3),key=lambda k:ext[k],reverse=True);major,minor,depth=axes
 rng=random.Random(1044+tris);cards=[]
 # Many modest overlapping billows occupy the old effect bounds, rather than
 # stretching one entire atlas over irregular source sheets.
 cols=min(count,max(1,round(math.sqrt(count*ext[major]/max(ext[minor],.001)))))
 rows_count=math.ceil(count/cols)
 for j in range(count):
  col,row=j%cols,j//cols
  pos=[0.,0.,0.];pos[major]=(col+.5)/cols-.5;pos[minor]=(row+.5)/rows_count-.5;pos[depth]=rng.uniform(-.15,.15)
  width=1.45/cols;height=1.45/rows_count
  angle=(j%4)*math.pi/4 if count<=9 else rng.uniform(-.5,.5)
  radial=[0.,0.,0.];radial[minor]=math.cos(angle);radial[depth]=math.sin(angle)
  pts=[]
  for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
   q=pos.copy();q[major]+=a*width/2
   for k in range(3):q[k]+=b*height/2*radial[k]
   pts.append(q)
  cards.append(pts)
 # Keep the local bounding box, center, inherited origin and axes exactly.
 mins=[min(p[k] for q in cards for p in q)for k in range(3)];maxs=[max(p[k]for q in cards for p in q)for k in range(3)]
 vertices=[];indices=[]
 for q in cards:
  pts=[tuple(lo[k]+(p[k]-mins[k])/(maxs[k]-mins[k])*ext[k]for k in range(3))for p in q]
  a,b,z=pts[:3];u=[b[k]-a[k]for k in range(3)];v=[z[k]-a[k]for k in range(3)];n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);length=math.sqrt(sum(x*x for x in n));n=tuple(x/length for x in n)
  pn=sum((round(x*511)&1023)<<(10*k)for k,x in enumerate(n))|(1<<30);off=len(vertices)
  vertices.extend([(p,pn,uv)for p,uv in zip(pts,[(0,1),(1,1),(1,0),(0,0)])]);indices.extend(off+i for i in [0,1,2,0,2,3,2,1,0,3,2,0])
 texture=b'vr_volcanic_smoke.png';raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*d['bounds'])+struct.pack('<H',1)+bytes([len(texture)])+texture+b'\x00'+struct.pack('<HHIIH',1,1,len(vertices),len(indices),0))
 for p,n,uv in vertices:raw+=struct.pack('<3fI',*p,n)+b'\x80'+struct.pack('<2e',*uv)
 raw+=struct.pack('<'+str(len(indices))+('H'if len(vertices)>255 else'B'),*indices);(c/name).write_bytes(raw)
 new=parse(c/name);assert new['bounds']==d['bounds'];assert len(new['buffers'][0]['indices'])//3==tris
 rows.append({'model':name,'cards':count,'triangles':tris,'boundsExactOriginal':True,'origin':[0,0,0],'shape':'Overlapping two-sided smoke billow cards with full-sprite UVs; source geometry replaced only for ghost effects'})
for name in ['volcanic-smoke-source.png','imagegen-prompt.txt']:shutil.copy2(r/'fidelity-v4c'/name,w/name)
(w/'changes.json').write_text(json.dumps({'parent':'V4C','models':rows,'roadAndGameplayDataEqualV3':True,'productionIntegrated':False},indent=2));print('V4D_BILLOW_CARDS_READY',rows)
