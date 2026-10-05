from pathlib import Path
import json,math,hashlib,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v27';c=w/'candidate';old=r/'fidelity-v26/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
p=json.loads((w/'column-changes.json').read_text());source=Path(p['sourceModel']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(source)==p['sourceModelSha256'];src=parse(source)
attrs=lambda v:{k:q for k,q in v.items()if not k.endswith('offset')}
sourceweights=[];targetweights=[]
for q in p['parts']:
    b=src['buffers'][q['sourceBuffer']];made=parse(q['model']);bb=made['buffers'][0]
    assert b['indices']==bb['indices']and [attrs(v)for v in b['vertices']]==[attrs(v)for v in bb['vertices']]
    assert made['materials']==[src['materials'][b['material']]]and list(made['bounds'])==q['localBounds']
    start=b['vertices'][0]['offset']-10;end=src['buffers'][1]['vertices'][0]['offset']-10 if q['sourceBuffer']==0 else src['geometry_end']
    texturebytes=39938 if q['part']=='stone_column'else 0
    before=end-start+texturebytes;after=Path(q['model']).stat().st_size+texturebytes;assert after<=before*1.2
    sourceweights.append(before);targetweights.append(after)
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();oldids=[];newids=[]
for q in p['placements']:
    original=before.find(f'library[@id="{q["source"]["id"]}"]');assert original.attrib==q['source'];oldids.append(original.get('id'))
    for part in ['grass','stone']:
        e=after.find(f'library[@id="{q[part]["id"]}"]');assert e.attrib==q[part];newids.append(e.get('id'))
    grass=q['grass'];assert all(grass[k]==q['source'][k]for k in ['xyz','hpr','scale'])
    s=list(map(float,q['stone']['scale'].split()));pos=list(map(float,q['stone']['xyz'].split()));oldscale=list(map(float,q['source']['scale'].split()));oldpos=list(map(float,q['source']['xyz'].split()))
    assert max(abs(s[k]-oldscale[k]*(2.8 if k==1 else .9))for k in range(3))<1e-7
    assert pos[0]==oldpos[0]and pos[2]==oldpos[2]and q['stone']['hpr']==q['source']['hpr']
    assert abs(pos[1]+p['parts'][1]['localBounds'][4]*s[1]-q['sourceStoneTopWorldY'])<1e-7
assert [E.tostring(e)for e in before if e.get('id')not in oldids]==[E.tostring(e)for e in after if e.get('id')not in newids]
assert len(newids)==116 and len(oldids)==58
assert {f.name for f in old.iterdir()}=={f.name for f in c.iterdir()}
for f in old.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
def bounds(pp):return [min(q[k]for q in pp)for k in range(3)]+[max(q[k]for q in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
main=parse(c/'volcano_track.spm');road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(q[k]*size[k]+pos[k]for k in range(3))for q in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
boxes=[bounds(t)for t in road];minimum=1e9
for q in p['placements']:
    e=q['stone'];pos=list(map(float,e['xyz'].split()));s=list(map(float,e['scale'].split()));a=math.radians(float(e['hpr'].split()[1]));co,si=math.cos(a),math.sin(a)
    def world(v):return(pos[0]+co*v[0]*s[0]+si*v[2]*s[2],pos[1]+v[1]*s[1],pos[2]-si*v[0]*s[0]+co*v[2]*s[2])
    best=1e9
    for tri in triangles(src['buffers'][1]):
        pp=[world(v)for v in tri];box=bounds(pp)
        for rb,rt in zip(boxes,road):
            lower=math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))
            if lower<best:best=min(best,triangle_distance(pp,rt))
    assert best>.5 and abs(best-q['exactStoneTriangleRoadMarginMeters'])<1e-7
    minimum=min(minimum,best)
resources=source.parent.parent.parent;texture=resources/'textures/fluxara_volcano_stone_shared_v16.jpg'
assert texture.stat().st_size==39938 and sha(texture)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
previous=json.loads((r/'fidelity-v26/preservation-verification.json').read_text());size=lambda folder:sum(f.stat().st_size for f in folder.rglob('*')if f.is_file())
shared=previous['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+sum(size(Path(q['library']))for q in p['parts'])
total=size(c)+shared+previous['newGlobalTextureBytes'];assert total<previous['v1Bytes']
production=resources/'tracks/fluxara-user-volcano-remake'
for f in (r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(production/f.name).read_bytes()
assert not(resources/'library/fluxara_driftlib_volcano_rounded_walls_v25').exists()
proof={'baseCandidate':'V26','sourceComponentGeometryNormalsUVsColorsAndBoundsExact':True,'sourcePooledModelUnmodified':True,
       'allCandidateModelsPhysicsTexturesControlsExactV26':True,'allOtherSceneNodesExactV26':True,'grassPosesExact':True,
       'stoneInstanceHeightFactor':2.8,'stoneInstanceWidthFactor':.9,'stoneTopWorldYRetained':True,
       'sourceModelDimensionsOriginAxesRetained':True,'stonePlacedWorldDimensionsIntentionallyChanged':True,
       'sharedPartPlacements':116,'originalCombinedPlacements':58,'protectedDrivingTriangles':len(road),
       'independentAllNewStoneTriangleRoadMarginMeters':minimum,'sourceComponentWithTextureBytes':sourceweights,
       'targetComponentWithTextureBytes':targetweights,'modelWithTextureUpper20PercentPassed':True,
       'newAuthoredGeometry':False,'newMaterials':0,'newTextureFiles':0,'newImagePixels':False,
       'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,
       'newGlobalTextureBytes':previous['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,
       'v1Bytes':previous['v1Bytes'],'savingBytesVsV1':previous['v1Bytes']-total,
       'changeBytesAgainstIntermediateV26':total-previous['candidateIncludingNewSharedBytes'],
       'rejectedV25LibraryExcludedFromResources':True,'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V27_TALL_COLUMNS_AND_REUSED_GEOMETRY_VERIFIED',total,minimum,flush=True)
