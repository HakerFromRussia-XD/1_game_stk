from pathlib import Path
import copy,collections,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v31/candidate',c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
p=json.loads((r/'fidelity-v31/cap-changes.json').read_text());source=Path(p['modelSources'][1]['path']);d=parse(source);old=d['buffers'][0];b=copy.deepcopy(old)
def key(v):return tuple(round(q,6)for q in v['position'])
def boundary(buf):
 edges=collections.Counter(tuple(sorted((key(buf['vertices'][buf['indices'][i+j]]),key(buf['vertices'][buf['indices'][i+(j+1)%3]]))))for i in range(0,len(buf['indices']),3)for j in range(3));return {v for e,n in edges.items()if n==1 for v in e}
edge=boundary(b);assert len(edge)==16;changed=[]
for i,v in enumerate(b['vertices']):
 if key(v)in edge:
  changed.append(i);v['position']=(v['position'][0],d['bounds'][4],v['position'][2])
def normal(v):return tuple((q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]])
acc={key(v):[0.,0.,0.]for v in b['vertices']};affected=set()
for j in range(0,len(b['indices']),3):
 ids=b['indices'][j:j+3];vv=[b['vertices'][i]for i in ids];a,t,u=[v['position']for v in vv];v=[t[k]-a[k]for k in range(3)];q=[u[k]-a[k]for k in range(3)];n=[v[1]*q[2]-v[2]*q[1],v[2]*q[0]-v[0]*q[2],v[0]*q[1]-v[1]*q[0]];assert math.sqrt(sum(x*x for x in n))>1e-6
 oldn=[sum(normal(old['vertices'][i])[k]for i in ids)for k in range(3)]
 if sum(n[k]*oldn[k]for k in range(3))<0:n=[-x for x in n]
 for vertex in vv:
  for k in range(3):acc[key(vertex)][k]+=n[k]
 if set(ids)&set(changed):affected.update(ids)
for i in affected:
 n=acc[key(b['vertices'][i])];l=math.sqrt(sum(v*v for v in n));b['vertices'][i]['normal']=ns['packed_normal']([v/l for v in n])
box=[min(v['position'][k]for v in b['vertices'])for k in range(3)]+[max(v['position'][k]for v in b['vertices'])for k in range(3)];assert box==list(d['bounds'])
raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*box)+struct.pack('<H',len(d['materials'])))
for mat in d['materials']:
 for name in mat:q=name.encode();raw+=bytes([len(q)])+q
raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](b,d['materials']);assert len(raw)==source.stat().st_size==2533
lib=w/'shared-runtime/fluxara_driftlib_volcano_stone_column_v32';lib.mkdir(parents=True);model=lib/'vr_v32_sealed_stone_column.spm';model.write_bytes(raw);(lib/'node.xml').write_text(f'<scene><object id="stone_column" type="animation" model="{model.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');shutil.copy2(source.parent/'materials.xml',lib/'materials.xml')
grass=parse(p['modelSources'][0]['path']);capBoundary=boundary(grass['buffers'][0]);capAnchor=max(v[1]for v in capBoundary);scene=E.parse(c/'scene.xml');transforms=[]
for group in p['placements']:
 before=copy.deepcopy(group['parts']);stone,cap,tree=group['parts'];stone['name']=lib.name;gs=list(map(float,cap['scale'].split()));gp=list(map(float,cap['xyz'].split()));gp[1]=group['stoneTopY']-capAnchor*gs[1]-.08;cap['xyz']=' '.join(f'{v:.8f}'for v in gp)
 yaw=math.radians(float(cap['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw);v=group['treeBaseOnCapLocalPoint'];tp=(gp[0]+co*v[0]*gs[0]+si*v[2]*gs[2],gp[1]+v[1]*gs[1],gp[2]-si*v[0]*gs[0]+co*v[2]*gs[2]);tree['xyz']=' '.join(f'{v:.8f}'for v in tp)
 for attrs in group['parts']:scene.getroot().find(f'library[@id="{attrs["id"]}"]').attrib.update(attrs)
 transforms.append({'before':before,'after':copy.deepcopy(group['parts']),'capHighestOpenBoundaryY':gp[1]+capAnchor*gs[1],'stoneTopY':group['stoneTopY'],'capBoundaryOverlapMeters':.08})
scene.write(c/'scene.xml',encoding='unicode');p.update({'baseCandidate':'V31 rejected thickness draft','lastVerifiedAcceptedCandidate':'V30','sourceStoneModel':str(source),'sourceStoneModelSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'newSharedModel':str(model.resolve()),'newSharedLibrary':str(lib.resolve()),'newPrototype':'VRV32_Prototype_SealedStoneBody','newPrototypeId':'volcano-fidelity-v32-sealed-stonebody','sourcePoolObjectId':'volcano-fidelity-v29-grounded-stonebody','stoneChangedBoundaryVertexIndices':changed,'stoneRecomputedNormalVertexIndices':sorted(affected),'stoneOpenBoundaryVertices':16,'stoneUpperBoundaryPlanarY':d['bounds'][4],'grassOpenBoundaryHighestLocalY':capAnchor,'changedPlacementGroups':transforms,'newTextureFiles':0,'newMaterials':0,'newModelFiles':1,'newGeometry':True,'sourceLocalBoundsUVRGBIndicesOriginsAxesRetained':True,'modelAndUsedTextureBytesBefore':42471,'modelAndUsedTextureBytesAfter':42471,'productionIntegrated':False,'referenceAcceptance':False})
p['modelSources'][1]={'path':str(model.resolve()),'sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'bytes':model.stat().st_size};(w/'seam-changes.json').write_text(json.dumps(p,indent=2))
assert (c/'volcano_track.spm').read_bytes()==(r/'fidelity-v30/candidate/volcano_track.spm').read_bytes()
(w/'protected-preflight.json').write_text(json.dumps({'mainSPMAndProtectedRoadBytesExactV30':True,'newStoneSourceBoundsExact':True,'modelWithTextureBytesBefore':42471,'modelWithTextureBytesAfter':42471,'sharedDonorsUnmodified':True,'stage':'Static ghost-camera preview permitted; independent route distances/native/pool/gameplay still pending.'},indent=2));print('V32_SEAM_PREFLIGHT_READY',len(changed),len(affected),capAnchor,flush=True)
