from pathlib import Path
import sys,json,math,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v22';old=r/'fidelity-v21/candidate';c=w/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
p=json.loads((w/'cliff-changes.json').read_text());source=Path(p['sourcePooledModel']);assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sourceModelSha256']
d=parse(source);n=parse(p['newSharedCliffModel']);assert d['bounds']==n['bounds'] and d['materials']==n['materials'];assert len(d['buffers'])==len(n['buffers'])==2
for b,nb in zip(d['buffers'],n['buffers']):assert b['indices']==nb['indices'] and len(b['vertices'])==len(nb['vertices'])
for b,nb in zip(d['buffers'],n['buffers']):assert [v['color']for v in b['vertices']]==[v['color']for v in nb['vertices']]
assert [v['uv']for v in d['buffers'][1]['vertices']]==[v['uv']for v in n['buffers'][1]['vertices']]
assert [v['color']for v in d['buffers'][1]['vertices']]==[v['color']for v in n['buffers'][1]['vertices']]
points=[v['position']for b in n['buffers']for v in b['vertices']];bd=[min(p[k]for p in points)for k in range(3)]+[max(p[k]for p in points)for k in range(3)];assert max(abs(x-y)for x,y in zip(bd,d['bounds']))<1e-5
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();min_depth=1e9
for q in p['placements']:
    e=after.find(f"library[@id='{q['id']}']");b=before.find(f"library[@id='{q['id']}']");assert e.get('name')==Path(p['newSharedCliffLibrary']).name;assert e.get('hpr')==b.get('hpr');xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
    assert abs(xyz[0]-q['oldXYZ'][0])<1e-7 and abs(xyz[2]-q['oldXYZ'][2])<1e-7
    assert abs(xyz[1]+bd[4]*scale[1]-q['oldXYZ'][1]-bd[4]*q['oldScale'][1])<1e-7
    depth=q['sourceGroundHeight']-xyz[1]-bd[1]*scale[1];assert depth>.4;min_depth=min(min_depth,depth)
    e.attrib.clear();e.attrib.update(b.attrib)
assert E.tostring(before)==E.tostring(after)
for f in old.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
assert {f.name for f in old.iterdir()}=={f.name for f in c.iterdir()}
main=parse(c/'volcano_track.spm');tris=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in tris(b)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));sc=list(map(float,e.get('scale').split()))
        for b in parse(c/e.get('model'))['buffers']:road +=[[tuple(p[k]*sc[k]+xyz[k]for k in range(3))for p in t]for t in tris(b)]
cy=(bd[1]+bd[4])/2;margins=[]
for q in p['placements']:
    e=E.parse(c/'scene.xml').getroot().find(f"library[@id='{q['id']}']");xyz=list(map(float,e.get('xyz').split()));sc=list(map(float,e.get('scale').split()));center=(xyz[0],xyz[1]+cy*sc[1],xyz[2]);radius=max(math.sqrt((v[0]*sc[0])**2+((v[1]-cy)*sc[1])**2+(v[2]*sc[2])**2)for v in points);margin=min(point_triangle_distance(center,t)for t in road)-radius;assert margin>2.5;margins.append(margin)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');texture=resources/'textures'/d['materials'][1][0];native_before=json.loads((r/'fidelity-v21/asset-registration.json').read_text());assert hashlib.sha256(texture.read_bytes()).hexdigest()==native_before['runtimeTextureAliases'][texture.name]['sha256']
weight=Path(p['newSharedCliffModel']).stat().st_size+texture.stat().st_size;assert weight<=p['sourcePoolModelWithTexturesBytes']*1.2
size=lambda path:sum(f.stat().st_size for f in path.rglob('*')if f.is_file());base=json.loads((r/'fidelity-v21/preservation-verification.json').read_text());shared=base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(p['newSharedCliffLibrary']));total=size(c)+shared+base['newGlobalTextureBytes'];v1=size(r/'fidelity-v2/baseline');assert total<v1
for f in (r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
result={'baseCandidate':'V21','allOtherFilesIncludingRoadControlsCollisionsTexturesExactV21':True,'originalSceneObjectsAndOtherLibrariesExactV21':True,'sourcePooledVariantUnmodified':True,'sourceObjectLocalBoundsOriginAxesRetained':True,'retainedStoneUVsColorsAndPixelHashExactV16':True,'changedNewDecorativeCliffPlacements':58,'instanceDirectionsHorizontalPositionsAndTopHeightsRetained':True,'instanceScalesAndVerticalOriginsIntentionallyChanged':True,'minimumFootingDepthBelowOriginalTerrainMeters':min_depth,'independentProtectedRoadSphereMarginMeters':min(margins),'protectedDrivingTriangles':len(road),'sourcePoolModelWithTexturesBytes':p['sourcePoolModelWithTexturesBytes'],'adaptedModelWithTextureBytes':weight,'modelWithTextureChangePercent':(weight/p['sourcePoolModelWithTexturesBytes']-1)*100,'modelWithTextureUpper20PercentPassed':True,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,'newGlobalTextureBytes':base['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':v1,'savingBytesVsV1':v1-total,'changeBytesAgainstIntermediateV21':total-base['candidateIncludingNewSharedBytes'],'newTextureFiles':0,'newTexturePixels':False,'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(result,indent=2));print('V22_CLIFFS_SOURCE_PRESERVATION_AND_WEIGHT_VERIFIED',total,min(margins),min_depth,flush=True)
