from pathlib import Path
import json,math,struct,sys,copy,shutil,random,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v13';w.mkdir(exist_ok=True);c=w/'candidate';old=r/'fidelity-v12/candidate';shutil.copytree(old,c,dirs_exist_ok=True)
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');libname='fluxara_driftlib_volcano_fountain_v13';lib=repo/'iosApp/FluxaraResources/library'/libname;lib.mkdir(exist_ok=True);texname='fluxara_volcano_lava_shared_v13.jpg';globaltex=repo/'iosApp/FluxaraResources/textures'/texname;original=old/'lava_2k_diffuse.jpg'
assert not globaltex.exists()or globaltex.read_bytes()==original.read_bytes();shutil.copy2(original,globaltex)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
code=(r/'fidelity_v2.py').read_text();ns={'struct':struct,'math':math};exec(code[code.index('def encode_buffer'):code.index('new_vertices, new_indices')],ns)
d=parse(c/'volcano_track.spm');b=d['buffers'][12];groups=ns['component_triangles'](b);target=next(g for g in groups if len(g)==72)
def subset(b,ts):
 indices=[i for t in sorted(ts)for i in b['indices'][3*t:3*t+3]];used=sorted(set(indices));mapping={v:i for i,v in enumerate(used)};return {'vertices':[copy.deepcopy(b['vertices'][i])for i in used],'indices':[mapping[i]for i in indices],'material':0}
source=subset(b,target);lo=[min(v['position'][k]for v in source['vertices'])for k in range(3)];hi=[max(v['position'][k]for v in source['vertices'])for k in range(3)]
def spm(buffer,texture='',flags=1):
 vv=buffer['vertices'];ii=buffer['indices'];bounds=[min(v['position'][k]for v in vv)for k in range(3)]+[max(v['position'][k]for v in vv)for k in range(3)];t=texture.encode();raw=bytearray(b'SP'+bytes([10,flags])+struct.pack('<6f',*bounds)+struct.pack('<H',1)+bytes([len(t)])+t+b'\0'+struct.pack('<HHIIH',1,1,len(vv),len(ii),0))
 for v in vv:
  raw+=struct.pack('<3fI',*v['position'],v['normal'])
  if flags&2:raw+=b'\x80'if tuple(v.get('color',(255,255,255)))==(255,255,255)else b'\xff'+bytes(v['color'])
  if texture:raw+=struct.pack('<2e',*v['uv'])
 raw+=struct.pack('<'+str(len(ii))+('H'if len(vv)>255 else'B'),*ii);return raw
sources=w/'original-component';sources.mkdir(exist_ok=True);(sources/'original_lava_column.spm').write_bytes(spm(source,'lava_2k_diffuse.jpg',3));shutil.copy2(original,sources/original.name)
collider='vr_v13_original_lava_column_collision.spm';(c/collider).write_bytes(spm(source))
keep=subset(b,set(range(len(b['indices'])//3))-set(target));keep['material']=b['material'];(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](d,{12:keep}))
vertices=[];indices=[];tube_vertex_count=0
def vecsub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
 length=math.sqrt(sum(x*x for x in v));return tuple(x/length for x in v)if length>1e-12 else(0,1,0)
def path(j,t):
 return [((.47+.10*t),(.02+.96*math.sin(math.pi*.65*t)),(.45+.05*t)),((.48-.32*t),(.02+.68*math.sin(math.pi*.80*t)),(.5+.14*t)),((.51+.34*t),(.015+.70*math.sin(math.pi*.78*t)),(.48-.2*t))][j]
for j in range(3):
 offset=len(vertices);rings=9;sides=6
 for i in range(rings):
  t=i/(rings-1);p=path(j,t);tangent=unit(vecsub(path(j,min(1,t+.001)),path(j,max(0,t-.001))));u=unit(cross(tangent,(0,0,1)));v=cross(tangent,u);radius=(.036 if j==0 else .027)*(1-.65*t)
  for k in range(sides+1):
   a=k*2*math.pi/sides;point=tuple(p[q]+radius*(math.cos(a)*u[q]+math.sin(a)*v[q])for q in range(3));vertices.append({'position':point,'uv':(k/sides,t*3.5)})
 for i in range(rings-1):
  for k in range(sides):
   a=offset+i*(sides+1)+k;z=a+sides+1;indices.extend([a,a+1,z,a+1,z+1,z])
 for end in [0,rings-1]:
  centre=len(vertices);vertices.append({'position':path(j,end/(rings-1)),'uv':(.5,end/(rings-1))});start=offset+end*(sides+1)
  for k in range(sides):indices.extend([centre,start+k+1,start+k]if end==0 else[centre,start+k,start+k+1])
tube_vertex_count=len(vertices);rng=random.Random(13026)
for j in range(16):
 p=(rng.uniform(.05,.95),rng.uniform(.4,.90),rng.uniform(.03,.97));size=rng.uniform(.006,.018);offset=len(vertices)
 for direction in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:vertices.append({'position':tuple(p[k]+direction[k]*size*(2 if k==1 else 1)for k in range(3)),'uv':(.125,.5)})
 for tri in [(0,2,4),(4,2,1),(1,2,5),(5,2,0),(4,3,0),(1,3,4),(5,3,1),(0,3,5)]:indices.extend(offset+i for i in tri)
unitlo=[min(v['position'][k]for v in vertices)for k in range(3)];unithi=[max(v['position'][k]for v in vertices)for k in range(3)]
for v in vertices:v['position']=tuple(lo[k]+(v['position'][k]-unitlo[k])/(unithi[k]-unitlo[k])*(hi[k]-lo[k])for k in range(3))
for v in vertices[:tube_vertex_count]:v['position']=(v['position'][0],lo[1]+(v['position'][1]-lo[1])*.62,v['position'][2])
# The effect keeps its original bounds through flying embers; the liquid jets emerge just above the crater.
ember_shift=hi[1]-max(v['position'][1]for v in vertices[tube_vertex_count:tube_vertex_count+6])
for v in vertices[tube_vertex_count:tube_vertex_count+6]:v['position']=(v['position'][0],v['position'][1]+ember_shift,v['position'][2])
normals=[[0.,0.,0.]for v in vertices]
for i in range(0,len(indices),3):
 a,z,h=indices[i:i+3];n=cross(vecsub(vertices[z]['position'],vertices[a]['position']),vecsub(vertices[h]['position'],vertices[a]['position']))
 for q in [a,z,h]:normals[q]=[normals[q][k]+n[k]for k in range(3)]
for v,n in zip(vertices,normals):v['normal']=ns['packed_normal'](unit(n))
model='vr_v13_lava_fountain.spm';(lib/model).write_bytes(spm({'vertices':vertices,'indices':indices},texname));(lib/'node.xml').write_text(f'<scene><object id="VolcanoFountain" type="animation" model="{model}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false"><animated-texture name="{texname}" dy="-0.05000" /></object></scene>');(lib/'materials.xml').write_text(f'<materials><material name="{texname}" /></materials>')
rewritten=[]
for p in c.glob('*.spm'):
 q=parse(p);names=[[texname if n=='lava_2k_diffuse.jpg'else n for n in pair]for pair in q['materials']]
 if names!=q['materials']:p.write_bytes(rewrite_texture_names(q,names));rewritten.append(p.name)
scene=E.parse(c/'scene.xml');material=E.parse(c/'materials.xml')
for root in [scene.getroot(),material.getroot()]:
 for e in root.iter():
  if e.get('name')=='lava_2k_diffuse.jpg':e.set('name',texname)
E.SubElement(scene.getroot(),'object',id='VRV13_OriginalLavaColumnCollision',type='animation',model=collider,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',shape='exact',**{'skeletal-animation':'false'});E.SubElement(scene.getroot(),'library',id='VRV13_PooledLavaFountain',name=libname,xyz='0 0 0',hpr='0 0 0',scale='1 1 1')
top=max(v['position'][1]for v in vertices[:tube_vertex_count]);peak=[v['position']for v in vertices[:tube_vertex_count]if v['position'][1]>top-.7];anchor=[sum(p[k]for p in peak)/len(peak)for k in range(3)];plume_anchor=[anchor[0],lo[1]+(top-lo[1])*.68,anchor[2]];cloud=next(e for e in scene.getroot().findall('object')if e.get('model')=='AshColumn.spm');oldcloud=E.tostring(cloud,encoding='unicode');cloudmodel=parse(c/'AshColumn.spm');cv=[v['position']for b in cloudmodel['buffers']for v in b['vertices']];bottom=min(v[1]for v in cv);points=[v for v in cv if abs(v[1]-bottom)<.001];base=[sum(v[k]for v in points)/len(points)for k in range(3)];scale=list(map(float,cloud.get('scale').split()));xyz=[plume_anchor[k]-base[k]*scale[k]for k in range(3)];xyz[1]-=2;cloud.set('xyz',' '.join(f'{v:.9f}'for v in xyz))
scene.write(c/'scene.xml',encoding='unicode');material.write(c/'materials.xml',encoding='unicode');(c/'lava_2k_diffuse.jpg').unlink()
before=(sources/'original_lava_column.spm').stat().st_size+original.stat().st_size;after=(lib/model).stat().st_size+globaltex.stat().st_size;assert after<=before*1.2,(before,after)
proof={'sourceModel':str((old/'volcano_track.spm').resolve()),'sourceBuffer':12,'originalTriangleIds':target,'sourceComponentTriangles':72,'sourceComponentBounds':[lo,hi],'originalExtractedVisual':str((sources/'original_lava_column.spm').resolve()),'originalTexture':str(original.resolve()),'newSharedLibrary':str(lib),'newSharedModel':str(lib/model),'newGlobalTexture':str(globaltex),'textureAlias':texname,'texturePixelsUnchanged':hashlib.sha256(original.read_bytes()).hexdigest()==hashlib.sha256(globaltex.read_bytes()).hexdigest(),'sourceModelWithTextureBytes':before,'newModelWithTextureBytes':after,'modelWithTextureWeightChangePercent':(after/before-1)*100,'triangles':len(indices)//3,'vertices':len(vertices),'jetCount':3,'emberCount':16,'originalOriginAxesAndComponentBoundsRetained':True,'hiddenOriginalCollisionModel':collider,'textureAliasOnlyModels':rewritten,'oldCloudXml':oldcloud,'newCloudXml':E.tostring(cloud,encoding='unicode'),'jetPeakAnchorWorld':anchor,'plumeAnchorWorld':plume_anchor,'plumeLowerPartOverlapsJetsAboveCrater':True,'liquidJetHeightScaleWithinOriginalBounds':.62,'flyingEmbersRetainOverallEffectBounds':True,'reference':'Figma 378:39 erupting volcano, thin orange lava jets, sparks and dark plume','newImagePixels':False,'productionIntegrated':False};(w/'fountain-changes.json').write_text(json.dumps(proof,indent=2));print('V13_LAVA_JETS_READY',before,after,proof['modelWithTextureWeightChangePercent'],len(indices)//3,flush=True)
