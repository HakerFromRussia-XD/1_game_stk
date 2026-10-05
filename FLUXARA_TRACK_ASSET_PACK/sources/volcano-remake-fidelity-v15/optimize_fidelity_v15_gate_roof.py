from pathlib import Path
import json,math,struct,sys,shutil
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct};exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns);proof=json.loads((w/'castle-atmosphere-changes.json').read_text());path=Path(proof['newGateRoofModel']);backup=w/'iterations/roof-336-triangles';backup.mkdir(parents=True,exist_ok=True);
if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
b={'vertices':[],'indices':[],'material':0};span=21.;depth=11.;nx=10;nz=4
for side in [-1,1]:
 for x in range(nx):
  for z in range(nz):
   x0=-span/2+span*x/nx;x1=-span/2+span*(x+1)/nx;z0=depth*.5*z/nz;z1=depth*.5*(z+1)/nz;base=len(b['vertices']);t=(x+z)%3;color=[(207,64,39),(228,86,48),(192,54,37)][t]
   for px,pz in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]:b['vertices'].append({'position':(px,1.6*(1-pz/(depth*.5))+(.018 if t==1 else 0),side*pz),'color':color})
   b['indices'] +=[base,base+1,base+2,base,base+2,base+3]if side<0 else[base+2,base+1,base,base+3,base+2,base]
nn=[[0.,0.,0.]for v in b['vertices']]
for t in range(len(b['indices'])//3):
 a,z,q=b['indices'][3*t:3*t+3];x=[b['vertices'][z]['position'][k]-b['vertices'][a]['position'][k]for k in range(3)];y=[b['vertices'][q]['position'][k]-b['vertices'][a]['position'][k]for k in range(3)];n=(x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0])
 for i in [a,z,q]:nn[i]=[nn[i][k]+n[k]for k in range(3)]
for v,n in zip(b['vertices'],nn):l=math.sqrt(sum(x*x for x in n));v['normal']=ns['packed_normal'](tuple(x/l for x in n))
old=parse(backup/path.name);raw=old['raw'][:32]+struct.pack('<HH',1,1)+ns['encode_buffer'](b,[['','']]);assert raw[:2]==b'SP';path.write_bytes(raw);assert parse(path)['bounds']==old['bounds']
source=parse(r/'fidelity-v14/candidate/volcano_track.spm');gate=source['buffers'][1];base=ns['encode_buffer'](gate,source['materials']);table=b'vr_arch_stone.png';vv=[v['position']for v in gate['vertices']];sourcebounds=[min(v[k]for v in vv)for k in range(3)]+[max(v[k]for v in vv)for k in range(3)];header=bytearray(source['raw'][:4])+struct.pack('<6f',*sourcebounds)+struct.pack('<H',1)+bytes([len(table)])+table+b'\0'+struct.pack('<HH',1,1);gate=dict(gate,material=0);base=header+ns['encode_buffer'](gate,[[table.decode(),'']]);diagnostic=w/'original-component';diagnostic.mkdir(exist_ok=True);(diagnostic/'original-gateway-component.spm').write_bytes(base);texture=r/'fidelity-v14/candidate/vr_arch_stone.png';before=len(base)+texture.stat().st_size;after=before+len(raw);assert after<=before*1.2,(before,after);proof['newGateRoofOptimization']={'trianglesBefore':336,'trianglesAfter':160,'modelBytesBefore':old['raw'].__len__(),'modelBytesAfter':len(raw),'existingGatewayComponentWithTextureBytes':before,'gatewayWithAddedRoofModelAndSameTextureBytes':after,'changePercent':(after/before-1)*100,'upper20PercentPassed':True,'originalGatewayModelUnmodified':True,'gateRoofBoundsOriginAxesUnchanged':True};(w/'castle-atmosphere-changes.json').write_text(json.dumps(proof,indent=2));builder=r/'build_fidelity_v15_castle_atmosphere.py';builder.write_text(builder.read_text().replace('nx=14;nz=6','nx=10;nz=4'));print('V15_GATE_ROOF_WITHIN_OBJECT_WEIGHT_LIMIT',len(raw),before,(after/before-1)*100)
