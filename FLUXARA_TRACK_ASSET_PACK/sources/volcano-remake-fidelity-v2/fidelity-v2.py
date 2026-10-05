"""Reference-driven visual candidate; protected buffers are copied verbatim."""
from pathlib import Path
import copy
import hashlib
import json
import math
import shutil
import struct
import sys
import xml.etree.ElementTree as E

r = Path(__file__).resolve().parent
sys.path.insert(0, str(r.parent / 'shared-object-redesign'))
from spm_io import parse

work = r / 'fidelity-v2'
baseline = work / 'baseline'
candidate = work / 'candidate'
if not baseline.exists():
    shutil.copytree(r / 'candidate', baseline)
shutil.copytree(baseline, candidate, dirs_exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def encode_buffer(buffer, materials):
    vertices, indices, material = buffer['vertices'], buffer['indices'], buffer['material']
    raw = bytearray(struct.pack('<IIH', len(vertices), len(indices), material))
    for v in vertices:
        raw += struct.pack('<3fI', *v['position'], v['normal'])
        color = tuple(v.get('color', (255, 255, 255)))
        raw += b'\x80' if color == (255, 255, 255) else b'\xff' + bytes(color)
        if materials[material][0]:
            raw += struct.pack('<2e', *v['uv'])
        if materials[material][1]:
            raw += struct.pack('<2e', *v['uv2'])
    raw += struct.pack('<' + str(len(indices)) +
                       ('I' if len(vertices) > 65535 else 'H' if len(vertices) > 255 else 'B'), *indices)
    return raw

def normal(v):
    return tuple((q - 1024 if q > 511 else q) / 511
                 for q in ((v['normal'] >> (10 * k)) & 1023 for k in range(3)))

def packed_normal(n):
    return sum((round(max(-1, min(1, x)) * 511) & 1023) << (10 * i)
               for i, x in enumerate(n)) | (1 << 30)

def replace_buffers(d, replacements):
    starts = [b['vertices'][0]['offset'] - 10 for b in d['buffers']]
    count = sum(len(replacements[i]) if isinstance(replacements.get(i),list) else 1 for i in range(len(d['buffers'])))
    raw = bytearray(d['raw'][:28]) + struct.pack('<H',len(d['materials']))
    for pair in d['materials']:
        for name in pair:
            value=name.encode()
            raw += struct.pack('B',len(value))+value
    raw += struct.pack('<HH',1,count)
    for i, b in enumerate(d['buffers']):
        end = starts[i + 1] if i + 1 < len(starts) else d['geometry_end']
        if i in replacements:
            for replacement in replacements[i] if isinstance(replacements[i],list) else [replacements[i]]:
                raw += encode_buffer(replacement,d['materials'])
        else:
            raw += d['raw'][starts[i]:end]
    return raw + d['raw'][d['geometry_end']:]

def component_triangles(b):
    parent = list(range(len(b['vertices'])))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(i, j):
        parent[find(i)] = find(j)
    keys = {}
    for i, v in enumerate(b['vertices']):
        key = tuple(round(x, 4) for x in v['position'])
        if key in keys:
            join(i, keys[key])
        keys[key] = i
    for t in range(0, len(b['indices']), 3):
        a, c, e = b['indices'][t:t + 3]
        join(a, c)
        join(c, e)
    groups = {}
    for t in range(0, len(b['indices']), 3):
        groups.setdefault(find(b['indices'][t]), []).append(t // 3)
    return list(groups.values())

new_vertices, new_indices = [], []
def face(points):
    a, b, c = points[:3]
    u = [b[k] - a[k] for k in range(3)]
    v = [c[k] - a[k] for k in range(3)]
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(x*x for x in n))
    assert length > 1e-6
    n = tuple(x/length for x in n)
    axis = max(range(3), key=lambda k: abs(n[k]))
    axes = (2, 1) if axis == 0 else (0, 2) if axis == 1 else (0, 1)
    offset = len(new_vertices)
    for p in points:
        new_vertices.append({'position': tuple(p), 'normal': packed_normal(n),
                             'color': (255, 232, 211),
                             'uv': (p[axes[0]] / 3.5, p[axes[1]] / 3.5)})
    new_indices.extend((offset, offset+1, offset+2, offset, offset+2, offset+3))

def box(x0, x1, y0, y1, z0, z1):
    face([(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)])
    face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
    face([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)])
    face([(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)])
    face([(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)])
    face([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)])

d = parse(baseline / 'volcano_track.spm')
assert d['flags'] == 3 and d['version'] & 7 == 2
arch = copy.deepcopy(d['buffers'][1])
groups = component_triangles(arch)
targets = [g for g in groups if len(g) == 294]
assert len(targets) == 1
target = set(targets[0])
old_points = [arch['vertices'][i]['position'] for t in target for i in arch['indices'][t*3:t*3+3]]
lo = tuple(min(v[k] for v in old_points) for k in range(3))
hi = tuple(max(v[k] for v in old_points) for k in range(3))
cx, outer = (lo[0] + hi[0])/2, (hi[0] - lo[0])/2
spring, inner = hi[1] - outer, 7.9
z0, z1 = lo[2], hi[2]
def ring(radius, angle, z):
    return (cx + radius*math.cos(angle), spring + radius*math.sin(angle), z)
for j in range(28):
    a, b = math.pi*j/28, math.pi*(j+1)/28
    face([ring(inner,a,z0),ring(inner,b,z0),ring(outer,b,z0),ring(outer,a,z0)])
    face([ring(inner,a,z1),ring(outer,a,z1),ring(outer,b,z1),ring(inner,b,z1)])
    face([ring(outer,a,z0),ring(outer,b,z0),ring(outer,b,z1),ring(outer,a,z1)])
    face([ring(inner,a,z0),ring(inner,a,z1),ring(inner,b,z1),ring(inner,b,z0)])
face([ring(inner,0,z0),ring(outer,0,z0),ring(outer,0,z1),ring(inner,0,z1)])
face([ring(inner,math.pi,z0),ring(inner,math.pi,z1),ring(outer,math.pi,z1),ring(outer,math.pi,z0)])
# Each pier has a separate foot, inset shaft and capital, without overlapping faces.
for xa, xb in [(lo[0], cx-inner), (cx+inner, hi[0])]:
    box(xa, xb, lo[1], lo[1]+1, z0, z1)
    box(xa+.14, xb-.14, lo[1]+1, spring-.75, z0+.14, z1-.14)
    box(xa, xb, spring-.75, spring, z0, z1)
assert len(new_indices)//3 == 300
remaining = [i for t in range(len(arch['indices'])//3) if t not in target
             for i in arch['indices'][t*3:t*3+3]]
used = sorted(set(remaining))
mapping = {old: new for new, old in enumerate(used)}
kept = [arch['vertices'][i] for i in used]
arch['vertices'] = kept + new_vertices
arch['indices'] = [mapping[i] for i in remaining] + [len(kept)+i for i in new_indices]

wall = copy.deepcopy(d['buffers'][5])
for v in wall['vertices']:
    v['uv'] = tuple(x*3 for x in v['uv'])
    v['color'] = tuple(round(x*k) for x,k in zip(v['color'], (1,.91,.83)))

def cliffs(buffer, moss_material):
    result=[{'vertices':[],'indices':[],'material':buffer['material']},
            {'vertices':[],'indices':[],'material':moss_material}]
    cache=[{},{}]
    counts={'mossTriangles':0,'stoneTriangles':0}
    for t in range(0,len(buffer['indices']),3):
        original=[buffer['vertices'][i] for i in buffer['indices'][t:t+3]]
        averaged=tuple(sum(normal(v)[k] for v in original)/3 for k in range(3))
        a,b,c=[v['position'] for v in original]
        u=[b[k]-a[k] for k in range(3)]
        v=[c[k]-a[k] for k in range(3)]
        geometric=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(x*x for x in geometric))
        geometric=tuple(x/length for x in geometric) if length>1e-8 else averaged
        if sum(x*y for x,y in zip(geometric,averaged))<0:
            geometric=tuple(-x for x in geometric)
        moss=geometric[1]>.85 and sum(v['position'][1] for v in original)/3>-10
        group=int(moss)
        axis=max(range(3),key=lambda k:abs(geometric[k]))
        axes=(2,1) if axis==0 else (0,2) if axis==1 else (0,1)
        for source in original:
            v=copy.deepcopy(source)
            x,y,z=v['position']
            v['uv']=(.75,.5) if moss else tuple(v['position'][k]/28 for k in axes)
            shade=.90+.08*(.5+.5*math.sin(x*.083+z*.041+y*.12))
            v['color']=tuple(round(255*shade*k) for k in ((.90,1,.85) if moss else (1,1,1)))
            key=(v['position'],v['normal'],v['uv'],v['color'])
            if key not in cache[group]:
                cache[group][key]=len(result[group]['vertices'])
                result[group]['vertices'].append(v)
            result[group]['indices'].append(cache[group][key])
        counts['mossTriangles' if moss else 'stoneTriangles']+=1
    return [b for b in result if b['indices']],counts

d['materials'].append(['vr_moss_palette.jpg',''])
rock, counts = cliffs(d['buffers'][2],len(d['materials'])-1)
(candidate / 'volcano_track.spm').write_bytes(replace_buffers(d, {1: arch, 2: rock, 5: wall}))
rows = [{'model':'volcano_track.spm', **counts}]
for name in ['vulcan_01.spm', 'vulcan_02.spm', 'vulcan_03.spm']:
    vd = parse(baseline/name)
    vd['materials'].append(['vr_moss_palette.jpg',''])
    replacement = {}
    for i, b in enumerate(vd['buffers']):
        if vd['materials'][b['material']][0] == 'Rock13_col.jpg':
            replacement[i], counts = cliffs(b,len(vd['materials'])-1)
            rows.append({'model':name, **counts})
    (candidate/name).write_bytes(replace_buffers(vd,replacement))

new = parse(candidate / 'volcano_track.spm')
for i in range(len(d['buffers'])):
    if i in {1,2,5}:
        continue
    a, b = d['buffers'][i], new['buffers'][i+int(i>2)]
    assert a['indices'] == b['indices']
    for v,w in zip(a['vertices'],b['vertices']):
        for key in ['position','normal','uv','color']:
            assert v.get(key) == w.get(key), (i,key)
assert d['bounds'] == new['bounds']
assert .8*294 <= len(new_indices)//3 <= 1.2*294
shutil.copy2(work/'volcano-cliff-stone-v2.jpg',candidate/'Rock13_col.jpg')
shutil.copy2(baseline/'Rock13_col.jpg',candidate/'vr_moss_palette.jpg')
materials=E.parse(candidate/'materials.xml')
source=next(e for e in materials.getroot() if e.get('name')=='Rock13_col.jpg')
entry=copy.deepcopy(source)
entry.set('name','vr_moss_palette.jpg')
materials.getroot().append(entry)
materials.write(candidate/'materials.xml',encoding='unicode')
references=set()
for p in candidate.glob('*.spm'):
    for pair in parse(p)['materials']:
        references.update(pair)
for p in candidate.glob('*.xml'):
    for e in E.parse(p).getroot().iter():
        for value in e.attrib.values():
            references.update(value.split())
support_names=['smoke_huricane-nm.png','Rock13_nrm.jpg','blackrock_lava_glossy.jpg',
               'castlewall_nm.jpg','Rock13_glossy.jpg','blackrock-nm.png',
               'Lava_004_glossy.jpg','lava_glossy.png','lava_2k_glossy.jpg',
               'lava_normal.png','lava_2k_nm.jpg']
archive=work/'unused-support-map-archive'
archive.mkdir(exist_ok=True)
removed=[]
for name in support_names:
    assert name not in references,name
    p=candidate/name
    shutil.copy2(p,archive/name)
    removed.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'archive':str(archive/name)})
    p.unlink()
(work/'unused-support-maps.json').write_text(json.dumps({'files':removed,
    'savedBytes':sum(v['bytes'] for v in removed),'pendingBundleAndRuntimeVerification':True},indent=2))
result = {'baseline':str(baseline), 'candidate':str(candidate),
          'mainBeforeSha256':sha(baseline/'volcano_track.spm'),
          'mainAfterSha256':sha(candidate/'volcano_track.spm'),
          'reference':'Figma 378:39',
          'arch':{'originalTriangles':294,'newTriangles':300,'componentBounds':[lo,hi],
                  'center':[(lo[k]+hi[k])/2 for k in range(3)],'newOpeningWidth':inner*2,
                  'newSpringHeight':spring,'originalNonTargetComponentsRetained':3,
                  'shape':'Stone semicircular portal replacing the decorative tooth-shaped entrance'},
          'castleUvMultiplier':3,'mossFaceNormalThreshold':.85,'cliffShading':rows,
          'unchangedMainBuffers':[i for i in range(len(d['buffers'])) if i not in {1,2,5}],
          'newTextures':1,'newSharedRuntimeBytes':0,
          'unusedSupportingMapsArchivedBytes':sum(v['bytes'] for v in removed),
          'previousTrackBytes':sum(p.stat().st_size for p in baseline.iterdir() if p.is_file()),
          'candidateTrackBytes':sum(p.stat().st_size for p in candidate.iterdir() if p.is_file()),
          'sourceCourseAndGameplayFilesUntouched':True,
          'note':'Candidate only; opening clearance and game rendering must pass before integration.'}
(work/'changes.json').write_text(json.dumps(result,indent=2))
print('FIDELITY_CANDIDATE_READY',len(new_indices)//3,rows)
