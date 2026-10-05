from pathlib import Path
import sys,struct,json
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rows=json.loads((w/'smoke-changes.json').read_text())
for row in rows:
 p=w/'candidate'/row['model'];d=parse(p);assert len(d['buffers'])==1;b=d['buffers'][0];out=[];mapping={};indices=[]
 for i in b['indices']:
  v=b['vertices'][i];key=(v['position'],v['uv'])
  if key not in mapping:mapping[key]=len(out);out.append(v)
  indices.append(mapping[key])
 texture=d['materials'][0][0].encode();raw=bytearray(b'SP'+bytes([10,1])+struct.pack('<6f',*d['bounds'])+struct.pack('<H',1)+bytes([len(texture)])+texture+b'\0'+struct.pack('<HHIIH',1,1,len(out),len(indices),0))
 for v in out:raw+=struct.pack('<3fI2e',*v['position'],v['normal'],*v['uv'])
 raw+=struct.pack('<'+str(len(indices))+'H',*indices);p.write_bytes(raw)
 after=parse(p);assert after['bounds']==d['bounds'];assert len(after['buffers'][0]['indices'])==len(b['indices'])
 for i,j in zip(b['indices'],after['buffers'][0]['indices']):assert b['vertices'][i]['position']==after['buffers'][0]['vertices'][j]['position']
 row.update({'verticesAfterWeld':len(out),'candidateBytes':len(raw),'vertexWeld':'Coincident vertices with identical UVs share one packed normal; indexed positions and triangle order unchanged.','modelByteChangePercent':100*(len(raw)/row['originalBytes']-1)})
 assert .8*row['originalBytes']<=len(raw)<=1.2*row['originalBytes']
(w/'smoke-changes.json').write_text(json.dumps(rows,indent=2));print('V5_SMOKE_WELDED',rows)
