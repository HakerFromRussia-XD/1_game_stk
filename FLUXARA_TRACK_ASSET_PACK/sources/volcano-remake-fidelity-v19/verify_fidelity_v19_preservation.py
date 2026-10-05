from pathlib import Path
import json, sys, collections, math, hashlib

r = Path(__file__).resolve().parent
w = r/'fidelity-v19'; c = w/'candidate'; old = r/'fidelity-v18/candidate'
sys.path.insert(0, str(r.parent/'shared-object-redesign'))
from spm_io import parse
proof = json.loads((w/'smoke-changes.json').read_text())
models = {q['model'] for q in proof['smoke']}
assert models == {'AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm'}
assert {p.name for p in c.iterdir()} == {p.name for p in old.iterdir()}
for p in old.iterdir():
    if p.is_file() and p.name not in models:
        assert (c/p.name).read_bytes() == p.read_bytes(), p.name
for q in proof['smoke']:
    x, y = parse(old/q['model']), parse(c/q['model'])
    assert x['bounds'] == y['bounds'] and x['materials'] == y['materials']
    b = y['buffers'][0]
    assert len(y['buffers']) == 1
    assert all(math.isfinite(z) for v in b['vertices'] for z in v['position'])
    extrema = [min(v['position'][k] for v in b['vertices']) for k in range(3)] + [max(v['position'][k] for v in b['vertices']) for k in range(3)]
    assert max(abs(a-b) for a,b in zip(extrema,x['bounds'])) < .0001
    edges = collections.Counter(); graph = collections.defaultdict(set); volume = 0.
    for i in range(0,len(b['indices']),3):
        a,z,f = b['indices'][i:i+3]
        assert len({a,z,f}) == 3
        for e,g in [(a,z),(z,f),(f,a)]:
            edges[tuple(sorted((e,g)))] += 1
            graph[e].add(g); graph[g].add(e)
        v, u, t = [b['vertices'][j]['position'] for j in [a,z,f]]
        volume += sum(v[k]*(u[(k+1)%3]*t[(k+2)%3]-u[(k+2)%3]*t[(k+1)%3]) for k in range(3))/6
    assert set(edges.values()) == {2}
    unseen = set(graph); count = 0
    while unseen:
        count += 1; stack = [unseen.pop()]
        while stack:
            v = stack.pop()
            for n in graph[v]:
                if n in unseen: unseen.remove(n); stack.append(n)
    assert count == 1 and volume > 0, (q['model'], count, volume)
    tex = c/y['materials'][0][0]
    assert hashlib.sha256(tex.read_bytes()).hexdigest() == q['paletteSha256']
    assert q['adaptedBytesWithTexture'] == (c/q['model']).stat().st_size+tex.stat().st_size
    assert q['sourceBytesWithTexture'] == (r/'fidelity-v2/baseline'/q['model']).stat().st_size+tex.stat().st_size
    assert q['adaptedBytesWithTexture'] <= q['sourceBytesWithTexture']*1.2
    q.update({'independentConnectedComponents': count, 'independentClosedSurfaceVerified': True,
               'outwardSignedVolume': volume, 'modelWithTextureUpper20PercentPassed': True})
resources = Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
size = lambda p: sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
b = json.loads((r/'fidelity-v18/preservation-verification.json').read_text())
result = {'baseCandidate':'V18','smoke':proof['smoke'],'allOtherModelTextureSceneAndControlBytesExactV18':True,
          'originalStoneImageUVsAndGeometryUnchanged':True,'allOriginalPhysicsAndGameplayControlsUnchanged':True,
          'cloudCentersAxesActualLocalBoundsAndGhostPlacementsUnchanged':True,'newImagePixels':False,
          'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':b['newSharedLibraryBytesIncludingRetainedHistoricalVariants'],
          'newGlobalTextureBytes':b['newGlobalTextureBytes'],'productionIntegrated':False,'referenceAcceptance':False}
result['candidateIncludingNewSharedBytes'] = result['candidateMapBytes']+result['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+result['newGlobalTextureBytes']
result['v1Bytes'] = size(r/'fidelity-v2/baseline')
result['savingBytesVsV1'] = result['v1Bytes']-result['candidateIncludingNewSharedBytes']
assert result['savingBytesVsV1'] > 0
for p in (r/'fidelity-v2/baseline').iterdir():
    if p.is_file(): assert p.read_bytes() == (resources/'tracks/fluxara-user-volcano-remake'/p.name).read_bytes()
result['productionStillExactV1'] = True
(w/'preservation-verification.json').write_text(json.dumps(result,indent=2))
print('V19_CLOSED_CONNECTED_SMOKE_AND_ALL_OTHER_BYTES_VERIFIED',result['candidateIncludingNewSharedBytes'],flush=True)
