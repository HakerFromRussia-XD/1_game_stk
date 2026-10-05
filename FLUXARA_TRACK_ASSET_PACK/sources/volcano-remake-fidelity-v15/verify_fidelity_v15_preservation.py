from pathlib import Path
import json,sys,math,struct,hashlib,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';old=r/'fidelity-v14/candidate';c=w/'candidate';proof=json.loads((w/'castle-atmosphere-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
alias=Path(proof['globalBrickTexture']).name;removed={int(i):set(ts)for i,ts in proof['mainRemovalTriangleIdsByBuffer'].items()}
def attrs(v):return {k:x for k,x in v.items()if not k.endswith('offset')}
def full(b,omit=set()):return collections.Counter(tuple(json.dumps(attrs(b['vertices'][j]),sort_keys=True)for j in b['indices'][3*t:3*t+3])for t in range(len(b['indices'])//3)if t not in omit)
def pos(b,ts=None):return collections.Counter(tuple(tuple(b['vertices'][j]['position'])for j in b['indices'][3*t:3*t+3])for t in (range(len(b['indices'])//3)if ts is None else ts))
before=parse(old/'volcano_track.spm');after=parse(c/'volcano_track.spm');assert before['bounds']==after['bounds'];assert [[alias if n=='castelwall.jpg'else n for n in pair]for pair in before['materials']]==after['materials'];assert len(before['buffers'])==len(after['buffers'])
for i,(x,y)in enumerate(zip(before['buffers'],after['buffers'])):assert full(x,removed.get(i,set()))==full(y),i
collisions=0
for q in proof['additionalTowerPlacements']:
 original=collections.Counter()
 for i,ts in q['removedTriangleIdsByBuffer'].items():original+=pos(before['buffers'][int(i)],ts)
 d=parse(c/q['collider']);assert pos(d['buffers'][0])==original;collisions+=len(d['buffers'][0]['indices'])//3
 # Exact visible bounds for the composite, original center and axes remain unchanged.
 bds=proof['towerCompositeBounds'];lo,hi=q['originalVisualBounds'];made=[[q['xyz'][k]+bds[k+3*a]*q['scale'][k]for k in range(3)]for a in [0,1]]
 assert max(abs(made[a][k]-[lo,hi][a][k])for a in [0,1]for k in range(3))<1e-4,q['id']
 assert E.parse(c/'scene.xml').getroot().find(f"object[@model='{q['collider']}']").get('interaction')=='physicsonly'
source=parse(r/'before/volcano_track.spm');road=lambda d:next(b for b in d['buffers']if d['materials'][b['material']][0]=='track01.png');assert full(road(source))==full(road(after))
protected=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for n in protected:assert(c/n).read_bytes()==(r/'before'/n).read_bytes()
s=E.parse(c/'scene.xml').getroot()
for e in list(s):
 if e.get('id','').startswith('VRV15_'):s.remove(e)
 if e.get('id')in ['VRV8_PooledTower_0','VRV8_PooledTower_1']:e.set('name','fluxara_driftlib_volcano_castle_tower_v9')
for e in s.iter():
 if e.get('name')==alias:e.set('name','castelwall.jpg')
assert E.tostring(s)==E.tostring(E.parse(old/'scene.xml').getroot())
m=E.parse(c/'materials.xml').getroot()
for e in m.iter():
 if e.get('name')==alias:e.set('name','castelwall.jpg')
assert E.tostring(m)==E.tostring(E.parse(old/'materials.xml').getroot())
smoke={q['model']for q in proof['smoke']};changed=set(proof['brickAliasOnlyModels'])|{'volcano_track.spm','scene.xml','materials.xml','castelwall.jpg'}|smoke
for p in old.iterdir():
 if p.is_file()and p.name not in changed:assert(c/p.name).read_bytes()==p.read_bytes(),p.name
for name in set(proof['brickAliasOnlyModels'])-{'volcano_track.spm'}:
 x=parse(old/name);y=parse(c/name);assert [full(b)for b in x['buffers']]==[full(b)for b in y['buffers']],name
for q in proof['smoke']:
 assert parse(old/q['model'])['bounds']==parse(c/q['model'])['bounds'];tex=parse(c/q['model'])['materials'][0][0];assert(c/tex).read_bytes()==(old/tex).read_bytes();assert(c/q['model']).stat().st_size+(c/tex).stat().st_size<=1.2*((old/q['model']).stat().st_size+(old/tex).stat().st_size)
assert Path(proof['globalBrickTexture']).read_bytes()==(old/'castelwall.jpg').read_bytes()
towerbytes=sum(Path(proof[k]).stat().st_size for k in ['newTowerBody','newTowerRoof','newTowerFlag'])+Path(proof['globalBrickTexture']).stat().st_size;assert towerbytes==proof['allTowerVariantsGeometryWithSharedTextureBytes']<=1.2*proof['sourceModelWithTextureBytes']
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');size=lambda p:sum(f.stat().st_size for f in p.rglob('*')if f.is_file());newlibs=['fluxara_driftlib_volcano_castle_tower_v8b','fluxara_driftlib_volcano_castle_tower_v9','fluxara_driftlib_volcano_fountain_v13','fluxara_driftlib_volcano_castle_body_v15','fluxara_driftlib_volcano_castle_roof_v15','fluxara_driftlib_volcano_castle_battlement_v15','fluxara_driftlib_volcano_gate_roof_v15'];librarybytes=sum(size(res/'library'/n)for n in newlibs);texturebytes=sum((res/'textures'/n).stat().st_size for n in ['fluxara_volcano_lava_shared_v13.jpg',alias]);total=size(c)+librarybytes+texturebytes;v1=size(r/'fidelity-v2/baseline');assert total<v1,(total,v1)
prod=res/'tracks/fluxara-user-volcano-remake'
for p in(r/'fidelity-v2/baseline').iterdir():
 if p.is_file():assert(prod/p.name).read_bytes()==p.read_bytes(),p.name
gate=proof['newGateRoofOptimization'];assert gate['gatewayWithAddedRoofModelAndSameTextureBytes']<=1.2*gate['existingGatewayComponentWithTextureBytes'];assert Path(proof['newGateRoofModel']).stat().st_size==gate['modelBytesAfter'];assert gate['trianglesAfter']==len(parse(proof['newGateRoofModel'])['buffers'][0]['indices'])//3
result={'gateModelWithTextureChangePercent':gate['changePercent'],'gateModelWithTextureUpper20PercentPassed':True,'baseCandidate':'V14','originalRoadIndexedAttributesExact':True,'protectedControlBytesExact':protected,'retainedMainIndexedTriangleAttributesExact':True,'originalTowerCollisionTrianglesExact':collisions,'additionalTowerPlacements':len(proof['additionalTowerPlacements']),'towerCentersAxesCompositeBoundsRetained':True,'cloudLocalBoundsAndTransformsRetained':True,'onlyOldBrickPixelsUsed':True,'stoneImageAndOldCliffGeometryUVsExactV14':True,'towerAllVariantsModelWithTextureBytesBefore':proof['sourceModelWithTextureBytes'],'towerAllVariantsModelWithTextureBytesAfter':towerbytes,'towerModelWithTextureChangePercent':(towerbytes/proof['sourceModelWithTextureBytes']-1)*100,'modelWithTextureUpper20PercentPassed':True,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':librarybytes,'newGlobalTextureBytes':texturebytes,'candidateIncludingNewSharedBytes':total,'v1Bytes':v1,'savingBytesVsV1':v1-total,'productionStillExactV1':True,'visualReferenceAcceptance':False};(w/'preservation-verification.json').write_text(json.dumps(result,indent=2));print('V15_PRESERVATION_AND_WEIGHT_VERIFIED',total,v1-total)
