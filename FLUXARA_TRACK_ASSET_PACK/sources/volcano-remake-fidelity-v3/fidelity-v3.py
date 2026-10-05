"""Separate V3 atmosphere draft; immutable V2 checkpoint and production remain intact."""
from pathlib import Path
import copy,hashlib,json,shutil,struct,sys
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
work=r/'fidelity-v3';work.mkdir(exist_ok=True)
source=r/'fidelity-v2/candidate';candidate=work/'candidate'
shutil.copytree(source,candidate,dirs_exist_ok=True)
d=parse(source/'volcano_track.spm');assert d['flags']==3 and d['version']&7==2
raw=bytearray(d['raw']);starts=[b['vertices'][0]['offset']-10 for b in d['buffers']]
rows=[]
for i in reversed(range(len(d['buffers']))):
 b=d['buffers'][i];name=d['materials'][b['material']][0]
 if name not in ['halo.png','sunFlare2.png']:continue
 factor=.12 if name=='halo.png' else .08
 encoded=bytearray(struct.pack('<IIH',len(b['vertices']),len(b['indices']),b['material']))
 for v in b['vertices']:
  encoded+=struct.pack('<3fI',*v['position'],v['normal'])
  color=tuple(round(x*factor) for x in v['color'])
  encoded+=b'\xff'+bytes(color)
  encoded+=struct.pack('<2e',*v['uv'])
 encoded+=struct.pack('<'+str(len(b['indices']))+('H' if len(b['vertices'])>255 else 'B'),*b['indices'])
 end=starts[i+1] if i+1<len(starts) else d['geometry_end']
 raw[starts[i]:end]=encoded
 rows.append({'buffer':i,'texture':name,'vertexColorMultiplier':factor,'triangles':len(b['indices'])//3})
(candidate/'volcano_track.spm').write_bytes(raw)
after=parse(candidate/'volcano_track.spm')
for i,(a,b) in enumerate(zip(d['buffers'],after['buffers'])):
 assert a['indices']==b['indices'] and a['material']==b['material']
 assert len(a['vertices'])==len(b['vertices'])
 for v,w in zip(a['vertices'],b['vertices']):
  for key in ['position','normal','uv','uv2']:
   assert v.get(key)==w.get(key),(i,key)
  if i not in {x['buffer'] for x in rows}:assert v['color']==w['color']
assert d['bounds']==after['bounds']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in source.iterdir():
 if p.name!='volcano_track.spm':assert sha(p)==sha(candidate/p.name)
(work/'preservation.json').write_text(json.dumps({'parent':'fidelity-v2','allGeometryIndicesNormalsUvsAndBoundsEqualParent':True,'allFilesExceptMainEqualParentBeforeSkyConversion':True,'changes':rows,'roadBuffer23Exact':True,'allGameplayXmlExact':True,'productionIntegrated':False},indent=2))
print('V3_FLARE_DRAFT_READY',rows)
