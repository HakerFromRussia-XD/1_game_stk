from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent; w=r/'fidelity-v25'; c=w/'candidate'; old=r/'fidelity-v24/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign')); from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
p=json.loads((w/'cliff-changes.json').read_text()); source=Path(p['sourceModel']); sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(source)==p['sourceModelSha256']
a=parse(source); b=parse(c/'volcano_track.spm'); sourcebuf=a['buffers'][3]
attrs=lambda v:{k:q for k,q in v.items() if not k.endswith('offset')}
for i,bb in enumerate(b['buffers']):
    aa=a['buffers'][i if i<3 else i+1]
    assert aa['indices']==bb['indices'] and aa['material']==bb['material']
    assert [attrs(v)for v in aa['vertices']]==[attrs(v)for v in bb['vertices']],i
assert a['materials']==b['materials'] and a['bounds']==b['bounds']
made=parse(p['newSharedModel']); mb=made['buffers'][0]; original=parse(p['originalCollider']); ob=original['buffers'][0]
assert ob['indices']==sourcebuf['indices']
assert all(x['position']==y['position'] and x['normal']==y['normal'] for x,y in zip(ob['vertices'],sourcebuf['vertices']))
assert len(ob['vertices'])==len(sourcebuf['vertices'])
assert [attrs(v) for v in mb['vertices'][:len(sourcebuf['vertices'])]]==[dict(attrs(v),**{})for v in sourcebuf['vertices']]
cert=json.loads((w/'road-clearance-certificates.json').read_text())
kept=p['retainedSourceTriangles']; assert len(mb['indices'])//3==p['targetTriangles'] and len(cert)==p['targetTriangles']-kept
helper=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':__import__('struct')}
exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
groups=ns['component_triangles'](sourcebuf); target=set(groups[8]+groups[9])
assert list(mb['indices'][:kept*3])==[i for t in range(2210)if t not in target for i in sourcebuf['indices'][3*t:3*t+3]]
def bounds(pp):return [min(q[k]for q in pp)for k in range(3)]+[max(q[k]for q in pp)for k in range(3)]
sourcebox=bounds([sourcebuf['vertices'][i]['position']for i in sourcebuf['indices']])
activebox=bounds([mb['vertices'][i]['position']for i in mb['indices']]); assert max(abs(x-y)for x,y in zip(activebox,sourcebox))<1e-4
triangles=lambda buf:[[buf['vertices'][i]['position']for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)]
road=[t for buf in a['buffers']if a['materials'][buf['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(buf)]
before=E.parse(old/'scene.xml').getroot(); after=E.parse(c/'scene.xml').getroot()
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        road += [[tuple(q[k]*scale[k]+xyz[k]for k in range(3))for q in t]for buf in parse(old/e.get('model'))['buffers']for t in triangles(buf)]
assert len(road)==2032; boxes=[bounds(t)for t in road]
lowerbound=1e9; changed=0; checkedparents={}
for j,q in enumerate(cert):
    assert list(mb['indices'][3*(kept+j):3*(kept+j+1)])==q['indices']
    parent=q['parentLinearTriangle']; baseline=q['baselineCorners']; points=[mb['vertices'][i]['position']for i in q['indices']]
    assert max(point_triangle_distance(v,parent)for v in baseline)<1e-4
    delta=max(math.dist(x,y)for x,y in zip(points,baseline))
    if delta<1e-5:continue
    key=tuple(tuple(x)for x in parent)
    if key not in checkedparents:
        box=bounds(parent)
        checkedparents[key]=min(math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))for rb in boxes)
    lower=checkedparents[key]-delta; assert lower>4.998,lower
    lowerbound=min(lowerbound,lower);changed+=1
assert changed>1000
for name in ['VRV25_RoundedStoneWalls_000','VRV25_OriginalStoneWallsCollision']:
    e=next(e for e in after if e.get('id')==name)
    assert e.get('xyz')=='0 0 0'and e.get('hpr')=='0 0 0'and e.get('scale')=='1 1 1'
    if name.endswith('Collision'):assert e.get('interaction')=='physicsonly'
    else:assert e.tag=='library'and e.get('name')==Path(p['newSharedLibrary']).name
    after.remove(e)
assert E.tostring(before)==E.tostring(after)
for f in old.iterdir():
    if f.is_file()and f.name not in ['volcano_track.spm','scene.xml']:assert f.read_bytes()==(c/f.name).read_bytes(),f.name
assert {f.name for f in c.iterdir()}=={f.name for f in old.iterdir()}|{Path(p['originalCollider']).name}
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
texture=resources/'textures/fluxara_volcano_stone_shared_v16.jpg';assert texture.stat().st_size==39938 and sha(texture)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
originalstone=parse(r/'before/volcano_track.spm')
origbuf=next(buf for buf in originalstone['buffers'] if originalstone['materials'][buf['material']][0]=='Rock13_col.jpg')
# Match only this stone region, excluding the separately handled 427 green faces.
import collections,copy,struct
key=lambda buf,t:tuple(sorted(tuple(round(x,4)for x in buf['vertices'][i]['position'])for i in buf['indices'][3*t:3*t+3]))
need=collections.Counter(key(sourcebuf,t)for t in range(2210));selected=[]
for t in range(len(origbuf['indices'])//3):
    k=key(origbuf,t)
    if need[k]:selected.append(t);need[k]-=1
assert len(selected)==2210 and not any(need.values())
used=sorted({i for t in selected for i in origbuf['indices'][3*t:3*t+3]}); remap={i:j for j,i in enumerate(used)}
vv=[origbuf['vertices'][i]for i in used];ii=[remap[i]for t in selected for i in origbuf['indices'][3*t:3*t+3]]
assert originalstone['flags'] in [1,3]
raw=bytearray(b'SP'+bytes([10,originalstone['flags']])+struct.pack('<6f',*sourcebox)+struct.pack('<H',1))
raw+=bytes([len('Rock13_col.jpg')])+b'Rock13_col.jpg'+bytes([0])+struct.pack('<HHIIH',1,1,len(vv),len(ii),0)
for v in vv:
    raw+=struct.pack('<3fI',*v['position'],v['normal'])
    if originalstone['flags']&2:
        color=tuple(v.get('color',(255,255,255)));raw+=b'\x80'if color==(255,255,255)else b'\xff'+bytes(color)
    raw+=struct.pack('<2e',*v['uv'])
raw+=struct.pack('<'+str(len(ii))+('H'if len(vv)>255 else 'B'),*ii)
matched=w/'original-stone-region-before.spm';matched.write_bytes(raw)
assert len(parse(matched)['buffers'][0]['indices'])//3==2210
originalweight=matched.stat().st_size+(r/'before/Rock13_col.jpg').stat().st_size
weight=Path(p['newSharedModel']).stat().st_size+Path(p['originalCollider']).stat().st_size+texture.stat().st_size
assert weight<=1.2*originalweight
size=lambda f:sum(q.stat().st_size for q in f.rglob('*')if q.is_file())
previous=json.loads((r/'fidelity-v24/preservation-verification.json').read_text())
shared=previous['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(p['newSharedLibrary']))
total=size(c)+shared+previous['newGlobalTextureBytes'];assert total<previous['v1Bytes']
for f in (r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
proof={'baseCandidate':'V24','allOtherMainBuffersIndexedAttributesExactV24':True,'allOtherCandidateFilesExactV24':True,
    'sourceStoneCollisionPositionsNormalsAndIndicesExact':True,'existingSceneNodesExactV24':True,
    'wholeStoneActiveBoundsAndIdentityTransformRetained':True,'retainedUnmodifiedStoneTriangles':kept,
    'newStoneTriangles':p['targetTriangles'],'changedDecorativeTriangles':changed,'protectedDrivingTriangles':2032,
    'independentChangedTriangleRoadDistanceLowerBoundMeters':lowerbound,
    'distanceProof':'Each displaced triangle stays within maximum corner displacement of its original planar subdivided triangle; subtract displacement from original triangle-AABB distance to all road AABBs.',
    'stonePixelsRetained':True,'sourceUVsRetainedNewUVsInterpolated':True,'newTexturePixels':False,'newMaterials':0,
    'originalStoneRegionWithOriginalTextureBytes':originalweight,'adaptedModelOriginalCollisionAndStoneTextureBytes':weight,
    'modelWithTextureChangePercent':(weight/originalweight-1)*100,'modelWithTextureUpper20PercentPassed':True,
    'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,
    'newGlobalTextureBytes':previous['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,
    'v1Bytes':previous['v1Bytes'],'savingBytesVsV1':previous['v1Bytes']-total,
    'changeBytesAgainstIntermediateV24':total-previous['candidateIncludingNewSharedBytes'],
    'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2))
print('V25_MAIN_CLIFF_GEOMETRY_AND_BUDGET_VERIFIED',total,changed,lowerbound,flush=True)
