from pathlib import Path
import copy,hashlib,json,math,shutil,struct,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v38';rej=w/'rejected-skirt-normal-diagnostic';assert not rej.exists();rej.mkdir();sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
pre=json.loads((w/'shape-sky-preflight.json').read_text());path=Path(pre['newGrassModel']['path']);shutil.copy2(path,rej/path.name)
for name in ['shape-sky-preflight.json','preservation-verification.json','drive-capture.json','probe-stdout.log','probe-stderr.log','drive-stdout.log','drive-stderr.log']:shutil.copy2(w/name,rej/name)
shutil.copytree(w/'screenshots',rej/'screenshots');(rej/'rejection.json').write_text(json.dumps({'reason':'Skirt face winding outward, but copied-normal heuristic flipped side normals toward arbitrary last original vertex. All16new lower normals faced inward. Diagnostic gameplay stopped after80s; no natural finish or acceptance claim. Native process interrupted during cold startup before file edits.','geometryAndStonePixelsUnaffected':True},indent=2));gd=parse(pre['grassSource']['path']);d=parse(path);gb=copy.deepcopy(d['buffers'][0]);oldgb=gd['buffers'][0];s=(r/'build_fidelity_v38.py').read_text();ns={'math':math,'struct':struct};ss=(r/'fidelity_v2.py').read_text();exec(ss[ss.index('def encode_buffer'):ss.index('new_vertices, new_indices')],ns);exec(s[s.index('def encode(d,b):'):s.index('def library(')]);upper=set(pre['grassNormalChanges'])-set(range(149,165));ids=upper|set(range(149,165))
def key(v):return tuple(round(x,6)for x in v['position'])
sums={key(v):[0.,0.,0.]for v in gb['vertices']}
for j in range(0,len(gb['indices']),3):
 ii=gb['indices'][j:j+3];a,b,c=[gb['vertices'][i]['position']for i in ii];ab=[b[k]-a[k]for k in range(3)];ac=[c[k]-a[k]for k in range(3)];n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
 if j<len(oldgb['indices']):
  oldn=[sum(normal(oldgb['vertices'][i])[k]for i in ii)for k in range(3)]
  if sum(n[k]*oldn[k]for k in range(3))<0:n=[-x for x in n]
 for i in ii:
  for k in range(3):sums[key(gb['vertices'][i])][k]+=n[k]
for i in ids:
 n=sums[key(gb['vertices'][i])];length=math.sqrt(sum(x*x for x in n));gb['vertices'][i]['normal']=ns['packed_normal']([x/length for x in n])
raw=encode(d,gb);assert len(raw)==len(d['raw']);path.write_bytes(raw);check=parse(path);radial=[]
for i in range(149,165):
 v=check['buffers'][0]['vertices'][i];n=normal(v);radial.append(v['position'][0]*n[0]+v['position'][2]*n[2]);assert radial[-1]>0
pre['newGrassModel'].update({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()});pre['skirtNormalRepair']={'all16LowerNormalsFaceOutwards':True,'minimumLowerRadialNormalDot':min(radial),'positionsUVColorsIndicesBoundsAndWeightExactInitialV38':True,'rejectedInitialDiagnostic':str(rej)};(w/'shape-sky-preflight.json').write_text(json.dumps(pre,indent=2));print('V38_SKIRT_NORMALS_OUTWARD_VERIFIED',min(radial),flush=True)
