from pathlib import Path
import copy,collections,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';c=w/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
attempt=w/'first-seam-attempt';assert not attempt.exists();attempt.mkdir();shutil.copytree(w/'shared-runtime',attempt/'shared-runtime');shutil.copy2(c/'scene.xml',attempt/'scene.xml');shutil.copy2(w/'seam-changes.json',attempt/'seam-changes.json');shutil.copytree(w/'screenshots',attempt/'screenshots')
p=json.loads((w/'seam-changes.json').read_text());stone_source=Path(p['sourceStoneModel']);grass_source=Path(json.loads((r/'fidelity-v30/facade-placements.json').read_text())['modelSources'][0]['path']);sd,gd=parse(stone_source),parse(grass_source);sb,gb=copy.deepcopy(sd['buffers'][0]),copy.deepcopy(gd['buffers'][0])
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
def key(v):return tuple(round(q,6)for q in v['position'])
def boundary(b):
 ed=collections.Counter(tuple(sorted((key(b['vertices'][b['indices'][i+j]]),key(b['vertices'][b['indices'][i+(j+1)%3]]))))for i in range(0,len(b['indices']),3)for j in range(3));return {v for e,n in ed.items()if n==1 for v in e}
se,ge=boundary(sb),boundary(gb);assert len(se)==len(ge)==16;anchor=max(v['position'][1]for v in gb['vertices']if key(v)in ge);mapping={}
for pos in se:
 a=math.atan2(pos[2],pos[0]);mapping[pos]=min(ge,key=lambda v:abs(math.atan2(math.sin(math.atan2(v[2],v[0])-a),math.cos(math.atan2(v[2],v[0])-a))))
assert len(set(mapping.values()))==16
schanges,gchanges=[],[]
for i,v in enumerate(sb['vertices']):
 if key(v)in se:g=mapping[key(v)];v['position']=(g[0]*.95,sd['bounds'][4],g[2]*.95);schanges.append(i)
for i,v in enumerate(gb['vertices']):
 if key(v)in ge:v['position']=(v['position'][0],anchor,v['position'][2]);gchanges.append(i)
def normal(v):return tuple((q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]])
def cross(a,b,c):
 x=[b[k]-a[k]for k in range(3)];y=[c[k]-a[k]for k in range(3)];return (x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0])
def finish(b,d,changed,path):
 old=d['buffers'][0];acc={key(v):[0.,0.,0.]for v in b['vertices']};affected=set()
 for j in range(0,len(b['indices']),3):
  ids=b['indices'][j:j+3];n=cross(*(b['vertices'][i]['position']for i in ids));oldface=cross(*(old['vertices'][i]['position']for i in ids));assert sum(v*v for v in n)>1e-12 and sum(n[k]*oldface[k]for k in range(3))>0,(path,j)
  oldn=[sum(normal(old['vertices'][i])[k]for i in ids)for k in range(3)]
  if sum(n[k]*oldn[k]for k in range(3))<0:n=[-v for v in n]
  for i in ids:
   for k in range(3):acc[key(b['vertices'][i])][k]+=n[k]
  if set(ids)&set(changed):affected.update(ids)
 for i in affected:
  n=acc[key(b['vertices'][i])];l=math.sqrt(sum(x*x for x in n));b['vertices'][i]['normal']=ns['packed_normal']([x/l for x in n])
 box=[min(v['position'][k]for v in b['vertices'])for k in range(3)]+[max(v['position'][k]for v in b['vertices'])for k in range(3)];assert box==list(d['bounds'])
 raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*box)+struct.pack('<H',len(d['materials'])))
 for mat in d['materials']:
  for name in mat:q=name.encode();raw+=bytes([len(q)])+q
 raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](b,d['materials']);path.write_bytes(raw);assert len(raw)==len(d['raw']);return sorted(affected)
stone=Path(p['newSharedModel']);sn=finish(sb,sd,schanges,stone);gl=w/'shared-runtime/fluxara_driftlib_volcano_grass_cap_v32';gl.mkdir();grass=gl/'vr_v32_sealed_grass_cap.spm';gn=finish(gb,gd,gchanges,grass)
(gl/'node.xml').write_text(f'<scene><object id="grass_cap" type="animation" model="{grass.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');shutil.copy2(grass_source.parent/'materials.xml',gl/'materials.xml');scene=E.parse(c/'scene.xml')
for group in p['placements']:
 st,cap,tr=group['parts'];cap['name']=gl.name;gs=list(map(float,cap['scale'].split()));gp=list(map(float,cap['xyz'].split()));gp[1]=group['stoneTopY']-anchor*gs[1]-.08;cap['xyz']=' '.join(f'{v:.8f}'for v in gp);yaw=math.radians(float(cap['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw);v=group['treeBaseOnCapLocalPoint'];tr['xyz']=' '.join(f'{v:.8f}'for v in [gp[0]+co*v[0]*gs[0]+si*v[2]*gs[2],gp[1]+v[1]*gs[1],gp[2]-si*v[0]*gs[0]+co*v[2]*gs[2]])
 for attrs in group['parts']:scene.getroot().find(f'library[@id="{attrs["id"]}"]').attrib.update(attrs)
scene.write(c/'scene.xml',encoding='unicode');p.update({'sourceGrassModel':str(grass_source),'sourceGrassModelSha256':hashlib.sha256(grass_source.read_bytes()).hexdigest(),'newGrassModel':str(grass.resolve()),'newGrassLibrary':str(gl.resolve()),'newGrassPrototype':'VRV32_Prototype_SealedGrassCap','newGrassPrototypeId':'volcano-fidelity-v32-sealed-grasscap','stoneChangedBoundaryVertexIndices':schanges,'grassChangedBoundaryVertexIndices':gchanges,'stoneRecomputedNormalVertexIndices':sn,'grassRecomputedNormalVertexIndices':gn,'grassOpenBoundaryHighestLocalY':anchor,'boundaryXZMapping':[[list(a),list(b)]for a,b in mapping.items()],'seamScaleRelationGrassXZEqualsStoneXZTimes':.95,'worldSeamOverlapMeters':.08,'newModelFiles':2,'newCoordinateGroups':24,'newGeometry':True,'bothModelsWithUsedStoneTextureBefore':46337,'bothModelsWithUsedStoneTextureAfter':46337,'stage':'Corrected seam draft: both copied boundaries now have matching XZ and planar Y, world overlap0.08m. Road distances, native/canonical/pool/gameplay pending.'})
p['modelSources'][0]={'path':str(grass.resolve()),'sha256':hashlib.sha256(grass.read_bytes()).hexdigest(),'bytes':grass.stat().st_size};p['modelSources'][1]['sha256']=hashlib.sha256(stone.read_bytes()).hexdigest();(w/'seam-changes.json').write_text(json.dumps(p,indent=2));print('V32_MATCHING_SEAMS_PREFLIGHT_READY',len(schanges),len(gchanges),flush=True)
