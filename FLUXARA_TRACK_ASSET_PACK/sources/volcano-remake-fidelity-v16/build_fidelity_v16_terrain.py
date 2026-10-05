from pathlib import Path
import math,struct,json,sys,shutil,copy,random,hashlib,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v16';w.mkdir(exist_ok=True);old=r/'fidelity-v15/candidate';c=w/'candidate';shutil.copytree(old,c,dirs_exist_ok=True);repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';pack=repo/'FLUXARA_TRACK_ASSET_PACK';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
s=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct};exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
code=(r/'build_fidelity_v12_greenery.py').read_text();exec(code[code.index('def bary'):code.index('folder=Path')])
def normalize(v):
 l=math.sqrt(sum(x*x for x in v));return tuple(x/l for x in v)if l else(0,1,0)
def encode(bufs,mats,bounds):
 raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*bounds)+struct.pack('<H',len(mats)))
 for pair in mats:
  for name in pair:raw+=bytes([len(name.encode())])+name.encode()
 raw+=struct.pack('<HH',1,len(bufs))
 for b in bufs:raw+=ns['encode_buffer'](b,mats)
 return raw
source=pack/'models/shared/fluxara_grassy_island_v1/library/fluxara_driftlib_cliffGrassEarth_a/fluxara_driftlib_cliffGrassEarth_a.spm';d=parse(source);buffers=copy.deepcopy(d['buffers']);alias='fluxara_volcano_stone_shared_v16.jpg';texture=res/'textures'/alias;assert not texture.exists()or texture.read_bytes()==(old/'Rock13_col.jpg').read_bytes();shutil.copy2(old/'Rock13_col.jpg',texture)
# Adapt an actual pooled oval grass-earth shelf, retaining its source overall bounds/origin/axes.
for bi,b in enumerate(buffers):
 ys=[v['position'][1]for v in b['vertices']];a,z=min(ys),max(ys)
 for v in b['vertices']:
  x,y,zp=v['position'];t=(y-a)/(z-a);newy=.57+t*(d['bounds'][4]-.57)if bi==0 else d['bounds'][1]+t*(.62-d['bounds'][1]);v['position']=(x,newy,zp)
  if bi==0:v['color']=(round(82+37*t),round(144+41*t),round(34+19*t));v.pop('uv',None)
  else:v['color']=(255,255,255)
 nn=[[0.,0.,0.]for v in b['vertices']]
 for i in range(0,len(b['indices']),3):
  aa,bb,cc=b['indices'][i:i+3];u=sub(b['vertices'][bb]['position'],b['vertices'][aa]['position']);v=sub(b['vertices'][cc]['position'],b['vertices'][aa]['position']);n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
  for j in [aa,bb,cc]:nn[j]=[nn[j][k]+n[k]for k in range(3)]
 for v,n in zip(b['vertices'],nn):v['normal']=ns['packed_normal'](normalize(n))
# Cylindrical UVs are authored only on the copied stone side, avoiding stretched source soil UVs.
b=buffers[1];ymin=min(v['position'][1]for v in b['vertices']);ymax=max(v['position'][1]for v in b['vertices'])
for v in b['vertices']:v['uv']=((math.atan2(v['position'][2],v['position'][0])/(2*math.pi)%1)*2,(v['position'][1]-ymin)/(ymax-ymin)*2)
indices=[];duplicates={}
for t in range(len(b['indices'])//3):
 face=b['indices'][3*t:3*t+3];uu=[b['vertices'][j]['uv'][0]for j in face]
 for j in face:
  if max(uu)-min(uu)>1 and b['vertices'][j]['uv'][0]<1:
   if j not in duplicates:
    v=copy.deepcopy(b['vertices'][j]);v['uv']=(v['uv'][0]+2,v['uv'][1]);duplicates[j]=len(b['vertices']);b['vertices'].append(v)
   indices.append(duplicates[j])
  else:indices.append(j)
b['indices']=indices
modelname='vr_v16_grass_stone_cliff.spm';library=res/'library/fluxara_driftlib_volcano_grass_stone_cliff_v16';library.mkdir(exist_ok=True);model=library/modelname;model.write_bytes(encode(buffers,[['',''],[alias,'']],d['bounds']));(library/'node.xml').write_text(f'<scene><object id="RoundedStoneCliff" type="animation" model="{modelname}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');(library/'materials.xml').write_text(f'<materials><material name="{alias}" /></materials>');before=source.stat().st_size+sum((source.parent/n).stat().st_size for pair in d['materials']for n in pair if n);after=model.stat().st_size+texture.stat().st_size;assert after<=before*1.2;assert parse(model)['bounds']==d['bounds']
# All four existing stone surfaces now resolve to one shared file with byte-identical pixels.
aliased=[]
for p in c.glob('*.spm'):
 t=parse(p);names=[[alias if n=='Rock13_col.jpg'else n for n in pair]for pair in t['materials']]
 if names!=t['materials']:p.write_bytes(rewrite_texture_names(t,names));aliased.append(p.name)
scene=E.parse(c/'scene.xml');materials=E.parse(c/'materials.xml')
for root in [scene.getroot(),materials.getroot()]:
 for e in root.iter():
  if e.get('name')=='Rock13_col.jpg':e.set('name',alias)
materials.write(c/'materials.xml',encoding='unicode');(c/'Rock13_col.jpg').unlink()
main=parse(c/'volcano_track.spm');green=main['buffers'][4];road=[b for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png']];triangles=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)];protected=[p for b in road for p in triangles(b)]
# Include the original reverse-only driving ramp unchanged, even in the forward inspection.
for e in scene.getroot().findall('object'):
 if e.get('driveable')=='true'and e.get('model')and e.get('hpr')=='0.0 -0.0 0.0':
  xyz=list(map(float,e.get('xyz').split()));sc=list(map(float,e.get('scale').split()))
  for b in parse(c/e.get('model'))['buffers']:protected +=[[tuple(v[k]*sc[k]+xyz[k]for k in range(3))for v in t]for t in triangles(b)]
boxes=[([min(v[k]for v in p)for k in range(3)],[max(v[k]for v in p)for k in range(3)],p)for p in protected]
def closest(q):
 scores=sorted((sum(max(a[k]-q[k],q[k]-z[k],0)**2 for k in range(3)),i)for i,(a,z,t)in enumerate(boxes));best=1e20
 for low,i in scores:
  if low>=best*best:break
  best=min(best,point_triangle_distance(q,boxes[i][2]))
 return best
flat=[];edges=collections.defaultdict(list)
for p in triangles(green):
 u=sub(p[1],p[0]);v=sub(p[2],p[0]);n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);l=math.sqrt(dot(n,n))
 if l and abs(n[1])/l>.85:
  flat.append((p,l/2))
  for i in range(3):
   a,z=p[i],p[(i+1)%3];key=tuple(sorted((tuple(round(x,3)for x in a),tuple(round(x,3)for x in z))));edges[key].append((a,z))
boundary=[vv[0]for vv in edges.values()if len(vv)==1];weights=[math.dist(a,z)for a,z in boundary];rng=random.Random(16026);verts=[v['position']for b in parse(model)['buffers']for v in b['vertices']];localcy=(d['bounds'][1]+d['bounds'][4])/2;towers=[list(map(float,e.get('xyz').split()))for e in scene.getroot().findall('library')if'castle'in e.get('name','')];proposals=[]
for i in range(2600):
 a,z=rng.choices(boundary,weights=weights,k=1)[0];t=rng.random();point=[a[k]+t*(z[k]-a[k])for k in range(3)];sx=rng.uniform(1.05,2.3);sz=rng.uniform(.95,2.0);sy=rng.uniform(6.5,13.5);yaw=math.degrees(math.atan2(-(z[2]-a[2]),z[0]-a[0]));raiseby=rng.uniform(1.7,3.5);xyz=[point[0],point[1]+raiseby-d['bounds'][4]*sy,point[2]];rad=max(math.hypot(v[0]*sx,v[2]*sz)for v in verts);sr=max(math.sqrt((v[0]*sx)**2+((v[1]-localcy)*sy)**2+(v[2]*sz)**2)for v in verts);center=[xyz[0],xyz[1]+localcy*sy,xyz[2]]
 if any(math.hypot(xyz[0]-p[0],xyz[2]-p[2])<rad+6 for p in towers):continue
 distance=closest(center)
 if distance<sr+3.5 or distance>70:continue
 proposals.append({'kind':'cliff','xyz':xyz,'hpr':[0,yaw,0],'scale':[sx,sy,sz],'groundHeight':point[1],'topRaiseMeters':raiseby,'horizontalRadius':rad,'boundingSphereCentre':center,'boundingSphereRadius':sr,'minimumProtectedRoadDistance3D':distance,'roadClearanceBeyondBoundingSphere':distance-sr,'score':abs(distance-24)+rng.uniform(0,12),'library':library.name})
selected=[]
for row in sorted(proposals,key=lambda q:q['score']):
 if all(math.hypot(row['xyz'][0]-p['xyz'][0],row['xyz'][2]-p['xyz'][2])>.75*(row['horizontalRadius']+p['horizontalRadius'])for p in selected):selected.append(row)
 if len(selected)==96:break
assert len(selected)>=24,('not enough safe edge positions',len(selected),len(proposals))
# Reuse the existing soft hill mesh directly for rounded crests behind the new cliff edges.
hilllib=res/'library/fluxara_driftlib_grassy_hill_v2';hillmodel=hilllib/'fluxara_driftlib_grassy_hill_v2_main.spm';hd=parse(hillmodel);hv=[v['position']for b in hd['buffers']for v in b['vertices']];hillproposals=[]
for i in range(1500):
 p,area=rng.choices(flat,weights=[area for p,area in flat],k=1)[0];aa,bb=rng.random(),rng.random()
 if aa+bb>1:aa,bb=1-aa,1-bb
 x,y,z=[aa*p[0][k]+bb*p[1][k]+(1-aa-bb)*p[2][k]for k in range(3)];sx=rng.uniform(7,13);sz=rng.uniform(7,12);sy=rng.uniform(2.5,5);radius=max(math.hypot(v[0]*sx,v[2]*sz)for v in hv);center=[x,y+sy*.5-.12,z];sr=max(math.sqrt((v[0]*sx)**2+((v[1]-.5)*sy)**2+(v[2]*sz)**2)for v in hv);dist=closest(center)
 if dist<sr+3.5 or dist>65:continue
 if any(math.hypot(x-q['xyz'][0],z-q['xyz'][2])<radius+q['horizontalRadius']*.7 for q in selected):continue
 foot=[greenheight(x+math.cos(j*math.pi/4)*radius*.75,z+math.sin(j*math.pi/4)*radius*.75,y)for j in range(8)]
 if sum(h is not None for h in foot)<6:continue
 if any(math.hypot(x-t[0],z-t[2])<radius+6 for t in towers):continue
 hillproposals.append({'kind':'hill','xyz':[x,y-.12,z],'hpr':[0,rng.uniform(-180,180),0],'scale':[sx,sy,sz],'groundHeight':y,'horizontalRadius':radius,'boundingSphereCentre':center,'boundingSphereRadius':sr,'minimumProtectedRoadDistance3D':dist,'roadClearanceBeyondBoundingSphere':dist-sr,'score':abs(dist-25)+rng.uniform(0,10),'library':hilllib.name,'sourcePoolObjectId':'lap-v1-5e6c75bde5183e13'})
hills=[]
for row in sorted(hillproposals,key=lambda q:q['score']):
 if all(math.hypot(row['xyz'][0]-p['xyz'][0],row['xyz'][2]-p['xyz'][2])>row['horizontalRadius']+p['horizontalRadius']for p in hills):hills.append(row)
 if len(hills)==20:break
for i,row in enumerate(selected+hills):
 row['id']=f'VRV16_RoundedTerrain_{i:03}';E.SubElement(scene.getroot(),'library',id=row['id'],name=row['library'],**{k:' '.join(f'{v:.8f}'for v in row[k])for k in ['xyz','hpr','scale']})
scene.write(c/'scene.xml',encoding='unicode');mapbytes=sum(p.stat().st_size for p in c.iterdir()if p.is_file());base=json.loads((r/'fidelity-v15/preservation-verification.json').read_text());libbytes=sum(p.stat().st_size for p in library.iterdir()if p.is_file());total=mapbytes+base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+libbytes+base['newGlobalTextureBytes']+texture.stat().st_size;assert total<base['v1Bytes'];proof={'baseCandidate':'V15','sourcePoolObjectId':'shared-grassy-island-v1','sourcePooledModel':str(source),'sourceBounds':list(d['bounds']),'adaptedSharedModel':str(model),'adaptedSharedLibrary':str(library),'globalStoneAlias':str(texture),'stonePixelsByteIdenticalOriginal':True,'existingStoneModelsAliasOnly':aliased,'sourceModelWithTextureBytes':before,'adaptedModelWithTextureBytes':after,'modelWithTextureWeightChangePercent':(after/before-1)*100,'upper20PercentPassed':True,'newMeshTriangles':432,'newMeshVertices':sum(len(b['vertices'])for b in buffers),'geometryAdaptation':'Source oval shelf copied; green lip compressed, existing earth side extended within same original local overall bounds, original horizontal coordinates retained; old stone image applied. New vertex colors on green lip, cylindrical UVs on copied stone side. All original map stone UVs retained. Ghost instances, original track unchanged.','placements':selected+hills,'newCliffPlacements':len(selected),'directSharedHillPlacements':len(hills),'hillSourceModel':str(hillmodel),'hillSourcePoolObjectId':'lap-v1-5e6c75bde5183e13','newMeshFiles':1,'newTexturePixels':False,'minimumRoadSphereMarginMeters':min(q['roadClearanceBeyondBoundingSphere']for q in selected+hills),'protectedTriangleCount':len(protected),'candidateMapBytes':mapbytes,'newSharedRuntimeLibraryBytes':libbytes,'newSharedLibraryBytesIncludingRetainedHistoricalVariants':base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+libbytes,'newGlobalTextureBytes':base['newGlobalTextureBytes']+texture.stat().st_size,'candidateIncludingNewSharedBytes':total,'v1Bytes':base['v1Bytes'],'savingBytesVsV1':base['v1Bytes']-total,'productionIntegrated':False,'referenceAcceptance':False};(w/'terrain-changes.json').write_text(json.dumps(proof,indent=2));print('V16_ROUNDED_TERRAIN_READY',len(selected),len(hills),total,proof['minimumRoadSphereMarginMeters'],flush=True)

# Reproducible final export excludes only verified, archived unused candidate sky copies.
import runpy
runpy.run_path(str(r/'remove_fidelity_v16_unused_sky.py'),run_name='__main__')
