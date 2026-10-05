from pathlib import Path
import hashlib,json,math,sys,collections,struct,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v23';old=r/'fidelity-v22/candidate';c=w/'candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
from terrain_triangle_distance import triangle_distance,check_triangle_distance_geometry
check_triangle_distance_geometry()
p=json.loads((w/'backdrop-changes.json').read_text());source=Path(p['sourcePooledModel']);made=Path(p['newSharedTerrainModel'])
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(source)==p['sourcePooledModelSha256']
a=parse(source);b=parse(made);av=a['buffers'][0];bv=b['buffers'][0]
attrs=lambda v:{k:q for k,q in v.items()if not k.endswith('offset')}
assert [attrs(v)for v in av['vertices']]==[attrs(v)for v in bv['vertices'][:len(av['vertices'])]]
removed=set(p['removedSourceTriangleIds'])
kept=[i for t in range(len(av['indices'])//3)if t not in removed for i in av['indices'][3*t:3*t+3]]
assert list(bv['indices'][:len(kept)])==kept
assert all(i>=len(av['vertices'])for i in bv['indices'][len(kept):])
helper=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct}
exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
original=parse(r/'fidelity-v19/candidate/volcano_track.spm')['buffers'][5];groups=ns['component_triangles'](original)
sourceedges=collections.Counter(tuple(sorted((tuple(original['vertices'][a]['position']),tuple(original['vertices'][b]['position']))))for g in [8,9]for t in groups[g]for a,b in [(original['indices'][3*t],original['indices'][3*t+1]),(original['indices'][3*t+1],original['indices'][3*t+2]),(original['indices'][3*t+2],original['indices'][3*t])])
segments=[edge for edge,n in sourceedges.items()if n==1]
newedges=collections.Counter(tuple(sorted((a,b)))for j in range(len(kept),len(bv['indices']),3)for a,b in [(bv['indices'][j],bv['indices'][j+1]),(bv['indices'][j+1],bv['indices'][j+2]),(bv['indices'][j+2],bv['indices'][j])])
assert all(n in [1,2]for n in newedges.values())
def segmentdistance(q,a,b):
    v=[b[k]-a[k]for k in range(3)];length=sum(x*x for x in v)
    t=max(0,min(1,sum((q[k]-a[k])*v[k]for k in range(3))/length))if length else 0
    return math.sqrt(sum((q[k]-a[k]-t*v[k])**2 for k in range(3)))
boundarymargin=max(min(segmentdistance(bv['vertices'][i]['position'],a,b)for a,b in segments)for edge,n in newedges.items()if n==1 for i in edge)
assert boundarymargin<.0001,boundarymargin
assert a['bounds']==b['bounds']and a['materials']==b['materials']
def bounds(pp):return [min(q[k]for q in pp)for k in range(3)]+[max(q[k]for q in pp)for k in range(3)]
active=bounds([bv['vertices'][i]['position']for i in bv['indices']]);assert max(abs(x-y)for x,y in zip(active,a['bounds']))<1e-4
assert len(bv['indices'])//3==p['newTerrainTriangles']
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot()
q=after.find('library[@id="VRV20_RoundedGreenTerrain_000"]');assert q.get('name')==Path(p['newSharedTerrainLibrary']).name
q.set('name',source.parent.name);assert E.tostring(before)==E.tostring(after)
assert {f.name for f in old.iterdir()}=={f.name for f in c.iterdir()}
for f in old.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
main=parse(c/'volcano_track.spm')
triangles=lambda buf:[[buf['vertices'][i]['position']for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)]
protected=[t for buf in main['buffers']if main['materials'][buf['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(buf)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0'
        xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        protected += [[tuple(q[k]*scale[k]+xyz[k]for k in range(3))for q in t]for buf in parse(c/e.get('model'))['buffers']for t in triangles(buf)]
rb=[bounds(t)for t in protected];margin=1e9
for j in range(len(kept),len(bv['indices']),3):
    points=[bv['vertices'][i]['position']for i in bv['indices'][j:j+3]];bd=bounds(points)
    for box,t in zip(rb,protected):
        distance=math.sqrt(sum(max(bd[k]-box[k+3],box[k]-bd[k+3],0)**2 for k in range(3)))
        if distance<margin:margin=min(margin,triangle_distance(points,t))
assert margin>4.5 and len(protected)==2032
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
palette=resources/'textures'/b['materials'][0][0]
assert sha(palette)=='a88393c638eb83032cd902251fe5d11d581d2a64565ec658e116e2c8dd282554'
stone=resources/'textures/fluxara_volcano_stone_shared_v16.jpg';assert sha(stone)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
p20=json.loads((r/'fidelity-v20/preservation-verification.json').read_text())
fullweight=made.stat().st_size+(c/'vr_v20_original_green_collision.spm').stat().st_size+palette.stat().st_size
assert fullweight<=p20['originalComponentWithTextureBytes']*1.2
size=lambda f:sum(p.stat().st_size for p in f.rglob('*')if p.is_file())
previous=json.loads((r/'fidelity-v22/preservation-verification.json').read_text())
shared=previous['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(p['newSharedTerrainLibrary']))
total=size(c)+shared+previous['newGlobalTextureBytes'];assert total<previous['v1Bytes']
for f in (r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
proof={'baseCandidate':'V22','allOtherCandidateFilesIncludingGeometryCollisionsControlsAndTexturesExactV22':True,'onlySceneLibraryNameChanged':True,'existingTerrainVerticesAndAllKeptIndexedAttributesExact':True,'retainedV20TerrainFaces':len(kept)//3,'wholeModelActiveBoundsOriginAxesAndInstanceTransformRetained':True,'originalNarrowRoadsideStripsUnchanged':True,'sourceBoundaryMaximumPositionErrorMeters':boundarymargin,'newTerrainTriangles':len(bv['indices'])//3,'protectedDrivingTriangles':len(protected),'independentAllNewFaceRoadTriangleMarginMeters':margin,'sourcePooledModelUnmodified':True,'stoneUVsAndTexturePixelsUnchanged':True,'newTexturePixels':False,'newMaterialCount':0,'newTextureFiles':0,'originalComponentWithTextureBytes':p20['originalComponentWithTextureBytes'],'adaptedVisibleAndOriginalCollisionWithTextureBytes':fullweight,'modelWithTextureChangePercent':(fullweight/p20['originalComponentWithTextureBytes']-1)*100,'modelWithTextureUpper20PercentPassed':True,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,'newGlobalTextureBytes':previous['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':previous['v1Bytes'],'savingBytesVsV1':previous['v1Bytes']-total,'changeBytesAgainstIntermediateV22':total-previous['candidateIncludingNewSharedBytes'],'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V23_BACKDROP_PRESERVATION_VERIFIED',total,margin,fullweight,flush=True)
