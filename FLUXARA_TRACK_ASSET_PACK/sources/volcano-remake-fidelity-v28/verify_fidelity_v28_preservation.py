from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v28';c=w/'candidate';old=r/'fidelity-v27/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
p=json.loads((w/'visible-cliff-changes.json').read_text());before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();ids=[]
def bounds(pp):return [min(q[k]for q in pp)for k in range(3)]+[max(q[k]for q in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
main=parse(c/'volcano_track.spm');road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(q[k]*size[k]+pos[k]for k in range(3))for q in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
boxes=[bounds(t)for t in road];minimum=1e9;checked=0
for group in p['changedGroups']:
    margins=[];deltas=[]
    for prev,current,part in zip(group['before'],group['after'],p['parts']):
        assert before.find(f'library[@id="{prev["id"]}"]').attrib==prev
        assert after.find(f'library[@id="{current["id"]}"]').attrib==current
        assert all(prev[k]==current[k]for k in prev if k!='xyz')
        pos=list(map(float,current['xyz'].split()));orig=list(map(float,prev['xyz'].split()));assert pos[1]==orig[1]
        deltas.append([pos[k]-orig[k]for k in [0,2]]);ids.append(prev['id'])
        s=list(map(float,current['scale'].split()));yaw=math.radians(float(current['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
        world=lambda v:(pos[0]+co*v[0]*s[0]+si*v[2]*s[2],pos[1]+v[1]*s[1],pos[2]-si*v[0]*s[0]+co*v[2]*s[2])
        best=1e9
        for tri in triangles(parse(part['model'])['buffers'][0]):
            pp=[world(v)for v in tri];box=bounds(pp)
            for rb,rt in zip(boxes,road):
                lower=math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))
                if lower<best:best=min(best,triangle_distance(pp,rt))
            checked+=1
        margins.append(best)
    assert max(abs(deltas[0][k]-deltas[1][k])for k in range(2))<1e-7
    assert min(margins)>1 and abs(min(margins)-group['exactAllPartTriangleRoadMarginMeters'])<1e-7
    minimum=min(minimum,min(margins))
assert [E.tostring(e)for e in before if e.get('id')not in ids]==[E.tostring(e)for e in after if e.get('id')not in ids]
assert {f.name for f in old.iterdir()}=={f.name for f in c.iterdir()}
for f in old.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
prev=json.loads((r/'fidelity-v27/preservation-verification.json').read_text());size=lambda folder:sum(f.stat().st_size for f in folder.rglob('*')if f.is_file())
total=size(c)+prev['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+prev['newGlobalTextureBytes'];assert total<prev['v1Bytes']
proof={'baseCandidate':'V27','allCandidateModelsTexturesPhysicsAndGameplayControlsExactV27':True,'allOtherSceneNodesExactV27':True,
    'onlyAddedCliffGrassAndStoneXZCoordinatesChanged':True,'instanceScaleHeightAndYawRetained':True,
    'changedCoordinateGroups':len(p['changedGroups']),'changedPartPlacements':len(ids),'independentlyCheckedMovedPartTriangles':checked,
    'protectedDrivingTriangles':len(road),'independentMovedPartTriangleRoadMarginMeters':minimum,
    'sourceModelLocalGeometryBoundsOriginAxesUnchanged':True,'newModelFiles':0,'newTexturePixels':False,'newMaterials':0,
    'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':prev['newSharedLibraryBytesIncludingRetainedHistoricalVariants'],
    'newGlobalTextureBytes':prev['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,
    'v1Bytes':prev['v1Bytes'],'savingBytesVsV1':prev['v1Bytes']-total,'changeBytesAgainstIntermediateV27':total-prev['candidateIncludingNewSharedBytes'],
    'rejectedV25NotIncluded':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V28_VISIBLE_GROUP_PLACEMENTS_VERIFIED',len(p['changedGroups']),total,minimum,flush=True)
