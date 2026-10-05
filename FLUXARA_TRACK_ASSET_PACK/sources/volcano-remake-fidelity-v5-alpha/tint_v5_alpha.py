from pathlib import Path
import struct,sys,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
names=['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm','AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm'];rows=[]
for name in names:
 p=w/'candidate'/name;d=parse(p);assert d['version']==10 and d['flags']in[1,3]
 raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*d['bounds'])+struct.pack('<H',len(d['materials'])))
 for pair in d['materials']:
  for item in pair:
   value=item.encode();raw+=bytes([len(value)])+value
 raw+=struct.pack('<HH',1,len(d['buffers']))
 for b in d['buffers']:
  raw+=struct.pack('<IIH',len(b['vertices']),len(b['indices']),b['material'])
  for v in b['vertices']:
   raw+=struct.pack('<3fI',*v['position'],v['normal'])+b'\xff'+bytes((145,119,159))+struct.pack('<2e',*v['uv'])
  raw+=struct.pack('<'+str(len(b['indices']))+('H'if len(b['vertices'])>255 else'B'),*b['indices'])
 p.write_bytes(raw);a=parse(p);assert a['bounds']==d['bounds']
 for old,new in zip(d['buffers'],a['buffers']):
  assert old['indices']==new['indices'];assert all(all(v[k]==u[k]for k in['position','normal','uv'])for v,u in zip(old['vertices'],new['vertices']))
 rows.append({'model':name,'vertexColourRgb':[145,119,159],'triangles':sum(len(b['indices'])//3 for b in a['buffers']),'positionsNormalsUvsIndicesBoundsUnchangedBeforeTint':True,'originalMeshBytes':(r/'before'/name).stat().st_size,'candidateMeshBytes':p.stat().st_size})
(w/'tint-changes.json').write_text(json.dumps(rows,indent=2));print('V5_ALPHA_TINT_READY',rows)
