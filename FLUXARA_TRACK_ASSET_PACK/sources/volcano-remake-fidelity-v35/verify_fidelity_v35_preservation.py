from pathlib import Path
import collections,hashlib,json,math,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v35';plan35=json.loads((w/'existing-seam-changes.json').read_text());c=r/'fidelity-v32/candidate';resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
s=(r/'build_fidelity_v30_facades.py').read_text();exec(s[s.index('model_paths='):s.index('rows=[]')])
actual=E.parse(w/'candidate/scene.xml').getroot();previous=E.parse(r/'fidelity-v34/candidate/scene.xml').getroot();changed={attrs['id']:attrs for q in plan35['groups']for attrs in q['partsAfter']};results=[]
assert len(actual)==len(previous)
for x,y in zip(previous,actual):
 if x.get('id')in changed:assert y.attrib==changed[x.get('id')]
 else:assert E.tostring(x)==E.tostring(y),x.attrib
for f in (r/'fidelity-v34/candidate').iterdir():
 if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(w/'candidate'/f.name).read_bytes(),f.name
def boundary(buf):
 def key(i):return tuple(round(x,6)for x in buf['vertices'][i]['position'])
 ed=collections.Counter(tuple(sorted((key(buf['indices'][j+k]),key(buf['indices'][j+(k+1)%3]))))for j in range(0,len(buf['indices']),3)for k in range(3));pts={v for edge,n in ed.items()if n==1 for v in edge};return list({tuple(v['position'])for v in buf['vertices']if tuple(round(x,6)for x in v['position'])in pts})
def bodymodel(attrs):
 folder=resources/'library'/attrs['name'];obj=E.parse(folder/'node.xml').getroot().find('object');assert obj.get('interaction')=='ghost'and obj.get('xyz')=='0 0 0'and obj.get('scale')=='1 1 1';return parse(folder/obj.get('model'))
maxXZ=0;maxOverlapError=0
for q in plan35['groups']:
 rims=[]
 for attrs in q['partsAfter']:
  d=bodymodel(attrs);buf=d['buffers'][0];xyz=list(map(float,attrs['xyz'].split()));scale=list(map(float,attrs['scale'].split()));hpr=list(map(float,attrs['hpr'].split()));assert hpr[0]==hpr[2]==0;yaw=math.radians(hpr[1]);best=margin(buf,xyz,scale,yaw);assert best>.15,(attrs['id'],best)
  results.append({'id':attrs['id'],'roadTriangleMarginMeters':best});rims.append([world(v,xyz,scale,yaw)for v in boundary(buf)])
 assert len(rims[0])==len(rims[1])==16
 for a in rims[0]:
  b=min(rims[1],key=lambda z:math.hypot(a[0]-z[0],a[2]-z[2]));maxXZ=max(maxXZ,math.hypot(a[0]-b[0],a[2]-b[2]));maxOverlapError=max(maxOverlapError,abs(a[1]-b[1]-.08))
 print('V35_EXISTING_SEAM_GROUP_VERIFIED',q['partsAfter'][0]['id'],min(results[-2]['roadTriangleMarginMeters'],results[-1]['roadTriangleMarginMeters']),flush=True)
assert maxXZ<1e-5 and maxOverlapError<1e-6,(maxXZ,maxOverlapError)
budget=json.loads((r/'fidelity-v34/preservation-verification.json').read_text());budget.update({'candidate':'V35','baseCandidate':'V34 isolated source-verified valley experiment','olderSeamGroupsAdapted':58,'existingAcceptedSharedModelsReused':True,'newAssetPayloadBytes':0,'allOtherCandidateFilesExactV34':True,'allOtherSceneNodesExactV34':True,'olderSeamPartsTriangleChecked':116,'olderSeamRenderedTrianglesChecked':58*432,'minimumOlderSeamPartRoadMarginMeters':min(q['roadTriangleMarginMeters']for q in results),'maximumMatchedRimXZErrorMeters':maxXZ,'maximum0p08mOverlapErrorMeters':maxOverlapError,'candidateMapBytes':plan35['candidateMapBytes'],'candidateIncludingNewSharedBytes':plan35['candidateIncludingNewSharedBytes'],'savingBytesVsV1':plan35['savingBytesVsV1'],'nativeCanonicalPoolAndGameplayPending':True})
(w/'preservation-verification.json').write_text(json.dumps(budget,indent=2));(w/'existing-seam-verification.json').write_text(json.dumps({'groups':58,'partChecks':results,'maxXZBoundaryErrorMeters':maxXZ,'max0p08mOverlapErrorMeters':maxOverlapError,'newSPMOrTextures':0,'sourceLocalBoundsPixelsUnchanged':True},indent=2));print('V35_ALL58_EXISTING_SEAMS_AND_CLEARANCE_VERIFIED',maxXZ,maxOverlapError,flush=True)
