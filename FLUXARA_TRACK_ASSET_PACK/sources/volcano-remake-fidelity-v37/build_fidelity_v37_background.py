from pathlib import Path
import collections,copy,hashlib,json,math,random,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';c=w/'candidate';assert (w/'rim-preflight.json').is_file()and not(w/'background-preflight.json').exists()
# Reuse source/road and triangle-clearance helpers, without rebuilding the already committed rim scene.
s=(r/'build_fidelity_v37_rims.py').read_text();start=s.index('def tris(');end=s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')");res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse;from terrain_triangle_distance import triangle_distance,point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot();exec(s[start:end]);bg=model('fluxara_driftlib_volcano_backdrop_terrain_v23');bgtris=tris(bg);bgbox=[box(t)for t in bgtris]
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns);buf=bg['buffers'][0];groups=ns['component_triangles'](buf);far=[g for g in groups if len(g)in[264,292,349,270,528,392]];assert len(far)==6
def height(tt,boxes,x,z):
 vals=[]
 for t,b in zip(tt,boxes):
  if not(b[0]-1e-7<=x<=b[3]+1e-7 and b[2]-1e-7<=z<=b[5]+1e-7):continue
  a,bb,d=t;den=(bb[2]-d[2])*(a[0]-d[0])+(d[0]-bb[0])*(a[2]-d[2])
  if abs(den)<1e-12:continue
  u=((bb[2]-d[2])*(x-d[0])+(d[0]-bb[0])*(z-d[2]))/den;v=((d[2]-a[2])*(x-d[0])+(a[0]-d[0])*(z-d[2]))/den
  if min(u,v,1-u-v)>=-1e-7:vals.append(u*a[1]+v*bb[1]+(1-u-v)*d[1])
 return max(vals)if vals else None
choices=[t for g in far for j in g for t in [[buf['vertices'][i]['position']for i in buf['indices'][j*3:j*3+3]]]if max(v[1]for v in t)>8]
weights=[max(.01,abs((t[1][0]-t[0][0])*(t[2][2]-t[0][2])-(t[2][0]-t[0][0])*(t[1][2]-t[0][2])))for t in choices];rng=random.Random(3701);rows=[];occup=[];mounds=[];rejected=0
for role,lib,count in [('Mound','fluxara_driftlib_volcano_green_mound_v18',20),('Tree','fluxara_driftlib_round_tree_green_v2',64)]:
 for k in range(count):
  found=None
  for trial in range(5000):
   t=rng.choices(choices,weights=weights,k=1)[0];u,v=rng.random(),rng.random()
   if u+v>1:u,v=1-u,1-v
   x=t[0][0]+u*(t[1][0]-t[0][0])+v*(t[2][0]-t[0][0]);z=t[0][2]+u*(t[1][2]-t[0][2])+v*(t[2][2]-t[0][2]);sy=rng.uniform(6,10)if role=='Mound'else rng.uniform(9,14);sx=rng.uniform(8,14)if role=='Mound'else sy;sz=sx;radiusXZ=sx if role=='Mound'else sy*.6
   if any(math.hypot(x-q[0],z-q[1])<.65*(radiusXZ+q[2])for q in occup):continue
   samples=[height(bgtris,bgbox,x,z)]+[height(bgtris,bgbox,x+radiusXZ*math.cos(a),z+radiusXZ*math.sin(a))for a in [j*math.pi/4 for j in range(8)]]
   if any(h is None for h in samples):continue
   py=min(samples)-.18 if role=='Mound'else samples[0]
   if role=='Tree':
    extra=[height(tt,bb,x,z)for tt,bb in mounds];py=max([py]+[h for h in extra if h is not None])
   attrs={'id':f'VRV37_Background{role}_{k:03d}','name':lib,'xyz':f'{x:.8f} {py:.8f} {z:.8f}','hpr':f'0 {rng.uniform(-180,180):.8f} 0','scale':f'{sx:.8f} {sy:.8f} {sz:.8f}'};valid,pr=certificate(attrs,required=2.)
   if not valid:rejected+=1;continue
   found=(attrs,pr,samples);break
  assert found is not None,(role,k)
  attrs,proof,samples=found;E.SubElement(root,'library',**attrs);occup.append([x,z,radiusXZ]);row={'role':role,'attrs':attrs,'backgroundSampledGroundHeights':samples,'clearanceProof':proof,'grounding':'Base buried0.18m below min9background footprint heights'if role=='Mound'else'Trunk base at highest actual background or newly placed mound triangle at its XZ'};rows.append(row)
  if role=='Mound':
   tt=[[world(v,attrs)for v in t]for t in tris(model(lib))];mounds.append((tt,[box(t)for t in tt]))
  print('V37_BACKGROUND_READY',role,k,flush=True)
tree.write(c/'scene.xml',encoding='unicode');p=json.loads((w/'rim-preflight.json').read_text());base=json.loads((r/'fidelity-v36/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());total=size+base['acceptedSharedHistoryBytes']+base['acceptedSharedTextureHistoryBytes']+base['newSharedRuntimeAllFilesBytes']+base['newSharedGlobalAliasesAllFilesBytes'];assert total<base['allCandidateAndAcceptedHistoryBytes'];proof={'newDecorativeCoordinateInstances':len(rows),'newTrees':64,'newMounds':20,'placements':rows,'sourceModels':sources,'originalFarTerrainGeometryAndAllSourceFilesUnchanged':True,'newMeshTextureMaterialBytes':0,'clearanceLowerBoundMeters':2.,'rejectedRoadCloseCandidates':rejected,'candidateAllFilesBytes':size,'allCandidateAndAcceptedHistoryBytes':total,'savingVsV36Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'v1Bytes':base['integratedV1BaselineBytes'],'productionIntegrated':False,'referenceAcceptance':False};(w/'background-preflight.json').write_text(json.dumps(proof,indent=2));print('V37_BACKGROUND_SOURCE_READY',len(rows),total,flush=True)
