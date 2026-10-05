from pathlib import Path
import math,struct,json,shutil,sys,copy,random,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';w.mkdir(exist_ok=True);old=r/'fidelity-v14/candidate';c=w/'candidate';shutil.copytree(old,c,dirs_exist_ok=True);repo=Path('/Users/motoricallc/Downloads/fluxara-drift');resources=repo/'iosApp/FluxaraResources';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
s=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct};exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
 l=math.sqrt(sum(x*x for x in v));return tuple(x/l for x in v)if l>1e-12 else(0,1,0)
def normals(buf):
 nn=[[0.,0.,0.]for v in buf['vertices']]
 for i in range(0,len(buf['indices']),3):
  a,b,z=buf['indices'][i:i+3];n=cross(sub(buf['vertices'][b]['position'],buf['vertices'][a]['position']),sub(buf['vertices'][z]['position'],buf['vertices'][a]['position']))
  for j in [a,b,z]:nn[j]=[nn[j][k]+n[k]for k in range(3)]
 for v,n in zip(buf['vertices'],nn):v['normal']=ns['packed_normal'](unit(n))
def points(buf,triangles):return [buf['vertices'][i]['position']for t in triangles for i in buf['indices'][t*3:t*3+3]]
def bounds(vv):return [[min(v[k]for v in vv)for k in range(3)],[max(v[k]for v in vv)for k in range(3)]]
def subset(buf,triangles,material=None):
 ii=[j for t in sorted(triangles)for j in buf['indices'][3*t:3*t+3]];used=sorted(set(ii));mapping={v:i for i,v in enumerate(used)};return {'vertices':[copy.deepcopy(buf['vertices'][i])for i in used],'indices':[mapping[i]for i in ii],'material':buf['material']if material is None else material}
def encoded(bufs,textures,flags=3,header_bounds=None):
 vv=[v['position']for b in bufs for v in b['vertices']];lo,hi=bounds(vv);raw=bytearray(b'SP'+bytes([10,flags])+struct.pack('<6f',*(header_bounds or lo+hi))+struct.pack('<H',len(textures)))
 for pair in textures:
  for n in pair:
   t=n.encode();raw+=bytes([len(t)])+t
 raw+=struct.pack('<HH',1,len(bufs))
 for b in bufs:
  verts=b['vertices'];indices=b['indices'];raw+=struct.pack('<IIH',len(verts),len(indices),b['material'])
  for v in verts:
   raw+=struct.pack('<3fI',*v['position'],v['normal'])
   if flags&2:
    color=tuple(v.get('color',(255,255,255)));raw+=b'\x80'if color==(255,255,255)else b'\xff'+bytes(color)
   if textures[b['material']][0]:raw+=struct.pack('<2e',*v['uv'])
  raw+=struct.pack('<'+str(len(indices))+('B'if len(verts)<=255 else'H'if len(verts)<=65535 else'I'),*indices)
 return raw
# One set of geometry files is shared by the roofed and crenellated scene libraries.
brick='fluxara_castle_brick_v15.jpg';brickpath=resources/'textures'/brick;assert not brickpath.exists()or brickpath.read_bytes()==(old/'castelwall.jpg').read_bytes();shutil.copy2(old/'castelwall.jpg',brickpath)
source=resources/'library/fluxara_driftlib_castle_tower_v1/fluxara_driftlib_castle_tower_v1_main.spm';v9=resources/'library/fluxara_driftlib_volcano_castle_tower_v9/vr_v9_castle_tower.spm';oldbody=parse(v9)['buffers'][0];radius=parse(source)['bounds'][3];apex=parse(source)['bounds'][4];body={'vertices':[],'indices':[],'material':0};roof={'vertices':[],'indices':[],'material':0};flag={'vertices':[],'indices':[],'material':0};tint=(178,184,195)
def vertex(buf,p,color=tint,uv=None):
 if uv is None:uv=((math.atan2(p[2],p[0])/(2*math.pi))%1*2,p[1]*6)
 buf['vertices'].append({'position':p,'color':color,'uv':uv});return len(buf['vertices'])-1
profile=[(0,radius),(.075,radius),(.075,.19),(.775,.19),(.775,radius),(.91,radius),(.96,.21)];sides=12
for y,rad in profile:
 for j in range(sides+1):
  a=2*math.pi*j/sides;vertex(body,(rad*math.cos(a),y,rad*math.sin(a)),uv=(j/sides*2,y*6))
for ring in range(len(profile)-1):
 for j in range(sides):
  a=ring*(sides+1)+j;b=a+sides+1;body['indices'] +=[a,b,a+1,a+1,b,b+1]
for end in [0,len(profile)-1]:
 center=vertex(body,(0,profile[end][0],0));start=end*(sides+1)
 for j in range(sides):body['indices'] +=[center,start+j,start+j+1]if end==0 else[center,start+j+1,start+j]
# Four rounded merlons; the base profile still sets the original horizontal bounds.
boxfaces=[(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),(2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
for j in range(4):
 a=math.pi/4+j*math.pi/2;cx=.177*math.cos(a);cz=.177*math.sin(a);base=len(body['vertices'])
 for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:vertex(body,(cx+x*.026,.952+y*.065,cz+z*.026))
 for tri in boxfaces:body['indices'] +=[base+i for i in tri]
# Keep only the visible fronts of the old window panels, reducing hidden geometry.
windowtris=[t for t in range(len(oldbody['indices'])//3)if all(oldbody['vertices'][j]['uv']==(.875,.125)for j in oldbody['indices'][3*t:3*t+3])];window=subset(oldbody,windowtris,0);front=[]
for g in ns['component_triangles'](window):
 maxrad=max(math.hypot(v[0],v[2])for v in points(window,g))
 front +=[t for t in g if all(math.hypot(window['vertices'][j]['position'][0],window['vertices'][j]['position'][2])>maxrad-.00001 for j in window['indices'][3*t:3*t+3])]
window=subset(window,front,0);offset=len(body['vertices'])
for v in window['vertices']:vertex(body,v['position'],(35,55,73))
body['indices'] +=[offset+i for i in window['indices']]
# Red conical roof and a small pennant keep the original top extent.
for j in range(16):
 a=2*math.pi*j/16;vertex(roof,(radius*math.cos(a),1.025,radius*math.sin(a)),(210+(j%2)*14,65+(j%2)*12,43))
peak=vertex(roof,(0,1.17,0),(214,62,38))
for j in range(16):roof['indices'] +=[j,peak,(j+1)%16]
for buf in [roof,flag]:
 base=len(buf['vertices'])
 for y in [1.155,apex]:
  for j in range(8):
   a=2*math.pi*j/8;vertex(buf,(.004*math.cos(a),y,.004*math.sin(a)),(108,74,46))
 for j in range(8):
  a=base+j;b=base+8+j;n=base+(j+1)%8;m=base+8+(j+1)%8;buf['indices'] +=[a,b,n,n,b,m]
 base=len(buf['vertices']);vertex(buf,(.004,apex-.005,0),(237,73,37));vertex(buf,(.081,apex-.015,.014),(250,88,44));vertex(buf,(.004,apex-.060,0),(195,47,31));buf['indices'] +=[base,base+2,base+1]
for buf in [body,roof,flag]:normals(buf)
modelnames={'body':'fluxara_castle_v15_body.spm','roof':'fluxara_castle_v15_roof.spm','flag':'fluxara_castle_v15_flag.spm'};modelpaths={k:resources/'models'/n for k,n in modelnames.items()};raws={'body':encoded([body],[[brick,'']]),'roof':encoded([roof],[['','']],header_bounds=[-radius,.96,-radius,radius,apex,radius]),'flag':encoded([flag],[['','']])};baseline=source.stat().st_size+(source.parent/'dp_palette.png').stat().st_size;total=sum(map(len,raws.values()))+brickpath.stat().st_size;assert total<=baseline*1.2,(total,baseline)
for k,path in modelpaths.items():assert not path.exists()or path.read_bytes()==raws[k];path.write_bytes(raws[k])
libs={}
for role in ['roof','battlement']:
 name='fluxara_driftlib_volcano_castle_'+role+'_v15';lib=resources/'library'/name;lib.mkdir(exist_ok=True);root=E.Element('scene');E.SubElement(root,'object',id='CastleBody',type='animation',model=modelnames['body'],xyz='0 0 0',hpr='0 0 0',scale='1 1 1'if role=='roof'else'1 1.2 1',interaction='ghost',**{'skeletal-animation':'false'});E.SubElement(root,'object',id='CastleCap',type='animation',model=modelnames['roof'if role=='roof'else'flag'],xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'});E.ElementTree(root).write(lib/'node.xml',encoding='unicode');(lib/'materials.xml').write_text(f'<materials><material name="{brick}" /></materials>');libs[role]=str(lib)
# Replace upright legacy tower clusters; every old collision triangle stays in a map-only proxy.
main=parse(c/'volcano_track.spm');wallidx=next(i for i,b in enumerate(main['buffers'])if main['materials'][b['material']][0]=='castelwall.jpg');wall=main['buffers'][wallidx];groups=ns['component_triangles'](wall);scene=E.parse(c/'scene.xml');remove={};changes=[];bodies=[]
for j,g in enumerate(groups):
 if len(g)not in [142,188]:continue
 lo,hi=bounds(points(wall,g));ext=[hi[k]-lo[k]for k in range(3)]
 if max(ext[0],ext[2])/min(ext[0],ext[2])<1.04 and ext[1]>2*ext[0]and min(ext[0],ext[2])>3:bodies.append((j,g,lo,hi))
for n,(j,g,lo,hi)in enumerate(bodies):
 selected=[q for q,ts in enumerate(groups)if q==j or(len(ts)<=30 and all(bounds(points(wall,ts))[0][k]>=lo[k]-.35 and bounds(points(wall,ts))[1][k]<=hi[k]+.35 for k in [0,2])and bounds(points(wall,ts))[0][1]>=lo[1]+(hi[1]-lo[1])*.55 and bounds(points(wall,ts))[1][1]<=hi[1]+2)]
 take={wallidx:{t for q in selected for t in groups[q]}}
 for i,b in enumerate(main['buffers']):
  tex=main['materials'][b['material']][0]
  if 'roof'not in tex.lower()and'wood'not in tex.lower():continue
  for ts in ns['component_triangles'](b):
   a,z=bounds(points(b,ts));center=[(a[k]+z[k])/2 for k in range(3)]
   if len(ts)<=20 and all(lo[k]-.35<=center[k]<=hi[k]+.35 for k in [0,2])and a[1]>=lo[1]+(hi[1]-lo[1])*.5 and z[1]<=hi[1]+10:take.setdefault(i,set()).update(ts)
 vv=[p for i,ts in take.items()for p in points(main['buffers'][i],ts)];a,z=bounds(vv);scale=[(z[k]-a[k])/(1.26 if k==1 else radius*2)for k in range(3)];xyz=[a[k]+(radius*scale[k]if k in [0,2]else 0)for k in range(3)];role='roof'if any(i!=wallidx and ts for i,ts in take.items())else'battlement';coll={'vertices':[],'indices':[],'material':0}
 for i,ts in take.items():
  assert not(remove.setdefault(i,set())&ts),(n,i);remove[i].update(ts);part=subset(main['buffers'][i],ts,0);offset=len(coll['vertices']);coll['vertices']+=part['vertices'];coll['indices'] +=[offset+k for k in part['indices']]
 collname=f'vr_v15_original_tower_collision_{n:02d}.spm';(c/collname).write_bytes(encoded([coll],[['','']],flags=1));E.SubElement(scene.getroot(),'object',id=f'VRV15_OriginalTowerCollision_{n:02d}',type='animation',model=collname,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',shape='exact',**{'skeletal-animation':'false'});ident=f'VRV15_PooledTower_{n:02d}';E.SubElement(scene.getroot(),'library',id=ident,name=Path(libs[role]).name,xyz=' '.join(f'{v:.9f}'for v in xyz),hpr='0 0 0',scale=' '.join(f'{v:.9f}'for v in scale));changes.append({'id':ident,'originalComponent':j,'removedTriangleIdsByBuffer':{str(i):sorted(ts)for i,ts in take.items()},'originalVisualBounds':[a,z],'xyz':xyz,'scale':scale,'role':role,'library':Path(libs[role]).name,'collider':collname,'originalCollisionTriangles':len(coll['indices'])//3})
for e in scene.getroot().findall('library'):
 if e.get('name')=='fluxara_driftlib_volcano_castle_tower_v9':e.set('name',Path(libs['roof']).name)
replacements={i:subset(main['buffers'][i],set(range(len(main['buffers'][i]['indices'])//3))-ts)for i,ts in remove.items()};(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](main,replacements))
# Shared roof over the existing stone gateway, above the protected road.
cap={'vertices':[],'indices':[],'material':0};span=21.;depth=11.;nx=10;nz=4
for side in [-1,1]:
 for x in range(nx):
  for z in range(nz):
   x0=-span/2+span*x/nx;x1=-span/2+span*(x+1)/nx;z0=depth*.5*z/nz;z1=depth*.5*(z+1)/nz;offset=len(cap['vertices']);t=(x+z)%3;color=[(207,64,39),(228,86,48),(192,54,37)][t]
   for px,pz in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]:vertex(cap,(px,1.6*(1-pz/(depth*.5))+(.018 if t==1 else 0),side*pz),color)
   cap['indices'] +=[offset,offset+1,offset+2,offset,offset+2,offset+3]if side<0 else[offset+2,offset+1,offset,offset+3,offset+2,offset]
normals(cap);capname='fluxara_volcano_gate_roof_v15.spm';cappath=resources/'models'/capname;cappath.write_bytes(encoded([cap],[['','']]));caplib=resources/'library/fluxara_driftlib_volcano_gate_roof_v15';caplib.mkdir(exist_ok=True);(caplib/'node.xml').write_text(f'<scene><object id="GateRoof" type="animation" model="{capname}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');(caplib/'materials.xml').write_text('<materials />');E.SubElement(scene.getroot(),'library',id='VRV15_GateRoof',name=caplib.name,xyz='55.469727 4.35 51.670963',hpr='0 0 0',scale='1 1 1')
# All uses of the brick image share one actual global file.
renamed=[]
for p in c.glob('*.spm'):
 d=parse(p);names=[[brick if n=='castelwall.jpg'else n for n in pair]for pair in d['materials']]
 if names!=d['materials']:p.write_bytes(rewrite_texture_names(d,names));renamed.append(p.name)
materials=E.parse(c/'materials.xml')
for root in [scene.getroot(),materials.getroot()]:
 for e in root.iter():
  if e.get('name')=='castelwall.jpg':e.set('name',brick)
scene.write(c/'scene.xml',encoding='unicode');materials.write(c/'materials.xml',encoding='unicode');(c/'castelwall.jpg').unlink()
# Dense irregular puffs within each previous local box, using the same two-tone palette.
def ico(subdivide):
 p=(1+math.sqrt(5))/2;vv=[unit(v)for v in [(-1,p,0),(1,p,0),(-1,-p,0),(1,-p,0),(0,-1,p),(0,1,p),(0,-1,-p),(0,1,-p),(p,0,-1),(p,0,1),(-p,0,-1),(-p,0,1)]];tt=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
 if subdivide:
  cache={};out=[]
  def mid(a,b):
   key=tuple(sorted((a,b)))
   if key not in cache:cache[key]=len(vv);vv.append(unit(tuple((vv[a][k]+vv[b][k])/2 for k in range(3))))
   return cache[key]
  for a,b,z in tt:
   ab=mid(a,b);bz=mid(b,z);za=mid(z,a);out +=[(a,ab,za),(b,bz,ab),(z,za,bz),(ab,bz,za)]
  tt=out
 return vv,tt
smoke=[]
for num,name in enumerate(['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']):
 original=parse(old/name);oldbuf=original['buffers'][0];lo=original['bounds'][:3];hi=original['bounds'][3:];xml=next(e for e in scene.getroot().findall('object')if e.get('model')==name);sc=list(map(float,xml.get('scale').split()));dim=[(hi[k]-lo[k])*sc[k]for k in range(3)];count=len(oldbuf['indices'])//240;rng=random.Random(15026+num);puffs=[];verts=[];tri=[];owners=[]
 for j in range(count+max(2,count//3)):
  core=j<count;t=(j/(count-1))if core else rng.uniform(.18,.95);rad=min(dim)*(.20+.19*t)*(1 if core else .47);center=[dim[0]*(.70-.36*t),dim[1]*(.18+.58*t),dim[2]*(.63-.25*t)]
  if j not in [0,count-1]:
   center=[center[k]+rng.uniform(-.07,.07)*dim[k]for k in range(3)]
  ell=[rad*rng.uniform(.88,1.12)for k in range(3)];puffs.append((center,ell));sphere,faces=ico(core);offset=len(verts)
  for v in sphere:verts.append(tuple(center[k]+v[k]*ell[k]for k in range(3)))
  for face in faces:tri.append(tuple(offset+i for i in face));owners.append(j)
 fullbounds=bounds(verts);extremes={i for i,v in enumerate(verts)if any(abs(v[k]-fullbounds[a][k])<1e-8 for a in [0,1]for k in range(3))};kept=[]
 for face,owner in zip(tri,owners):
  inside=any(all(sum(((verts[v][k]-ctr[k])/rad[k])**2 for k in range(3))<.93**2 for v in face)for q,(ctr,rad)in enumerate(puffs)if q!=owner)
  if not inside or any(v in extremes for v in face):kept +=list(face)
 used=sorted(set(kept));mapping={v:i for i,v in enumerate(used)};buf={'vertices':[],'indices':[mapping[v]for v in kept],'material':0}
 for i in used:
  normalized=[(verts[i][k]-fullbounds[0][k])/(fullbounds[1][k]-fullbounds[0][k])for k in range(3)];pos=tuple(lo[k]+normalized[k]*(hi[k]-lo[k])for k in range(3));buf['vertices'].append({'position':pos,'uv':(.75 if normalized[1]<.38 else .25,.5)})
 normals(buf);raw=encoded([buf],original['materials'],flags=1,header_bounds=original['bounds']);assert len(raw)+(c/original['materials'][0][0]).stat().st_size <=1.2*((old/name).stat().st_size+(old/original['materials'][0][0]).stat().st_size),(name,len(raw),(old/name).stat().st_size);(c/name).write_bytes(raw);check=parse(c/name);assert all(abs(x-y)<.0001 for x,y in zip(check['bounds'],original['bounds']));smoke.append({'model':name,'sourceBounds':list(original['bounds']),'puffs':len(puffs),'triangles':len(kept)//3,'vertices':len(used),'bytesBefore':(old/name).stat().st_size,'bytesAfter':len(raw),'originalGhostTransformUnchanged':True,'palettePixelsUnchanged':True,'removedHiddenOverlapTriangles':len(tri)-len(kept)//3})
proof={'baseCandidate':'V14','newTowerBody':str(modelpaths['body']),'newTowerRoof':str(modelpaths['roof']),'newTowerFlag':str(modelpaths['flag']),'globalBrickTexture':str(brickpath),'brickImageBytesUnchanged':True,'sourcePoolModel':str(source),'sourceModelWithTextureBytes':baseline,'allTowerVariantsGeometryWithSharedTextureBytes':total,'towerModelWithTextureChangePercent':(total/baseline-1)*100,'towerCompositeBounds':list(parse(source)['bounds']),'roofedLibrary':libs['roof'],'battlementLibrary':libs['battlement'],'additionalTowerPlacements':changes,'existingTwoTowerPlacementsUnchangedExceptLibrary':True,'mainRemovalTriangleIdsByBuffer':{str(i):sorted(v)for i,v in remove.items()},'newGateRoofModel':str(cappath),'newGateRoofLibrary':str(caplib),'gateRoofPlacementId':'VRV15_GateRoof','gateRoofPosition':[55.469727,4.35,51.670963],'smoke':smoke,'brickAliasOnlyModels':renamed,'newImagePixels':False,'productionIntegrated':False,'referenceAcceptance':False};(w/'castle-atmosphere-changes.json').write_text(json.dumps(proof,indent=2));print('V15_CASTLE_ATMOSPHERE_DRAFT_READY',len(changes),baseline,total,smoke,flush=True)

import runpy
runpy.run_path(str(r/"fix_fidelity_v15_library_layout.py"),run_name="__main__")
