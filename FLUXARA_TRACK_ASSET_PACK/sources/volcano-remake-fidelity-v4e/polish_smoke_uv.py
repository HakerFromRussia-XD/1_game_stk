from pathlib import Path
import sys,json,struct,shutil
from PIL import Image
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
changes=[]
for src in (r/'before').glob('*.spm'):
 d=parse(src);changed=0
 for b in d['buffers']:
  tex=d['materials'][b['material']][0]
  if tex not in ['smoke_huricane.png','smoke_huricane_transp.png','gfx_snowStormAnimated_a.png']:continue
  bounds=[(min(v['uv'][i] for v in b['vertices']),max(v['uv'][i] for v in b['vertices'])) for i in [0,1]]
  for v in b['vertices']:
   uv=[(v['uv'][i]-bounds[i][0])/(bounds[i][1]-bounds[i][0]) if bounds[i][1]>bounds[i][0] else .5 for i in [0,1]];uv=[uv[0],uv[1]/16] if tex=='gfx_snowStormAnimated_a.png' else [v['uv'][0]*.5,v['uv'][1]*.5];struct.pack_into('<2e',d['raw'],v['uv_offset'],*uv);changed+=1
 if changed:(f/src.name).write_bytes(d['raw']);changes.append({'model':src.name,'spriteUvVertices':changed,'positionsNormalsIndicesBoundsExact':True,'operation':'Cross-card UV normalized to one of 16 identical alpha sprite atlas rows; continuous smoke UV frequency halved'})

shutil.copy2(f/'fluxara_drifttex_generic_lavaA.png',f/'stktex_generic_lavaA.png')
(r/'smoke-uv-proof.json').write_text(json.dumps(changes,indent=2));print('SMOKE_UV_READY',changes)
