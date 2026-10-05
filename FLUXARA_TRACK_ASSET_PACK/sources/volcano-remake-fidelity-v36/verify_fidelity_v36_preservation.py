from pathlib import Path
import collections, copy, hashlib, json, math, sys, xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v36';c=w/'candidate';old=r/'fidelity-v35/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
p=json.loads((w/'visual-batch-preflight.json').read_text());plants=json.loads((w/'plant-grounding.json').read_text())
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def clean(v):return {k:q for k,q in v.items()if not k.endswith('offset')}
def payload(d):return d['raw'][30+sum(2+sum(len(n.encode())for n in pair)for pair in d['materials']):]
def active(d):
 vv=[v['position']for b in d['buffers']for v in b['vertices']];return tuple(min(v[k]for v in vv)for k in range(3))+tuple(max(v[k]for v in vv)for k in range(3))
protected=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for n in protected:assert (c/n).read_bytes()==(r/'fidelity-v2/baseline'/n).read_bytes(),n
a=parse(old/'volcano_track.spm');b=parse(c/'volcano_track.spm');assert a['bounds']==b['bounds'];assert len(a['buffers'])==len(b['buffers'])
changes=[]
for i,(x,y)in enumerate(zip(a['buffers'],b['buffers'])):
 assert x['indices']==y['indices']and x['material']==y['material'];assert len(x['vertices'])==len(y['vertices'])
 for j,(v,z)in enumerate(zip(x['vertices'],y['vertices'])):
  cv,cz=clean(v),clean(z)
  if i==p['woodBuffer']and j in p['woodRoofVertexColorIndices']:
   assert cz['color']==(255,100,66);cv.pop('color',None);cz.pop('color',None);changes.append((i,j))
  assert cv==cz,(i,j)
for pair0,pair1 in zip(a['materials'],b['materials']):
 assert [[p['newMudTextureAlias']['path'].split('/')[-1]if n in ['stk_mudpot_a.png','fluxara_drift_mudpot_a.png']else n for n in pair0]][0]==pair1
for f in c.glob('*.spm'):
 if f.name=='volcano_track.spm':continue
 if f.name in [q['name']for q in p['mapMudModelAliasChanges']]:assert payload(parse(f))==payload(parse(old/f.name)),f.name
 else:assert f.read_bytes()==(old/f.name).read_bytes(),f.name
for q in p['mudSourceModels']:
 x=parse(q['before']['path']);y=parse(q['after']['path']);assert x['bounds']==y['bounds']and x['version']==y['version']and x['flags']==y['flags'];assert payload(x)==payload(y),'all skin/animation payload must be byte exact'
src=parse(p['sourceRoofModel']['path']);dst=parse(p['newRoofModel']['path']);assert src['bounds']==dst['bounds'];assert active(src)==active(dst)
def tri_positions(buf,indices):return collections.Counter(tuple(buf['vertices'][i]['position']for i in indices[j:j+3])for j in range(0,len(indices),3))
assert tri_positions(src['buffers'][0],src['buffers'][0]['indices'][:48])==tri_positions(dst['buffers'][0],dst['buffers'][0]['indices'][:48])
assert tri_positions(src['buffers'][0],src['buffers'][0]['indices'][-3:])==tri_positions(dst['buffers'][0],dst['buffers'][0]['indices'][-3:])
assert len(dst['buffers'][0]['indices'])//3==25 and len(dst['raw'])<=len(src['raw'])
olds=E.parse(old/'scene.xml').getroot();news=E.parse(c/'scene.xml').getroot()
expected={q['before']['id']:q['after']for q in p['mudOriginalPoseChangesNameOnly']+p['roofOriginalPoseChangesNameOnly']+plants['placements']};expected[p['smokeBefore']['id']]=p['smokeAfter']
assert len(list(olds))==len(list(news))
for x,y in zip(olds,news):
 assert x.tag==y.tag
 if x.tag=='sun':assert y.attrib==p['sunAfter']
 elif x.tag=='sky-box':assert y.attrib==p['skyAfter']
 elif x.get('id')in expected:assert y.attrib==expected[x.get('id')]
 else:assert E.tostring(x)==E.tostring(y),(x.tag,x.get('id'))
for q in p['mudOriginalPoseChangesNameOnly']+p['roofOriginalPoseChangesNameOnly']:
 x,y=copy.deepcopy(q['before']),copy.deepcopy(q['after']);x.pop('name');y.pop('name');assert x==y
# Independent road clearance replay: a full transformed model is contained in the stated bounding sphere.
from terrain_triangle_distance import point_triangle_distance
road=[]
names=['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']
def yawpoint(v,attrs):
 pos=list(map(float,attrs['xyz'].split()));scale=list(map(float,attrs['scale'].split()));yaw=math.radians(float(attrs['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
 return(pos[0]+co*v[0]*scale[0]+si*v[2]*scale[2],pos[1]+v[1]*scale[1],pos[2]-si*v[0]*scale[0]+co*v[2]*scale[2])
for buf in b['buffers']:
 if b['materials'][buf['material']][0]in names:road.extend([[buf['vertices'][i]['position']for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)])
for el in news.findall('object'):
 if el.get('driveable')=='true':
  for buf in parse(c/el.get('model'))['buffers']:road.extend([[yawpoint(buf['vertices'][i]['position'],el.attrib)for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)])
assert len(road)==2032
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');cache={};margins=[]
for q in plants['placements']:
 lib=q['after']['name']
 if lib not in cache:
  node=E.parse(res/'library'/lib/'node.xml').getroot().find('object');cache[lib]=parse(res/'library'/lib/node.get('model'))
 center=q['boundingSphereCenter'];rad=q['boundingSphereRadius'];vv=[yawpoint(v['position'],q['after'])for buf in cache[lib]['buffers']for v in buf['vertices']];assert max(math.dist(v,center)for v in vv)<=rad+1e-7
 # Inspect only road triangles whose coordinate AABB can beat the known margin; exact triangle distance decides.
 threshold=rad+q['boundingSphereRoadMarginMeters']+.0001
 near=[t for t in road if sum(max(min(v[k]for v in t)-center[k],center[k]-max(v[k]for v in t),0)**2 for k in range(3))<=threshold**2]
 margin=min(point_triangle_distance(center,t)for t in near)-rad;assert abs(margin-q['boundingSphereRoadMarginMeters'])<1e-6 and margin>.15;margins.append(margin)
 assert q['after']['hpr'].split()[0]==q['after']['hpr'].split()[2]=='0' or float(q['after']['hpr'].split()[0])==float(q['after']['hpr'].split()[2])==0
for q in p['removedCandidateOwnedUnreferencedImages']:
 f=old/Path(q['path']).name;assert f.is_file()and digest(f)==q['sha256'];assert not (c/f.name).exists()
for q in p['reusedSkyTextureSources']:assert Path(q['source']['path']).read_bytes()==Path(q['alias']['path']).read_bytes()
stone=res/'textures/fluxara_volcano_stone_shared_v16.jpg';assert digest(stone)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
candidate=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());shared=sum(f.stat().st_size for f in (w/'shared-runtime').rglob('*')if f.is_file());tex=sum(f.stat().st_size for f in (w/'shared-textures').rglob('*')if f.is_file());total=candidate+208348+96362+shared+tex;assert total<6672491 and total<7693535
out={'protectedControlFilesExactV1':protected,'protectedRoadTriangles':2032,'allMainGeometryNormalsUVIndicesExactV35':True,'onlyMainVertexColoursChanged':changes,'allOtherSPMExactExceptMudTextureAliasPayloadExactIncludingAnimation':True,'roofHeaderAndActualBoundsExact':True,'roofOriginalConeAndFlagTrianglesExact':True,'roofModelBytesBefore':len(src['raw']),'roofModelBytesAfter':len(dst['raw']),'mudModelUsedTexturesBefore':p['mudModelsAndUsedTexturesBytesBefore'],'mudModelUsedTexturesAfter':p['mudModelsAndUsedTexturesBytesAfter'],'originalMudAndRoofTransformsExact':True,'repositionedDecorativePlants':len(plants['placements']),'minimumFullBoundingSphereRoadMarginMeters':min(margins),'originalStonePixelsRetained':True,'originalsAndRemovedCandidateImagesPreservedInV35':True,'candidateAllFilesBytes':candidate,'newSharedRuntimeAllFilesBytes':shared,'newSharedGlobalAliasesAllFilesBytes':tex,'acceptedSharedHistoryBytes':208348,'acceptedSharedTextureHistoryBytes':96362,'allCandidateAndAcceptedHistoryBytes':total,'integratedV1BaselineBytes':7693535,'savingVsV1Bytes':7693535-total,'savingVsV35Bytes':6672491-total,'stage':'Independent source preservation and size verification; native, runtime and visual acceptance separate.'}
(w/'preservation-verification.json').write_text(json.dumps(out,indent=2));print('V36_PRESERVATION_AND_WEIGHT_VERIFIED',total,min(margins),flush=True)
