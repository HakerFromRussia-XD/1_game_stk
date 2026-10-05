from pathlib import Path
import copy,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v29';w.mkdir(exist_ok=True);c=w/'candidate'
assert not c.exists();shutil.copytree(r/'fidelity-v28/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
source=resources/'library/fluxara_driftlib_volcano_stone_column_v27/vr_v27_stone_column.spm';d=parse(source);old=d['buffers'][0];b=copy.deepcopy(old)
def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
box=bounds([v['position']for v in old['vertices']]);rx=max(abs(box[0]),abs(box[3]));rz=max(abs(box[2]),abs(box[5]));changes=[]
for i,v in enumerate(b['vertices']):
    x,y,z=v['position']
    if y>=0:continue
    radius=math.hypot(x/rx,z/rz)
    if radius<1e-5:continue
    depth=min(1,-y/.54349893);factor=1+.7*depth;target=min(.97,radius*factor)
    factor=target/radius
    v['position']=(x*factor,y,z*factor);changes.append({'vertex':i,'before':old['vertices'][i]['position'],'after':v['position']})
assert bounds([v['position']for v in b['vertices']])==box
def normal(v):return tuple((q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]])
def key(v):return tuple(round(q,6)for q in v['position'])
acc={key(v):[0.,0.,0.]for v in b['vertices']}
for j in range(0,len(b['indices']),3):
    ids=b['indices'][j:j+3];vv=[b['vertices'][i]for i in ids];a,t,u=[v['position']for v in vv]
    v=[t[k]-a[k]for k in range(3)];q=[u[k]-a[k]for k in range(3)];n=[v[1]*q[2]-v[2]*q[1],v[2]*q[0]-v[0]*q[2],v[0]*q[1]-v[1]*q[0]]
    assert math.sqrt(sum(x*x for x in n))>1e-6,(j,n)
    oldn=[sum(normal(old['vertices'][i])[k]for i in ids)for k in range(3)]
    if sum(n[k]*oldn[k]for k in range(3))<0:n=[-x for x in n]
    for vertex in vv:
        for k in range(3):acc[key(vertex)][k]+=n[k]
for v in b['vertices']:
    if v['position'][1]>=0:continue
    n=acc[key(v)];length=math.sqrt(sum(x*x for x in n));assert length>1e-6
    v['normal']=ns['packed_normal']([x/length for x in n])
raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*box)+struct.pack('<H',len(d['materials'])))
for material in d['materials']:
    for name in material:q=name.encode();raw+=bytes([len(q)])+q
raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](b,d['materials'])
lib=resources/'library/fluxara_driftlib_volcano_stone_column_v29';assert not lib.exists();lib.mkdir()
model=lib/'vr_v29_grounded_stone_column.spm';model.write_bytes(raw)
(lib/'node.xml').write_text(f'<scene><object id="stone_column" type="animation" model="{model.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
shutil.copy2(source.parent/'materials.xml',lib/'materials.xml')
scene=E.parse(c/'scene.xml');root=scene.getroot();poses=[]
for e in root.findall('library'):
    if e.get('name')!=source.parent.name:continue
    before=dict(e.attrib);e.set('name',lib.name);poses.append({'before':before,'after':dict(e.attrib)})
assert len(poses)==58;scene.write(c/'scene.xml',encoding='unicode')
main=parse(c/'volcano_track.spm');triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in root.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(q[k]*size[k]+pos[k]for k in range(3))for q in t]for buf in parse(c/e.get('model'))['buffers']for t in triangles(buf)]
assert len(road)==2032;boxes=[bounds(t)for t in road];minimum=1e9
for row in poses:
    e=row['after'];pos=list(map(float,e['xyz'].split()));size=list(map(float,e['scale'].split()));yaw=math.radians(float(e['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
    world=lambda v:(pos[0]+co*v[0]*size[0]+si*v[2]*size[2],pos[1]+v[1]*size[1],pos[2]-si*v[0]*size[0]+co*v[2]*size[2])
    best=1e9
    for tri in triangles(b):
        tt=[world(v)for v in tri];tb=bounds(tt)
        for rb,rt in zip(boxes,road):
            lower=math.sqrt(sum(max(tb[k]-rb[k+3],rb[k]-tb[k+3],0)**2 for k in range(3)))
            if lower<best:best=min(best,triangle_distance(tt,rt))
    row['exactStoneTriangleRoadMarginMeters']=best;minimum=min(minimum,best);assert best>.5,(e['id'],best)
    print('V29_FOOT_CLEAR',e['id'],best,flush=True)
stone=resources/'textures/fluxara_volcano_stone_shared_v16.jpg';assert hashlib.sha256(stone.read_bytes()).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
p={'baseCandidate':'V28','sourceModel':str(source),'sourceModelSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'newSharedModel':str(model),'newSharedLibrary':str(lib),'sourcePoolObjectId':'volcano-fidelity-v22-stonebody','newPrototype':'VRV29_Prototype_GroundedStoneBody','newPrototypeId':'volcano-fidelity-v29-grounded-stonebody','localBounds':box,'changedVertices':changes,'placements':poses,'triangles':152,'vertices':95,'sourceUVsRGBIndicesBoundsOriginsAxesRetained':True,'upperHalfPositionsNormalsRetained':True,'instanceTransformsRetained':True,'minimumExactStoneTriangleRoadMarginMeters':minimum,'protectedDrivingTriangles':2032,'newTextureFiles':0,'newMaterials':0,'productionIntegrated':False,'referenceAcceptance':False}
(w/'stone-foot-changes.json').write_text(json.dumps(p,indent=2));print('V29_STONE_FOOT_CANDIDATE_READY',len(changes),model.stat().st_size,minimum,flush=True)
