from pathlib import Path
import collections,copy,hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v38';c=w/'candidate';old=r/'fidelity-v37/candidate';pre=json.loads((w/'shape-sky-preflight.json').read_text());bg=json.loads((w/'background-grounding.json').read_text());res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();removed=pre['removedCandidateUnreferencedImage'];assert sha(removed['preservedSource'])==removed['sha256']and not(c/Path(removed['path']).name).exists()
for f in old.iterdir():
 if f.is_file()and f.name not in ['scene.xml',Path(removed['path']).name]:assert f.read_bytes()==(c/f.name).read_bytes(),f.name
for n in ['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']:assert (c/n).read_bytes()==(r/'fidelity-v2/baseline'/n).read_bytes(),n
s=(r/'verify_fidelity_v37_preservation.py').read_text();exec(s[s.index('def localtris('):s.index('maxXZ=')]);
for lib in (w/'shared-runtime').iterdir():cache[lib.name]=parse(lib/E.parse(lib/'node.xml').getroot().find('object').get('model'))
def active(d):v=[v['position']for b in d['buffers']for v in b['vertices']];return tuple(min(q[k]for q in v)for k in range(3))+tuple(max(q[k]for q in v)for k in range(3))
sourcechecks=[]
for name,typ in [('Grass','grass'),('Terrain','terrain'),('Cloud','cloud')]:
 src=pre[typ+'Source'];assert sha(src['path'])==src['sha256'];a=parse(src['path']);b=parse(pre['new'+name+'Model']['path']);assert a['bounds']==b['bounds']==active(a)==active(b)and a['flags']==b['flags'];av=a['buffers'][0];bv=b['buffers'][0];assert len(b['raw'])<=len(a['raw'])*1.2
 if typ=='grass':
  assert len(bv['vertices'])==len(av['vertices'])+16 and len(bv['indices'])==len(av['indices'])+96;assert bv['indices'][:len(av['indices'])]==av['indices'];assert a['materials']==b['materials']
  for i,(u,v)in enumerate(zip(av['vertices'],bv['vertices'])):
   assert all(u.get(k)==v.get(k)for k in ['position','uv','uv2','color']);assert i in pre['grassNormalChanges']or u['normal']==v['normal']
 elif typ=='terrain':
  assert av['indices']==bv['indices']and a['materials']==b['materials'];changed=set(pre['terrainChangedPositionIndices']);norms=set(pre['terrainChangedNormalIndices']);assert not(changed&set(pre['terrainLockedVertexIndices']))
  for i,(u,v)in enumerate(zip(av['vertices'],bv['vertices'])):
   assert u['position'][0]==v['position'][0]and u['position'][2]==v['position'][2];assert i in changed or u['position']==v['position'];assert i in norms or u['normal']==v['normal'];assert all(u.get(k)==v.get(k)for k in ['uv','uv2','color'])
 else:
  assert av['indices']==bv['indices']and a['materials']==b['materials'];assert len(a['raw'])==len(b['raw']);assert all(all(u.get(k)==v.get(k)for k in ['position','normal','uv','uv2'])for u,v in zip(av['vertices'],bv['vertices']))
 sourcechecks.append({'role':typ,'sourceBytes':len(a['raw']),'newModelBytes':len(b['raw']),'ratio':len(b['raw'])/len(a['raw']),'headerAndActiveBoundsExact':True,'texturePixelsAddedOrEdited':False})
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();changed={q['after']['id']:q['after']for q in pre['grassPlacements']}
for q in pre['grassPlacements']:changed.update({x['after']['id']:x['after']for x in q['linkedPlants']})
changed.update({q['after']['id']:q['after']for q in bg['placements']});changed[pre['newTerrainPlacement']['id']]=pre['newTerrainPlacement'];new={q['attrs']['id']:q['attrs']for q in pre['cloudNewPlacements']};assert len(after)==len(before)+8
for x,y in zip(before,list(after)[:len(before)]):
 if x.get('id')in changed:assert y.attrib==changed[x.get('id')]
 else:assert E.tostring(x)==E.tostring(y),x.attrib
assert {e.get('id'):e.attrib for e in list(after)[len(before):]}==new
maxXZ=0;maxOverlap=0;maxPeak=0;gr=boundary(md('fluxara_driftlib_volcano_grass_roll_v38'));sr=boundary(md('fluxara_driftlib_volcano_stone_column_v32'));assert len(gr)==len(sr)==16
for q in pre['grassPlacements']:
 a=q['after'];b=after.find('library[@id="'+a['id'].replace('_Grass','_Stone')+'"]').attrib;gp=[world(v,a)for v in gr];sp=[world(v,b)for v in sr]
 assert all(q['before'][k]==a[k]for k in ['id','hpr']);assert [float(a['scale'].split()[k])for k in [0,2]]==[float(q['before']['scale'].split()[k])for k in [0,2]]
 for v in sp:
  g=min(gp,key=lambda x:math.hypot(x[0]-v[0],x[2]-v[2]));maxXZ=max(maxXZ,math.hypot(g[0]-v[0],g[2]-v[2]));maxOverlap=max(maxOverlap,abs(v[1]-g[1]-.08))
 maxPeak=max(maxPeak,abs(q['originalTopWorldY']-q['newTopWorldY']))
assert maxXZ<2e-5 and maxOverlap<2e-5 and maxPeak<2e-5
s=(r/'verify_fidelity_v37_preservation.py').read_text();exec(s[s.index('main=parse('):s.index('assert len(roads)==2032')]);assert len(roads)==2032;rb=[bounds(t)for t in roads];checks=[]
for ident,attrs in {**changed,**new}.items():
 threshold=5. if ident in new else 2. if ident.startswith('VRV37_Background')else .25
 if ident==pre['newTerrainPlacement']['id']:continue
 tri=tt(attrs);whole=bounds([v for t in tri for v in t]);candidateRoads=[(t,b)for t,b in zip(roads,rb)if lower(whole,b)<=threshold**2];pairs=0
 for t in tri:
  tb=bounds(t)
  for q,qb in candidateRoads:
   if lower(tb,qb)<=threshold**2:assert triangle_distance(t,q)>threshold,(ident,t,q);pairs+=1
 checks.append({'id':ident,'allRenderedTrianglesChecked':len(tri),'roadClearanceLowerBoundMeters':threshold,'exactCloseTrianglePairs':pairs})
a=parse(pre['terrainSource']['path']);b=parse(pre['newTerrainModel']['path']);changedIDs=set(pre['terrainChangedPositionIndices']);roadXZ=[[(v[0],0,v[2])for v in t]for t in roads];roadXZbox=[bounds(t)for t in roadXZ];changedTri=0;minTerrainDistance=math.inf
for j in range(0,len(b['buffers'][0]['indices']),3):
 ii=b['buffers'][0]['indices'][j:j+3]
 if not(changedIDs&set(ii)):continue
 h=[(b['buffers'][0]['vertices'][i]['position'][0],0,b['buffers'][0]['vertices'][i]['position'][2])for i in ii];d=min(lower(bounds(h),z)for z in roadXZbox);assert d>60**2;minTerrainDistance=min(minTerrainDistance,math.sqrt(d));changedTri+=1
maxTreeContact=0
for q in pre['grassPlacements']:
 surface=tt(q['after'])
 for child in q['linkedPlants']:
  if child['role']=='Tree':pos=list(map(float,child['after']['xyz'].split()));err=min(point_triangle_distance(pos,t)for t in surface);maxTreeContact=max(maxTreeContact,err);assert err<1e-5
bgt=tt(pre['newTerrainPlacement']);mt=[t for q in bg['placements']if q['role']=='Mound'for t in tt(q['after'])];maxBackgroundTreeContact=0
for q in bg['placements']:
 assert all(q['before'][k]==q['after'][k]for k in ['hpr','scale','name','id'])
 if q['role']=='Tree':p=list(map(float,q['after']['xyz'].split()));err=min(point_triangle_distance(p,t)for t in bgt+mt);assert err<1e-5;maxBackgroundTreeContact=max(maxBackgroundTreeContact,err)
assert sha(res/'textures/fluxara_volcano_stone_shared_v16.jpg')=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
base=json.loads((r/'fidelity-v37/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());shared=sum(f.stat().st_size for f in(w/'shared-runtime').rglob('*')if f.is_file());total=size+shared+base['acceptedAllSharedHistoryIncludingV36Bytes'];assert total<base['allCandidateAndAcceptedHistoryBytes']
proof={'baseCandidate':'V37','allOtherCandidateFilesExactV37':True,'protectedControlsExactV1':True,'protectedRoadTriangles':2032,'allOriginalCollisionModelsAndPlacementsByteExactV37':True,'sourceStonePixelsRetained':True,'newPixels':False,'sourceObjectChecks':sourcechecks,'grassStoneBoundaryPointsPerGroup':16,'maximumWorldRimXZErrorMeters':maxXZ,'maximum0p08mInterfaceOverlapErrorMeters':maxOverlap,'maximumCapPeakWorldYChangeMeters':maxPeak,'changedFarTerrainTriangles':changedTri,'changedFarTerrainXZDistanceToRoadLowerBoundMeters':minTerrainDistance,'verifiedRoadChecks':checks,'existingTreeRootsOnActualCapsMaxErrorMeters':maxTreeContact,'backgroundTreeRootsOnTerrainOrMoundMaxErrorMeters':maxBackgroundTreeContact,'candidateAllFilesBytes':size,'acceptedSharedHistoryIncludingV37Bytes':base['acceptedAllSharedHistoryIncludingV36Bytes'],'newSharedRuntimeAllFilesBytes':shared,'allCandidateAndAcceptedHistoryBytes':total,'v1Bytes':base['v1Bytes'],'savingVsV1Bytes':base['v1Bytes']-total,'savingVsV37Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'productionIntegrated':False,'referenceAcceptance':False,'nativeAndRuntimeAcceptanceSeparate':True};(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V38_SOURCE_BOUNDS_SEAMS_CONTACT_CLEARANCE_AND_WEIGHT_VERIFIED',len(checks),total,shared,flush=True)
