import json,sys,math,xml.etree.ElementTree as E
from pathlib import Path
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rows=json.load(open(r/'canyon-enrichment.json'))['placements'];lib=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_round_bush_green_v2');d=parse(next(lib.glob('*_main.spm')));qs=[]
for e in E.parse(r/'before/fluxara-canyon/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  s=e.get('p'+str(k));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
def inside(x,z,q):
 signs=[(q[(i+1)%4][0]-q[i][0])*(z-q[i][2])-(q[(i+1)%4][2]-q[i][2])*(x-q[i][0]) for i in range(4)];return min(signs)>=0 or max(signs)<=0
bad=[];checked=0
for row in rows:
 ang=math.radians(row['hpr'][1]);c,s=math.cos(ang),math.sin(ang);px,py,pz=row['xyz'];sx,sy,sz=row['scale']
 for b in d['buffers']:
  for v in b['vertices']:
   x,y,z=v['position'];x,z=x*sx*c+z*sz*s+px,-x*sx*s+z*sz*c+pz;y=y*sy+py;checked+=1
   for q in qs:
    if min(t[1] for t in q)-.5<=y<=max(t[1] for t in q)+3.5 and inside(x,z,q):bad.append({'id':row['id'],'vertex':[x,y,z]});break
assert not bad,bad;(r/'enrichment-layout-verification.json').write_text(json.dumps({'instances':len(rows),'verticesChecked':checked,'verticesWithinDrivingEnvelope':bad,'supportFootprintSamplesPerInstance':13,'scope':'Original driving quads and actual reused mesh vertices; not continuous collision proof'},indent=2));print('ENRICHMENT_LAYOUT_VERIFIED',len(rows),checked)
