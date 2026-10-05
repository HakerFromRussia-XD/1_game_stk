from pathlib import Path
import collections,hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v29';c=w/'candidate';previous=r/'fidelity-v28/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
p=json.loads((w/'stone-foot-changes.json').read_text());source=Path(p['sourceModel']);model=Path(p['newSharedModel']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(source)==p['sourceModelSha256'];original=parse(source);made=parse(model);a=original['buffers'][0];b=made['buffers'][0]
assert a['indices']==b['indices']and len(a['vertices'])==len(b['vertices'])==95 and len(b['indices'])==456
assert original['materials']==made['materials']and original['bounds']==made['bounds']
changed=0
for old,new in zip(a['vertices'],b['vertices']):
    for key in ['uv','color']:assert old.get(key)==new.get(key)
    assert old['position'][1]==new['position'][1]
    if old['position'][1]>=0:assert old['position']==new['position']and old['normal']==new['normal']
    if old['position']!=new['position']:changed+=1
assert changed==len(p['changedVertices'])
def bounds(pp):return [min(v[k]for v in pp)for k in range(3)]+[max(v[k]for v in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
assert bounds([b['vertices'][i]['position']for i in b['indices']])==list(original['bounds'])
def topology(buf):
    edges=collections.Counter()
    for tri in triangles(buf):
        vv=[tuple(round(x,5)for x in q)for q in tri]
        for i in range(3):edges[tuple(sorted((vv[i],vv[(i+1)%3])))]+=1
    return collections.Counter(edges.values())
assert topology(a)==topology(b)==collections.Counter({2:220,1:16}),topology(b)
def cross(t):
    u=[t[1][k]-t[0][k]for k in range(3)];v=[t[2][k]-t[0][k]for k in range(3)]
    return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
for aa,bb in zip(triangles(a),triangles(b)):
    x,y=cross(aa),cross(bb);assert sum(v*v for v in y)>1e-12
    assert sum(x[k]*y[k]for k in range(3))>0,'Face orientation reversed'
oldscene=E.parse(previous/'scene.xml').getroot();scene=E.parse(c/'scene.xml').getroot();changedids=[]
for q in p['placements']:
    before=oldscene.find(f'library[@id="{q["before"]["id"]}"]');after=scene.find(f'library[@id="{q["after"]["id"]}"]')
    assert before.attrib==q['before']and after.attrib==q['after']
    assert all(before.get(k)==after.get(k)for k in before.attrib if k!='name');changedids.append(before.get('id'))
assert len(changedids)==58
assert [E.tostring(e)for e in oldscene if e.get('id')not in changedids]==[E.tostring(e)for e in scene if e.get('id')not in changedids]
for f in previous.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
assert {f.name for f in previous.iterdir()}=={f.name for f in c.iterdir()}
main=parse(c/'volcano_track.spm');road=[t for buf in main['buffers']if main['materials'][buf['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(buf)]
for e in oldscene.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));s=list(map(float,e.get('scale').split()))
        road += [[tuple(v[k]*s[k]+pos[k]for k in range(3))for v in t]for buf in parse(c/e.get('model'))['buffers']for t in triangles(buf)]
assert len(road)==2032;boxes=[bounds(t)for t in road];minimum=1e9
for q in p['placements']:
    e=q['after'];pos=list(map(float,e['xyz'].split()));s=list(map(float,e['scale'].split()));yaw=math.radians(float(e['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
    world=lambda v:(pos[0]+co*v[0]*s[0]+si*v[2]*s[2],pos[1]+v[1]*s[1],pos[2]-si*v[0]*s[0]+co*v[2]*s[2])
    best=1e9
    for tri in triangles(b):
        tt=[world(v)for v in tri];box=bounds(tt)
        for rb,rt in zip(boxes,road):
            lower=math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))
            if lower<best:best=min(best,triangle_distance(tt,rt))
    assert best>.5 and abs(best-q['exactStoneTriangleRoadMarginMeters'])<1e-5
    minimum=min(minimum,best)
resources=source.parent.parent.parent;texture=resources/'textures/fluxara_volcano_stone_shared_v16.jpg'
assert texture.stat().st_size==39938 and sha(texture)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
weights=[source.stat().st_size+texture.stat().st_size,model.stat().st_size+texture.stat().st_size];assert weights[1]<=weights[0]*1.2
size=lambda folder:sum(f.stat().st_size for f in folder.rglob('*')if f.is_file());prev=json.loads((r/'fidelity-v28/preservation-verification.json').read_text())
shared=prev['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(p['newSharedLibrary']));total=size(c)+shared+prev['newGlobalTextureBytes'];assert total<prev['v1Bytes']
for f in(r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
assert not(resources/'library/fluxara_driftlib_volcano_rounded_walls_v25').exists()
proof={'baseCandidate':'V28','allCandidateModelsPhysicsTexturesAndGameplayControlsExactV28':True,'allOtherSceneNodesExactV28':True,'allAddedInstanceTransformsExactV28':True,'sourcePooledModelUnmodified':True,'sourceLocalActiveBoundsOriginAxesRetained':True,'sourceUVsRGBIndicesRetained':True,'upperHalfPositionsAndNormalsExact':True,'changedLowerVertices':changed,'allTriangleOrientationsRetainedAndNoDegenerateFaces':True,'weldedSharedEdges':220,'sourceOpenTopBoundaryEdgesRetained':16,'sourceTriangles':152,'targetTriangles':152,'sourceVertices':95,'targetVertices':95,'sourceModelWithTextureBytes':weights[0],'targetModelWithTextureBytes':weights[1],'modelWithTextureUpper20PercentPassed':True,'protectedDrivingTriangles':len(road),'independentAllNewStoneTriangleRoadMarginMeters':minimum,'newMaterials':0,'newTextureFiles':0,'newImagePixels':False,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,'newGlobalTextureBytes':prev['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':prev['v1Bytes'],'savingBytesVsV1':prev['v1Bytes']-total,'changeBytesAgainstIntermediateV28':total-prev['candidateIncludingNewSharedBytes'],'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V29_STONE_FEET_PRESERVATION_VERIFIED',changed,total,minimum,flush=True)
