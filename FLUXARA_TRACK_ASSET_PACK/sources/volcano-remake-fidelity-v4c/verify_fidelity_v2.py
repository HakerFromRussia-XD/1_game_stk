import bpy
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

r = Path(__file__).resolve().parent
sys.path.insert(0, str(r.parent / 'shared-object-redesign'))
from spm_io import parse
work = r/'fidelity-v2'
change = json.loads((work/'changes.json').read_text())
d = parse(work/'candidate/volcano_track.spm')
original = parse(work/'baseline/volcano_track.spm')
arch = d['buffers'][1]
# The last 300 triangles are precisely the new entrance component.
indices = arch['indices'][-900:]
verts = [Vector(v['position']) for v in arch['vertices']]
surface = BVHTree.FromPolygons(verts, [indices[i:i+3] for i in range(0,len(indices),3)])
qs = []
for e in E.parse(work/'candidate/quads.xml').getroot().findall('quad'):
    q=[]
    for k in range(4):
        s=e.get('p'+str(k))
        q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
    qs.append(q)
lo,hi=change['arch']['componentBounds']
tested=[]
hits=[]
for i,q in enumerate(qs):
    if max(p[0] for p in q)<lo[0] or min(p[0] for p in q)>hi[0] or max(p[2] for p in q)<lo[2] or min(p[2] for p in q)>hi[2]:
        continue
    tested.append(i)
    for step in range(41):
        t=step/40
        left=Vector(q[0]).lerp(Vector(q[3]),t)
        right=Vector(q[1]).lerp(Vector(q[2]),t)
        for cross in range(41):
            p=left.lerp(right,cross/40)
            if surface.ray_cast(p+Vector((0,.05,0)),Vector((0,1,0)),3.45)[0]:
                hits.append({'quad':i,'t':t,'cross':cross/40})
assert not hits,hits[:10]
points=[arch['vertices'][i]['position'] for i in indices]
actual=[[min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]]
error=max(abs(a-b) for aa,bb in zip([lo,hi],actual) for a,b in zip(aa,bb))
assert error<.001,error
before=sum(len(b['indices'])//3 for b in original['buffers'])
after=sum(len(b['indices'])//3 for b in d['buffers'])
assert after-before==6
def geometry(b):
    return [tuple((b['vertices'][i]['position'],b['vertices'][i]['normal']) for i in b['indices'][t:t+3])
            for t in range(0,len(b['indices']),3)]
assert sorted(geometry(original['buffers'][2]))==sorted(geometry(d['buffers'][2])+geometry(d['buffers'][3]))
a,b=original['buffers'][5],d['buffers'][6]
assert a['indices']==b['indices']
assert all(v['position']==w['position'] and v['normal']==w['normal'] for v,w in zip(a['vertices'],b['vertices']))
for name in ['scene.xml','track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']:
    assert (work/'baseline'/name).read_bytes()==(work/'candidate'/name).read_bytes(),name
old_mat=E.parse(work/'baseline/materials.xml').getroot()
new_mat=E.parse(work/'candidate/materials.xml').getroot()
assert len(new_mat)==len(old_mat)+1
assert all(E.tostring(a)==E.tostring(b) for a,b in zip(old_mat,new_mat))
assert new_mat[-1].get('name')=='vr_moss_palette.jpg'
assert {k:v for k,v in new_mat[-1].attrib.items() if k!='name'}=={k:v for k,v in next(m for m in old_mat if m.get('name')=='Rock13_col.jpg').attrib.items() if k!='name'}
proof={'newArchBoundsMaxError':error,'newArchRoadClearanceSampled':True,
       'sampledQuadIds':tested,'samples':len(tested)*41*41,'minimumRequiredOverheadMeters':3.5,
       'samplesWithArchGeometryInsideDrivingEnvelope':hits,
       'scope':'Dense vertical sample rays over original quads; not a swept kart-collision proof.',
       'mainTriangleDelta':after-before,'allOtherMainGeometryExact':True,
       'courseGameplaySceneFilesByteExactAgainstPreviousVersion':True,
       'allExistingMaterialDefinitionsExact':True,'newMossMaterialCopiesOriginalRockPhysics':True,
       'textureRepeatReview':'3x3 inspected visually; no conspicuous straight boundary or edge vignette.'}
(work/'preservation.json').write_text(json.dumps(proof,indent=2))
print('FIDELITY_PRESERVATION_VERIFIED',proof)
