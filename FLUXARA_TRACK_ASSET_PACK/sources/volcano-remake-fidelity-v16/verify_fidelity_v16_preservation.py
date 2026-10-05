from pathlib import Path
import math,struct,json,sys,hashlib,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v16';c=w/'candidate';old=r/'fidelity-v15/candidate';p=json.loads((w/'terrain-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
alias=Path(p['globalStoneAlias']).name
removed={q['name']:q for q in p['removedUnusedSkyImages']}
for name,row in removed.items():
 assert not(c/name).exists();assert Path(row['preservedOutsideCandidate']).read_bytes()==(old/name).read_bytes();assert hashlib.sha256(Path(row['preservedOutsideCandidate']).read_bytes()).hexdigest()==row['sha256']
clean=lambda v:{k:x for k,x in v.items()if not k.endswith('offset')}
def indexed(b):return collections.Counter(tuple(json.dumps(clean(b['vertices'][j]),sort_keys=True)for j in b['indices'][3*t:3*t+3])for t in range(len(b['indices'])//3))
for name in p['existingStoneModelsAliasOnly']:
 a=parse(old/name);b=parse(c/name);assert a['bounds']==b['bounds'];assert b['materials']==[[alias if n=='Rock13_col.jpg'else n for n in pair]for pair in a['materials']];assert len(a['buffers'])==len(b['buffers'])
 for x,y in zip(a['buffers'],b['buffers']):assert indexed(x)==indexed(y),name
for q in old.iterdir():
 if q.is_file()and q.name not in set(p['existingStoneModelsAliasOnly'])|set(removed)|{'Rock13_col.jpg','scene.xml','materials.xml'}:assert(c/q.name).read_bytes()==q.read_bytes(),q.name
assert Path(p['globalStoneAlias']).read_bytes()==(old/'Rock13_col.jpg').read_bytes();assert not(c/'Rock13_col.jpg').exists();s=E.parse(c/'scene.xml').getroot();added=[e for e in s if e.get('id','').startswith('VRV16_')];assert len(added)==len(p['placements'])
for e in added:s.remove(e)
for e in s.iter():
 if e.get('name')==alias:e.set('name','Rock13_col.jpg')
assert E.tostring(s)==E.tostring(E.parse(old/'scene.xml').getroot());m=E.parse(c/'materials.xml').getroot()
for e in m.iter():
 if e.get('name')==alias:e.set('name','Rock13_col.jpg')
assert E.tostring(m)==E.tostring(E.parse(old/'materials.xml').getroot());protected=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in protected:assert(c/name).read_bytes()==(r/'before'/name).read_bytes()
source=parse(p['sourcePooledModel']);new=parse(p['adaptedSharedModel']);assert source['bounds']==new['bounds'];assert sum(len(b['indices'])//3 for b in new['buffers'])==432;assert all(abs(source['buffers'][i]['vertices'][j]['position'][k]-new['buffers'][i]['vertices'][j]['position'][k])<1e-6 for i in [0,1]for j in range(len(source['buffers'][i]['vertices']))for k in [0,2]);assert E.parse(Path(p['adaptedSharedLibrary'])/'node.xml').getroot().find('object').get('interaction')=='ghost';assert p['adaptedModelWithTextureBytes']<=p['sourceModelWithTextureBytes']*1.2
# The exact enclosing-sphere distance check is independently recomputed against the immutable navigation quads.
code=(r/'build_fidelity_v12_greenery.py').read_text();exec(code[code.index('def bary'):code.index('folder=Path')]);quad=[]
for e in E.parse(c/'quads.xml').getroot().findall('quad'):
 points=[]
 for k in range(4):
  value=e.get('p'+str(k))
  if ':'in value:
   i,j=map(int,value.split(':'));points.append(quad[i][j])
  else:points.append(tuple(map(float,value.split())))
 quad.append(points)
triangles=[t for q in quad for t in [(q[0],q[1],q[2]),(q[0],q[2],q[3])]];minimum=1e20
for row in p['placements']:
 margin=min(point_triangle_distance(row['boundingSphereCentre'],t)for t in triangles)-row['boundingSphereRadius'];minimum=min(minimum,margin);assert margin>=3.5,(row['id'],margin)
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');prod=repo/'iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake'
for q in(r/'fidelity-v2/baseline').iterdir():
 if q.is_file():assert(prod/q.name).read_bytes()==q.read_bytes(),q.name
size=lambda folder:sum(q.stat().st_size for q in folder.rglob('*')if q.is_file());base=json.loads((r/'fidelity-v15/preservation-verification.json').read_text());mapbytes=size(c);newlibbytes=size(Path(p['adaptedSharedLibrary']));total=mapbytes+base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+newlibbytes+base['newGlobalTextureBytes']+Path(p['globalStoneAlias']).stat().st_size;assert total==p['candidateIncludingNewSharedBytes']<p['v1Bytes'];out={'baseCandidate':'V15','allPriorIndexedGeometryUVsNormalsColorsExact':True,'allPriorCollisionAndPlacementGeometryExact':True,'protectedControlBytesExact':protected,'onlySceneAdditionsAndStoneRuntimeTextureAlias':True,'stoneImagePixelsAndOldModelUVsRetained':True,'allRetainedPriorModelsAndImagesByteExact':True,'unusedLegacySkyCopiesRemovedAndArchived':list(removed),'activeSkyIBLAndEffectsRetained':True,'newCliffPlacements':p['newCliffPlacements'],'newCliffBoundingOriginAxesRetainedFromPooledDonor':True,'minimumRoadSphereMarginMeters':p['minimumRoadSphereMarginMeters'],'minimumOriginalNavigationQuadSphereMarginMeters':minimum,'roadAndNavMeshNotCovered':True,'modelWithTextureUpper20PercentPassed':True,'sourceModelWithTextureBytes':p['sourceModelWithTextureBytes'],'adaptedModelWithTextureBytes':p['adaptedModelWithTextureBytes'],'modelWithTextureWeightChangePercent':p['modelWithTextureWeightChangePercent'],'candidateMapBytes':mapbytes,'newSharedLibraryBytesIncludingRetainedHistoricalVariants':base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+newlibbytes,'newGlobalTextureBytes':base['newGlobalTextureBytes']+Path(p['globalStoneAlias']).stat().st_size,'candidateIncludingNewSharedBytes':total,'v1Bytes':p['v1Bytes'],'savingBytesVsV1':p['v1Bytes']-total,'productionStillExactV1':True,'referenceAcceptance':False};(w/'preservation-verification.json').write_text(json.dumps(out,indent=2));print('V16_COURSE_NAVIGATION_AND_WEIGHT_VERIFIED',total,minimum,flush=True)
