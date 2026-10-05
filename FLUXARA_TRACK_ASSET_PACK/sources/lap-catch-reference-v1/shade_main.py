from pathlib import Path
import sys,struct,json,math
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(f/'lap-catch_track.spm');assert d['flags']==1
raw=bytearray(d['raw'][:28]);raw[3]=3;raw+=struct.pack('<H',len(d['materials']))
for pair in d['materials']:
 for name in pair:b=name.encode();raw+=struct.pack('B',len(b))+b
raw+=struct.pack('<HH',1,len(d['buffers']));grass={9,18,19,20,41,45,46,47};rock={0,2,6,10,17,22,32,34,35,37,43,44,52,54,61,65,67};road={2,3,14,17,22,52,53,54,56,62,67,68,70,71};water={28,66,73,74}
for i,b in enumerate(d['buffers']):
 raw+=struct.pack('<IIH',len(b['vertices']),len(b['indices']),b['material'])
 for v in b['vertices']:
  pn=v['normal'];n=[(pn>>(k*10))&1023 for k in range(3)];n=[(q-1024 if q>511 else q)/511 for q in n];light=.78+.22*max(0,-n[0]*.3+n[1]*.87-n[2]*.3)
  tint=[.60,.63,.66] if i in road else [.58,.76,.75] if i in grass else [.76,.64,.68] if i in rock else [.65,.74,.77] if i in water else [.78,.79,.8]
  color=tuple(round(255*light*q) for q in tint);raw+=struct.pack('<3fI',*v['position'],v['normal']);raw+=b'\xff'+bytes(color)
  if d['materials'][b['material']][0]:raw+=struct.pack('<2e',*v['uv'])
  if d['materials'][b['material']][1]:raw+=struct.pack('<2e',*v['uv2'])
 raw+=struct.pack('<'+str(len(b['indices']))+('I' if len(b['vertices'])>65535 else 'H' if len(b['vertices'])>255 else 'B'),*b['indices'])
(f/'lap-catch_track.spm').write_bytes(raw);print('MAIN_SHADED',len(raw))
