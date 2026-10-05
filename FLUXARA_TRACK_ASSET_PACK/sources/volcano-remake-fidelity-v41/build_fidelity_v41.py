from pathlib import Path
import copy,hashlib,heapq,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v41';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v40/candidate',c);res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
root=E.parse(c/'scene.xml').getroot();s=(r/'build_fidelity_v37_rims.py').read_text();exec(s[s.index('def tris('):s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')")].replace('len(road)==2032','len(road)==1968'));ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
def info(f):return {'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
# Every selected block remains the original physical/material/UV mesh; only its vertex color changes.
d=parse(c/'volcano_track.spm');b=copy.deepcopy(d['buffers'][5]);groups=ns['component_triangles'](b);centers=[tuple(sum(v[k]for v in t)/3 for k in range(3))for t in road];selected=[]
for g in groups:
 vv=[b['vertices'][i]['position']for j in g for i in b['indices'][j*3:j*3+3]];bound=box(vv)
 if bound[4]-bound[1]>3.5 or len(g)>32:continue
 center=tuple((bound[k]+bound[k+3])/2 for k in range(3));near=heapq.nsmallest(32,range(len(road)),key=lambda i:math.dist(center,centers[i]));dist=min(point_triangle_distance(center,road[i])for i in near)
 if dist<=4:selected.append({'triangleIds':g,'vertexIds':sorted(set(i for j in g for i in b['indices'][j*3:j*3+3])),'bounds':bound,'center':center,'roadDistanceUpperBound':dist})
assert len(selected)==128
# Order components in spatial chains rather than using the original file order.
left=set(range(len(selected)));chains=[]
while left:
 start=min(left,key=lambda i:tuple(selected[i]['center']));chain=[start];left.remove(start)
 while left:
  i=min(left,key=lambda i:math.dist(selected[i]['center'],selected[chain[-1]]['center']))
  if math.dist(selected[i]['center'],selected[chain[-1]]['center'])>7:break
  chain.append(i);left.remove(i)
 chains.append(chain)
for chain in chains:
 for k,i in enumerate(chain):
  col=(255,58,48)if k%2==0 else(255,255,255);selected[i]['color']=col;selected[i]['chainIndex']=k
  for j in selected[i]['vertexIds']:b['vertices'][j]['color']=col
newraw=ns['replace_buffers'](d,{5:b});(c/'volcano_track.spm').write_bytes(newraw)
# Reuse an opaque light cell from the approved, unchanged fifth-map palette. A scoped alias lets the smoke use an unlit shader without affecting the fifth map or other vertex-only objects.
palette=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/textures/orbital-soccer-reference-v5/orbital_palette.png');alias='fluxara_volcano_smoke_palette_v41.png';shutil.copy2(palette,c/alias);assert palette.stat().st_size==158;mt=E.parse(c/'materials.xml');assert not any(e.get('name')==alias for e in mt.getroot());E.SubElement(mt.getroot(),'material',name=alias,shader='unlit');mt.write(c/'materials.xml',encoding='unicode');smoke=[]
for name in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']:
 old=parse(r/'fidelity-v40/candidate'/name);new=copy.deepcopy(old);assert old['materials']==[['','']]and len(old['buffers'])==1;new['materials']=[[alias,'']];buf=new['buffers'][0];entry=root.find('object[@model="'+name+'"]');pos=list(map(float,entry.get('xyz').split()));scale=list(map(float,entry.get('scale').split()));hpr=list(map(float,entry.get('hpr').split()));assert hpr[:2]==[0.,0.];angle=math.radians(hpr[2]);co,si=math.cos(angle),math.sin(angle)
 def world_position(v):
  x,y,z=[v['position'][i]*scale[i]for i in range(3)];return(pos[0]+co*x-si*y,pos[1]+si*x+co*y,pos[2]+z)
 positions=[world_position(v)for v in buf['vertices']];ymin,ymax=min(v[1]for v in positions),max(v[1]for v in positions);light=(-.45,.65,.62);ll=math.sqrt(sum(x*x for x in light));light=[x/ll for x in light]
 for v,p in zip(buf['vertices'],positions):
  nn=[((v['normal']>>s)&1023)for s in [0,10,20]];nn=[(x-1024 if x>511 else x)/511/scale[k]for k,x in enumerate(nn)];nn=[co*nn[0]-si*nn[1],si*nn[0]+co*nn[1],nn[2]];length=math.sqrt(sum(x*x for x in nn));nn=[x/length for x in nn];height=(p[1]-ymin)/(ymax-ymin);shade=.58+.42*max(0.,sum(nn[k]*light[k]for k in range(3)));gray=[x*shade for x in (142,133,161)];glow=max(0.,1-height/.72)**1.15*(.38+.62*max(0.,-nn[1]));warm=(255,166,64);target=[gray[k]*(1-glow)+warm[k]*glow for k in range(3)];v['color']=tuple(min(255,round(target[k]*255/pixel))for k,pixel in enumerate((237,228,223)));v['uv']=(.125,.75)
 raw=ns['replace_buffers'](new,{0:buf});(c/name).write_bytes(raw);budget=len(raw)+palette.stat().st_size;assert budget<=len(old['raw'])*1.2,(name,len(old['raw']),budget);smoke.append({'model':name,'beforeModelBytes':len(old['raw']),'afterModelBytes':len(raw),'afterModelPlusUsedTextureBytes':budget,'increasePercent':100*(budget/len(old['raw'])-1),'sourceWorldYRange':[ymin,ymax],'geometryNormalsBoundsIndicesAndWorldPlacementRetained':True,'bakedVertexLightingWithScopedUnlitMaterial':True})
base=json.loads((r/'fidelity-v40/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());accepted=base['acceptedSharedHistoryIncludingV39Bytes']+base['newSharedRuntimeAllFilesBytes'];total=size+accepted;assert total<base['v1Bytes'];proof={'baseCandidate':'V40','barrierBuffer':5,'roadsideBlocks':selected,'spatialChains':chains,'wallBeforeBytes':len(d['raw']),'wallAfterBytes':len(newraw),'wallGeometryUVNormalsIndicesBoundsAndPhysicalMaterialRetained':True,'smoke':smoke,'paletteSource':info(palette),'palettePoolId':'orbital-v5-texture-orbital-palette','paletteAlias':info(c/alias),'paletteDimensions':[32,16],'sampledOpaquePixel':[237,228,223,255],'sampleUV':[.125,.75],'newRasterPixels':False,'newShaderMaterialOnlyForNamedSmokeAlias':True,'candidateAllFilesBytes':size,'acceptedSharedHistoryIncludingV40Bytes':accepted,'allCandidateAndAcceptedHistoryBytes':total,'v1Bytes':base['v1Bytes'],'productionIntegrated':False,'referenceAcceptance':False};(w/'barrier-smoke-preflight.json').write_text(json.dumps(proof,indent=2));print('V41_RED_WHITE_ROADSIDE_BLOCKS_AND_WARM_SMOKE_SOURCE_READY',len(selected),smoke,total,flush=True)
