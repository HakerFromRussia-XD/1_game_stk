from pathlib import Path
import collections,hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';c=w/'candidate';old=r/'fidelity-v36/candidate';rp=json.loads((w/'rim-preflight.json').read_text());bg=json.loads((w/'background-preflight.json').read_text());res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();removed=rp['removedUnusedCandidateImage'];assert sha(removed['preservedSource'])==removed['sha256']and not(c/Path(removed['path']).name).exists()
for f in old.iterdir():
 if f.is_file()and f.name not in ['scene.xml',Path(removed['path']).name]:assert f.read_bytes()==(c/f.name).read_bytes(),f.name
for n in ['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']:assert (c/n).read_bytes()==(r/'fidelity-v2/baseline'/n).read_bytes(),n
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();changed={q['after']['id']:q['after']for q in rp['rims']}
for q in rp['rims']:changed.update({x['after']['id']:x['after']for x in q['linkedPlants']})
new={q['attrs']['id']:q['attrs']for q in bg['placements']};assert len(new)==84;assert len(after)==len(before)+84
for x,y in zip(before,list(after)[:len(before)]):
 if x.get('id')in changed:assert y.attrib==changed[x.get('id')]
 else:assert E.tostring(x)==E.tostring(y),x.attrib
assert {e.get('id'):e.attrib for e in list(after)[len(before):]}==new
for q in rp['reusedSources']+bg['sourceModels']:assert sha(q['path'])==q['sha256']and Path(q['path']).stat().st_size==q['bytes']
def localtris(d):return [[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for b in d['buffers']for j in range(0,len(b['indices']),3)]
def world(v,a):
 p=list(map(float,a['xyz'].split()));s=list(map(float,a['scale'].split()));h=list(map(float,a['hpr'].split()));assert h[0]==h[2]==0;yaw=math.radians(h[1]);co,si=math.cos(yaw),math.sin(yaw);return(p[0]+co*v[0]*s[0]+si*v[2]*s[2],p[1]+v[1]*s[1],p[2]-si*v[0]*s[0]+co*v[2]*s[2])
def bounds(tt):return tuple(min(p[k]for p in tt)for k in range(3))+tuple(max(p[k]for p in tt)for k in range(3))
def lower(a,b):return sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3))
cache={}
def md(lib):
 if lib not in cache:
  folder=res/'library'/lib;node=E.parse(folder/'node.xml').getroot().find('object');cache[lib]=parse(folder/node.get('model'))
 return cache[lib]
def tt(attrs):return [[world(v,attrs)for v in t]for t in localtris(md(attrs['name']))]
def boundary(d):
 ts=localtris(d);ed=collections.Counter(tuple(sorted((tuple(round(v,6)for v in t[j]),tuple(round(v,6)for v in t[(j+1)%3]))))for t in ts for j in range(3));
 keys={p for edge,n in ed.items()if n==1 for p in edge};return list({tuple(v['position'])for b in d['buffers']for v in b['vertices']if tuple(round(x,6)for x in v['position'])in keys})
maxXZ=0;maxOverlap=0;grass='fluxara_driftlib_volcano_grass_cap_v32';stone='fluxara_driftlib_volcano_stone_column_v32';gr=boundary(md(grass));sr=boundary(md(stone));assert len(gr)==len(sr)==16
for q in rp['rims']:
 a=q['after'];b=dict(after.find('library[@id="'+a['id'].replace('_Grass','_Stone')+'"]').attrib);gp=[world(v,a)for v in gr];sp=[world(v,b)for v in sr]
 for v in sp:
  g=min(gp,key=lambda x:math.hypot(x[0]-v[0],x[2]-v[2]));maxXZ=max(maxXZ,math.hypot(g[0]-v[0],g[2]-v[2]));maxOverlap=max(maxOverlap,abs(v[1]-g[1]-.08))
assert maxXZ<2e-5 and maxOverlap<2e-5,(maxXZ,maxOverlap)
main=parse(c/'volcano_track.spm');names=['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png'];roads=[t for b in main['buffers']if main['materials'][b['material']][0]in names for t in localtris({'buffers':[b]})]
for el in after.findall('object'):
 if el.get('driveable')=='true':roads.extend([[world(v,el.attrib)for v in t]for t in localtris(parse(c/el.get('model')))])
assert len(roads)==2032;rb=[bounds(t)for t in roads];checks=[];attributes={**changed,**new}
for ident,attrs in attributes.items():
 threshold=2. if ident in new else .25;tri=tt(attrs);whole=bounds([v for t in tri for v in t]);candidateRoads=[(t,b)for t,b in zip(roads,rb)if lower(whole,b)<=threshold**2];pairs=0
 for t in tri:
  tb=bounds(t)
  for q,qb in candidateRoads:
   if lower(tb,qb)<=threshold**2:assert triangle_distance(t,q)>threshold,(ident,t,q);pairs+=1
 checks.append({'id':ident,'allRenderedTrianglesChecked':len(tri),'roadClearanceLowerBoundMeters':threshold,'exactCloseTrianglePairs':pairs,'allExcludedPairsUseAABBLowerBound':True})
maxTreeContact=0
for q in rp['rims']:
 surface=tt(q['after'])
 for child in q['linkedPlants']:
  if child['sourceGroundingRole']=='Tree':pos=list(map(float,child['after']['xyz'].split()));err=min(point_triangle_distance(pos,t)for t in surface);maxTreeContact=max(maxTreeContact,err);assert err<1e-5
bgt=tt(after.find('library[@name="fluxara_driftlib_volcano_backdrop_terrain_v23"]').attrib);mt=[t for q in bg['placements']if q['role']=='Mound'for t in tt(q['attrs'])];maxBackgroundTreeContact=0
for q in bg['placements']:
 if q['role']=='Tree':p=list(map(float,q['attrs']['xyz'].split()));err=min(point_triangle_distance(p,t)for t in bgt+mt);assert err<1e-5;(maxBackgroundTreeContact:=max(maxBackgroundTreeContact,err))
sourceStone=res/'textures/fluxara_volcano_stone_shared_v16.jpg';assert sha(sourceStone)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
base=json.loads((r/'fidelity-v36/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());shared=base['acceptedSharedHistoryBytes']+base['acceptedSharedTextureHistoryBytes']+base['newSharedRuntimeAllFilesBytes']+base['newSharedGlobalAliasesAllFilesBytes'];total=size+shared;assert total==bg['allCandidateAndAcceptedHistoryBytes']and total<base['allCandidateAndAcceptedHistoryBytes']
proof={'baseCandidate':'V36','allOtherCandidateModelsMaterialXMLPixelsAndControlsByteExactV36':True,'protectedControlsExactV1':True,'protectedRoadTriangles':2032,'sourceStonePixelsRetained':True,'newSPMTextureMaterialPayloadBytes':0,'thickerGrassCaps':rp['changedCapInstances'],'linkedExistingVegetationTransforms':rp['linkedPlantInstances'],'newBackgroundCoordinateInstances':84,'grassStoneBoundaryPointsPerGroup':16,'maximumWorldRimXZErrorMeters':maxXZ,'maximum0p08mInterfaceOverlapErrorMeters':maxOverlap,'verifiedRoadChecks':checks,'existingTreeRootsOnActualCapsMaxErrorMeters':maxTreeContact,'newTreeRootsOnBackgroundOrMoundMaxErrorMeters':maxBackgroundTreeContact,'allSourceLibraryHashesExact':True,'removedCandidateImagePreservedInV36':True,'candidateAllFilesBytes':size,'acceptedAllSharedHistoryIncludingV36Bytes':shared,'allCandidateAndAcceptedHistoryBytes':total,'v1Bytes':base['integratedV1BaselineBytes'],'savingVsV1Bytes':base['integratedV1BaselineBytes']-total,'savingVsV36Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'productionIntegrated':False,'referenceAcceptance':False,'nativeRuntimeAndFullVisualAcceptanceSeparate':True};(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V37_INDEPENDENT_SOURCE_SEAMS_CONTACT_AND_CLEARANCE_VERIFIED',len(checks),total,maxOverlap,flush=True)
