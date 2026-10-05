from pathlib import Path
from collections import defaultdict
import sys,math,struct,json,hashlib,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';w.mkdir(exist_ok=True);c=w/'candidate';shutil.copytree(r/'fidelity-v9/candidate',c,dirs_exist_ok=True);sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
changes=[]
def key(p):return tuple(round(x,5)for x in p)
def decode(n):return [((n>>(10*k)&1023)-1024 if(n>>(10*k)&1023)>511 else(n>>(10*k)&1023))/511 for k in range(3)]
def packed(n):
 length=math.sqrt(sum(x*x for x in n));return sum((round(x/length*511)&1023)<<(10*k)for k,x in enumerate(n))|(1<<30)
for name in ['volcano_track.spm','vulcan_01.spm','vulcan_02.spm','vulcan_03.spm']:
 d=parse(c/name);rows=[]
 for index,b in enumerate(d['buffers']):
  if d['materials'][b['material']][0]!='Rock13_col.jpg':continue
  sums=defaultdict(lambda:[0.,0.,0.])
  for t in range(0,len(b['indices']),3):
   ids=b['indices'][t:t+3];ps=[b['vertices'][i]['position']for i in ids];a=[ps[1][k]-ps[0][k]for k in range(3)];z=[ps[2][k]-ps[0][k]for k in range(3)];cross=[a[1]*z[2]-a[2]*z[1],a[2]*z[0]-a[0]*z[2],a[0]*z[1]-a[1]*z[0]]
   if sum(x*x for x in cross)<1e-18:continue
   source=decode(b['vertices'][ids[0]]['normal'])
   if sum(x*y for x,y in zip(cross,source))<0:cross=[-x for x in cross]
   for p in ps:
    dest=sums[key(p)]
    for k in range(3):dest[k]+=cross[k]
  normal_changes=0
  for v in b['vertices']:
   struct.pack_into('<2e',d['raw'],v['uv_offset'],.25,.5);n=sums[key(v['position'])]
   if sum(x*x for x in n)>1e-18:
    value=packed(n);normal_changes+=value!=v['normal'];struct.pack_into('<I',d['raw'],v['normal_offset'],value)
  rows.append({'buffer':index,'vertices':len(b['vertices']),'triangles':len(b['indices'])//3,'changedNormals':normal_changes,'shaderTexture':'vr_moss_palette.jpg','uv': [.25,.5]})
 materials=[['vr_moss_palette.jpg'if n=='Rock13_col.jpg'else n for n in pair]for pair in d['materials']];(c/name).write_bytes(rewrite_texture_names(d,materials));changes.append({'model':name,'buffers':rows,'positionsIndicesColoursAndBoundsRetained':True,'method':'Area-weighted smooth normals across coincident decorative cliff vertices; existing palette stone cell via UVs. No new pixel files.'})
(w/'cliff-changes.json').write_text(json.dumps(changes,indent=2));print('V10_CLIFF_PALETTE_AND_SMOOTH_NORMALS_READY',flush=True)
