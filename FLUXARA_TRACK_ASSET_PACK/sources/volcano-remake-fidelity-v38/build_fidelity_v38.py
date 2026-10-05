from pathlib import Path
import collections,copy,hashlib,json,math,random,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v38';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v37/candidate',c);shared=w/'shared-runtime';shared.mkdir();res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot();s=(r/'build_fidelity_v37_rims.py').read_text();exec(s[s.index('def tris('):s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')")]);ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
def info(f):return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
def encode(d,b):
 flags=d['flags'];assert d['version']==10 and flags in [1,3]and len(d['buffers'])==1;raw=bytearray(d['raw'][:30+sum(2+sum(len(n.encode())for n in pair)for pair in d['materials'])]);raw+=struct.pack('<HHIIH',1,1,len(b['vertices']),len(b['indices']),b['material'])
 for v in b['vertices']:
  raw+=struct.pack('<3fI',*v['position'],v['normal'])
  if flags&2:
   col=v.get('color',(255,255,255));raw+=b'\x80'if col==(255,255,255)else b'\xff'+bytes(col)
  if d['materials'][b['material']][0]:raw+=struct.pack('<2e',*v['uv'])
  if d['materials'][b['material']][1]:raw+=struct.pack('<2e',*v['uv2'])
 raw+=struct.pack('<'+str(len(b['indices']))+('I'if len(b['vertices'])>65535 else'H'if len(b['vertices'])>255 else'B'),*b['indices']);raw+=d['raw'][d['geometry_end']:];return raw
def actual_bounds(buf):
 vv=[v['position']for v in buf['vertices']];return tuple(min(v[k]for v in vv)for k in range(3))+tuple(max(v[k]for v in vv)for k in range(3))
def normal(v):return [(q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]]]
def renormalize(buf,source,ids):
 def key(v):return tuple(round(x,6)for x in v['position'])
 sums={key(v):[0.,0.,0.]for v in buf['vertices']}
 for j in range(0,len(buf['indices']),3):
  ii=buf['indices'][j:j+3];a,b,c=[buf['vertices'][i]['position']for i in ii];ab=[b[k]-a[k]for k in range(3)];ac=[c[k]-a[k]for k in range(3)];n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
  if j<len(source['indices']):
   oldn=[sum(normal(source['vertices'][i])[k]for i in ii)for k in range(3)]
   if sum(n[k]*oldn[k]for k in range(3))<0:n=[-x for x in n]
  for i in ii:
   for k in range(3):sums[key(buf['vertices'][i])][k]+=n[k]
 for i in ids:
  n=sums[key(buf['vertices'][i])];length=math.sqrt(sum(x*x for x in n));assert length>1e-10;buf['vertices'][i]['normal']=ns['packed_normal']([x/length for x in n])
def library(name,srcfolder,filename,raw):
 lib=shared/name;lib.mkdir();(lib/filename).write_bytes(raw);node=E.parse(srcfolder/'node.xml');node.getroot().find('object').set('model',filename);node.write(lib/'node.xml',encoding='unicode');shutil.copy2(srcfolder/'materials.xml',lib/'materials.xml');return lib
# A small copied side skirt creates the missing visible green volume. Source bounds, top positions and all texture pixels stay unchanged.
grasssrc=res/'library/fluxara_driftlib_volcano_grass_cap_v32/vr_v32_sealed_grass_cap.spm';gd=parse(grasssrc);gb=copy.deepcopy(gd['buffers'][0]);oldgb=gd['buffers'][0]
def vk(i):return tuple(round(x,6)for x in gb['vertices'][i]['position'])
ec=collections.Counter(tuple(sorted((vk(gb['indices'][j+k]),vk(gb['indices'][j+(k+1)%3]))))for j in range(0,len(gb['indices']),3)for k in range(3));boundary={e for e,n in ec.items()if n==1};direct=[]
for j in range(0,len(gb['indices']),3):
 for k in range(3):
  a,b=gb['indices'][j+k],gb['indices'][j+(k+1)%3]
  if tuple(sorted((vk(a),vk(b))))in boundary:direct.append((a,b))
assert len(direct)==16;upper={i for edge in direct for i in edge};assert len(upper)==16;old_anchor=max(gb['vertices'][i]['position'][1]for i in upper);bottom={}
for i in sorted(upper):
 v=copy.deepcopy(gb['vertices'][i]);x,y,z=v['position'];v['position']=(x,gd['bounds'][1],z);v['color']=(74,126,24);bottom[i]=len(gb['vertices']);gb['vertices'].append(v)
for a,b in direct:gb['indices']=list(gb['indices'])+[b,a,bottom[a],b,bottom[a],bottom[b]]
renormalize(gb,oldgb,upper|set(bottom.values()));assert actual_bounds(gb)==gd['bounds'];graw=encode(gd,gb);assert len(graw)<=len(gd['raw'])*1.2;glib=library('fluxara_driftlib_volcano_grass_roll_v38',grasssrc.parent,'vr_v38_grass_roll.spm',graw);cache[glib.name]=parse(glib/'vr_v38_grass_roll.spm')
oldplants=json.loads((r/'fidelity-v37/rim-preflight.json').read_text())['rims'];bycap={q['after']['id']:q for q in oldplants};grassrows=[]
for e in root.findall('library'):
 if e.get('name')!='fluxara_driftlib_volcano_grass_cap_v32':continue
 old=dict(e.attrib);p,sz,yaw=params(old);newsy=sz[1]*(gd['bounds'][4]-old_anchor)/(gd['bounds'][4]-gd['bounds'][1]);newp=[p[0],p[1]+old_anchor*sz[1]-gd['bounds'][1]*newsy,p[2]];attrs=copy.deepcopy(old);attrs.update({'name':glib.name,'xyz':' '.join(f'{x:.8f}'for x in newp),'scale':' '.join(f'{x:.8f}'for x in [sz[0],newsy,sz[2]])});valid,pr=certificate(attrs);assert valid,(old['id'],pr);linked=[]
 for q in bycap[e.get('id')]['linkedPlants']:
  child=root.find('library[@id="'+q['after']['id']+'"]');cp,cs,cy=params(child.attrib);h=(cp[1]-p[1])/sz[1];groundrole=q['sourceGroundingRole']
  # Reconstruct the old root point from its original source grounding, then use the new cap's affine height.
  if groundrole=='Bush':root_y=cp[1]+model(child.get('name'))['bounds'][1]*cs[1]+.15
  elif groundrole=='Mound':root_y=cp[1]+.10
  else:root_y=cp[1]
  h=(root_y-p[1])/sz[1];delta=newp[1]+h*newsy-root_y;ca=dict(child.attrib);ca['xyz']=' '.join(f'{x:.8f}'for x in [cp[0],cp[1]+delta,cp[2]]);ok,prc=certificate(ca);assert ok,(ca['id'],prc);linked.append({'before':dict(child.attrib),'after':ca,'role':groundrole,'clearance':prc});child.attrib.clear();child.attrib.update(ca)
 e.attrib.clear();e.attrib.update(attrs);grassrows.append({'before':old,'after':attrs,'originalTopWorldY':p[1]+gd['bounds'][4]*sz[1],'newTopWorldY':newp[1]+gd['bounds'][4]*newsy,'oldInterfaceWorldY':p[1]+old_anchor*sz[1],'newInterfaceWorldY':newp[1]+gd['bounds'][1]*newsy,'clearance':pr,'linkedPlants':linked})
# Rolling far terrain: modify only triangles whose old XZ boxes are over60m away from every protected road triangle.
bgsrc=res/'library/fluxara_driftlib_volcano_backdrop_terrain_v23/vr_v23_rounded_backdrop_terrain.spm';bd=parse(bgsrc);bb=copy.deepcopy(bd['buffers'][0]);groups=ns['component_triangles'](bb);far={j for g in groups if len(g)in[264,292,349,270,528,392]for j in g};hroad=[[(v[0],0.,v[2])for v in t]for t in road];hrbox=[box(t)for t in hroad];locked=set();distances={}
for j in range(len(bb['indices'])//3):
 ii=bb['indices'][j*3:j*3+3];v=[bb['vertices'][i]['position']for i in ii];hbox=box([(q[0],0.,q[2])for q in v]);near=min(dsq(hbox,z)for z in hrbox)
 if j not in far or near<=60**2:locked.update(ii)
for i,v in enumerate(bb['vertices']):
 if any(v['position'][k]in[bd['bounds'][k],bd['bounds'][k+3]]for k in range(3)):locked.add(i)
changed=[]
for i,v in enumerate(bb['vertices']):
 if i in locked:continue
 x,y,z=v['position'];point=(x,0.,z);dist=min(point_triangle_distance(point,t)for t,b in zip(hroad,hrbox)if dsq(tuple(point)*2,b)<400**2)if any(dsq(tuple(point)*2,b)<400**2 for b in hrbox)else 400;factor=max(0.,min(1.,(dist-60)/70));rise=(11*(1+math.sin(x*.031)*math.cos(z*.027))+5*(1+math.sin((x-z)*.019)))*factor;yy=min(bd['bounds'][4]-.5,y+rise);v['position']=(x,yy,z);changed.append(i)
assert len(changed)>30;affected={i for j in range(0,len(bb['indices']),3)if set(bb['indices'][j:j+3])&set(changed)for i in bb['indices'][j:j+3]};renormalize(bb,bd['buffers'][0],affected);braw=encode(bd,bb);assert actual_bounds(bb)==bd['bounds']and len(braw)<=len(bd['raw'])*1.2;blib=library('fluxara_driftlib_volcano_rolling_terrain_v38',bgsrc.parent,'vr_v38_rolling_terrain.spm',braw);cache[blib.name]=parse(blib/'vr_v38_rolling_terrain.spm');bgentry=root.find('library[@name="fluxara_driftlib_volcano_backdrop_terrain_v23"]');oldbg=dict(bgentry.attrib);bgentry.set('name',blib.name)
# White/gold clouds are copies of the actual pooled rounded ash volume: only mesh colors change, no raster pixels.
cloudsrc=c/'AshCloud.spm';cd=parse(cloudsrc);cb=copy.deepcopy(cd['buffers'][0])
for v in cb['vertices']:
 u=(v['position'][1]-cd['bounds'][1])/(cd['bounds'][4]-cd['bounds'][1]);v['color']=tuple(round(a+(b-a)*u)for a,b in zip((232,184,130),(255,247,229)))
craw=encode(cd,cb);assert len(craw)<=len(cd['raw'])*1.2;clib=shared/'fluxara_driftlib_volcano_sky_cloud_v38';clib.mkdir();(clib/'vr_v38_sky_cloud.spm').write_bytes(craw);(clib/'node.xml').write_text('<scene><object id="WarmSkyCloud" type="animation" model="vr_v38_sky_cloud.spm" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');shutil.copy2(grasssrc.parent/'materials.xml',clib/'materials.xml');cache[clib.name]=parse(clib/'vr_v38_sky_cloud.spm');cloudrows=[]
for k,(x,y,z,sx,sy,sz,yaw)in enumerate([(-320,132,-400,.09,.17,.075,25),(-220,147,-520,.11,.19,.09,-20),(-75,139,-430,.085,.16,.07,40),(90,152,-450,.095,.18,.08,15),(285,128,-360,.1,.16,.08,-25),(390,146,-120,.085,.17,.075,30),(-385,122,80,.09,.16,.07,-10),(145,165,330,.09,.18,.085,15)]):
 attrs={'id':f'VRV38_SkyCloud_{k:03d}','name':clib.name,'xyz':f'{x} {y} {z}','hpr':f'0 {yaw} 0','scale':f'{sx} {sy} {sz}'};valid,pr=certificate(attrs,required=5);assert valid,(attrs,pr);E.SubElement(root,'library',**attrs);cloudrows.append({'attrs':attrs,'clearance':pr})
# Only this candidate copy loses an old unreferenced filename. The original image and previous working copies stay intact.
unused=c/'stktex_generic_lavaA.png';allrefs=set();visited=set();xmlfiles=list(c.glob('*.xml'));modelpaths=list(c.glob('*.spm'))
def walklib(name):
 if name in visited:return
 visited.add(name);folder=res/'library'/name;node=E.parse(folder/'node.xml').getroot();xmlfiles.extend(folder.glob('*.xml'));modelpaths.extend(folder.glob('*.spm'))
 for child in node.findall('library'):walklib(child.get('name'))
for e in root.findall('library'):
 if e.get('name')not in[glib.name,blib.name,clib.name]:walklib(e.get('name'))
for lib in [glib,blib,clib]:xmlfiles.extend(lib.glob('*.xml'));modelpaths.extend(lib.glob('*.spm'))
for f in modelpaths:allrefs.update(n for pair in parse(f)['materials']for n in pair if n)
for f in xmlfiles:
 for node in E.parse(f).getroot().iter():allrefs.update(n for v in node.attrib.values()for n in v.split())
assert unused.name not in allrefs and unused.name not in(c/'scripting.as').read_text();assert not any(unused.name in f.read_text()for f in (res/'gfx').glob('*.xml'));removed=info(unused);removed['preservedSource']=str(r/'fidelity-v37/candidate'/unused.name);unused.unlink()
tree.write(c/'scene.xml',encoding='unicode');proof={'baseCandidate':'V37','grassSource':info(grasssrc),'newGrassModel':info(glib/'vr_v38_grass_roll.spm'),'grassAddedVertices':16,'grassAddedTriangles':32,'grassActualBoundsRetained':True,'grassOldVertexPositionsUVColorsRetained':True,'grassNormalChanges':sorted(upper|set(bottom.values())),'grassOldAnchorY':old_anchor,'grassNewAnchorY':gd['bounds'][1],'grassPlacements':grassrows,'terrainSource':info(bgsrc),'newTerrainModel':info(blib/'vr_v38_rolling_terrain.spm'),'terrainChangedPositionIndices':changed,'terrainChangedNormalIndices':sorted(affected),'terrainLockedVertexIndices':sorted(locked),'terrainNearRoadLockedDistanceMeters':60,'terrainOriginalUVIndicesColorsSourceBoundsRetained':True,'originalTerrainPlacement':oldbg,'newTerrainPlacement':dict(bgentry.attrib),'cloudSource':info(cloudsrc),'newCloudModel':info(clib/'vr_v38_sky_cloud.spm'),'cloudNewPlacements':cloudrows,'cloudLocalGeometryNormalsUVBoundsRetained':True,'removedCandidateUnreferencedImage':removed,'recurseReferencedOriginalLibraries':sorted(visited),'newPixels':False,'productionIntegrated':False,'referenceAcceptance':False,'stage':'Coherent source shape/sky batch. Reground84background props, then independent source/runtime/native/pool gates.'};(w/'shape-sky-preflight.json').write_text(json.dumps(proof,indent=2));print('V38_SHAPE_SKY_SOURCE_READY',len(graw),len(braw),len(craw),len(changed),len(cloudrows),flush=True)
