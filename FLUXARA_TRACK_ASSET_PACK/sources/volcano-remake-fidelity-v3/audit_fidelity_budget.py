from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as E

r=Path(__file__).resolve().parent
work=r/'fidelity-v2'
repo=Path('/Users/motoricallc/Downloads/fluxara-drift')
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
tri=lambda p:sum(len(b['indices'])//3 for b in parse(p)['buffers'])
size=lambda folder:sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
def library_triangles(name,depth=0):
    assert depth<8
    folder=repo/'iosApp/FluxaraResources/library'/name
    node=E.parse(folder/'node.xml').getroot()
    models=[q.get('model') for q in node.findall('object') if q.get('model') and q.get('interaction') not in ['physicsonly','physics-only']]
    models += [list(g)[0].get('model') for g in node.findall('./lod/group') if len(g)]
    return sum(tri(folder/n) for n in models)+sum(library_triangles(q.get('name'),depth+1) for q in node.findall('library'))
def total(folder):
    node=E.parse(folder/'scene.xml').getroot()
    return (tri(folder/'volcano_track.spm')+
            sum(tri(folder/q.get('model')) for q in node.findall('./track/static-object')+node.findall('object') if q.get('model'))+
            sum(library_triangles(q.get('name')) for q in node.findall('library')))
before=total(r/'before')
previous=total(work/'baseline')
new=total(work/'candidate')
assert new-previous==6
original_bytes=size(r/'before')
old_bytes=size(work/'baseline')
new_bytes=size(work/'candidate')
assert new_bytes<old_bytes<original_bytes
assert .8*before<=new<=1.2*before
proof={'originalBytes':original_bytes,'previousTrackBytes':old_bytes,
       'candidateTrackBytes':new_bytes,'newSharedRuntimeBytes':0,
       'newBytesIncludingNewSharedRuntime':new_bytes,
       'savedBytesAgainstPrevious':old_bytes-new_bytes,
       'originalTriangles':before,'previousTriangles':previous,'candidateTriangles':new,
       'triangleChangePercentAgainstOriginal':100*(new/before-1),
       'triangleBudgetPassed':True,'weightDecreased':True,
       'scope':'Highest visual LOD plus all conditional original objects; authoring-only pool and Blender files are outside app payload. No GPU or FPS measurement.',
       'mainModelSha256':hashlib.sha256((work/'candidate/volcano_track.spm').read_bytes()).hexdigest()}
(work/'budget.json').write_text(json.dumps(proof,indent=2))
print('FIDELITY_BUDGET_VERIFIED',json.dumps(proof))
