from pathlib import Path
import collections
import copy
import hashlib
import json
import math
import shutil
import struct
import sys
import xml.etree.ElementTree as E

r=Path(__file__).resolve().parent;w=r/'fidelity-v23';w.mkdir(exist_ok=True)
c=w/'candidate';assert not c.exists()
shutil.copytree(r/'fidelity-v22/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
from terrain_triangle_distance import point_triangle_distance,triangle_distance,check_triangle_distance_geometry
check_triangle_distance_geometry()
code=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct}
exec(code[code.index('def encode_buffer'):code.index('new_vertices, new_indices')],ns)
p20=json.loads((r/'fidelity-v20/terrain-changes.json').read_text())
oldmodel=Path(p20['newSharedTerrainModel']);old=parse(oldmodel);oldbuf=old['buffers'][0]
original=parse(r/'fidelity-v19/candidate/volcano_track.spm')['buffers'][5]
groups=ns['component_triangles'](original);targetgroups=[8,9]
baseline=p20['baselineAfterSubdivision']
def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
def boxdistance(a,b):return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
def triangle_points(buf):return [[buf['vertices'][i]['position']for i in buf['indices'][j:j+3]]for j in range(0,len(buf['indices']),3)]
sourcegroups={g:[[original['vertices'][j]['position']for j in original['indices'][3*t:3*t+3]]for t in groups[g]]for g in targetgroups}
removed=[];owners={}
for t in range(len(oldbuf['indices'])//3):
    ids=oldbuf['indices'][3*t:3*t+3]
    center=tuple(sum(baseline[i][k]for i in ids)/3 for k in range(3))
    for g,triangles in sourcegroups.items():
        if min(point_triangle_distance(center,q)for q in triangles)<.0001:
            removed.append(t);owners[t]=g;break
assert removed
kept=[i for t in range(len(oldbuf['indices'])//3)if t not in owners for i in oldbuf['indices'][3*t:3*t+3]]
out=copy.deepcopy(oldbuf);out['indices']=kept
changedtriangles=[];records=[]
for g,src in sourcegroups.items():
    positions=[];mapping={};triangles=[]
    for tri in src:
        ids=[]
        for p in tri:
            key=tuple(p)
            if key not in mapping:mapping[key]=len(positions);positions.append(key)
            ids.append(mapping[key])
        triangles.append(tuple(ids))
    edges=collections.Counter(tuple(sorted((a,b)))for t in triangles for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])])
    boundary={q for q,n in edges.items()if n==1}
    segments=[(positions[a],positions[b])for a,b in boundary]
    target=30.;splits=0
    while True:
        unique={tuple(sorted((a,b)))for t in triangles for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]}
        length,edge=max((math.dist(positions[a],positions[b]),(a,b))for a,b in unique)
        if length<=target:break
        assert len(triangles)<1500
        a,b=edge;mid=len(positions);positions.append(tuple((positions[a][k]+positions[b][k])/2 for k in range(3)))
        if edge in boundary:boundary.remove(edge);boundary.update([tuple(sorted((a,mid))),tuple(sorted((mid,b)))])
        nexttri=[]
        for t in triangles:
            if a not in t or b not in t:nexttri.append(t);continue
            for k in range(3):
                u,v,z=t[k],t[(k+1)%3],t[(k+2)%3]
                if {u,v}=={a,b}:nexttri.extend([(u,mid,z),(mid,v,z)]);break
        triangles=nexttri;splits+=1
    base=list(positions);rim={i for edge in boundary for i in edge};bd=bounds(base)
    def segmentdistance(p,a,b):
        dx,dz=b[0]-a[0],b[2]-a[2];length=dx*dx+dz*dz
        t=max(0,min(1,((p[0]-a[0])*dx+(p[2]-a[2])*dz)/length))if length else 0
        return math.hypot(p[0]-a[0]-dx*t,p[2]-a[2]-dz*t)
    changed=[]
    for i,p in enumerate(base):
        if i in rim:continue
        distance=min(segmentdistance(p,a,b)for a,b in segments)
        u=(p[0]-(bd[0]+bd[3])/2)/max((bd[3]-bd[0])/2,1)
        z=(p[2]-(bd[2]+bd[5])/2)/max((bd[5]-bd[2])/2,1)
        fade=min(1,distance/55);fade=fade*fade*(3-2*fade)
        shape=.7+.2*math.cos(u*math.pi)+.1*math.cos(z*math.pi*1.3+g)
        lift=min(36*fade*shape,max(0,old['bounds'][4]-p[1]))
        if lift>.001:positions[i]=(p[0],p[1]+lift,p[2]);changed.append(i)
    assert len(changed)>30
    normals=[[0.,0.,0.]for p in positions]
    for t in triangles:
        a,b,z=[positions[i]for i in t];u=[b[k]-a[k]for k in range(3)];v=[z[k]-a[k]for k in range(3)]
        n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        for i in t:
            for k in range(3):normals[i][k]+=n[k]
    offset=len(out['vertices'])
    for p,n in zip(positions,normals):
        length=math.sqrt(sum(q*q for q in n));assert length>1e-8
        out['vertices'].append({'position':p,'normal':ns['packed_normal']([q/length for q in n]),'color':(255,255,255),'uv':(.75,.5)})
    out['indices'].extend(offset+i for t in triangles for i in t)
    changedset=set(changed)
    changedtriangles += [[positions[i]for i in t]for t in triangles if any(i in changedset for i in t)]
    records.append({'component':g,'sourceTriangles':len(src),'newTriangles':len(triangles),'newVertices':len(positions),'edgeSplits':splits,'raisedVertices':len(changed),'maximumLiftMeters':max(positions[i][1]-base[i][1]for i in changed),'originalBoundaryPositionsExact':True,'sourceComponentBounds':bd})

main=parse(c/'volcano_track.spm')
protected=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangle_points(b)]
scene=E.parse(c/'scene.xml')
for e in scene.getroot().findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0'
        xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        protected += [[tuple(p[k]*scale[k]+xyz[k]for k in range(3))for p in t]for b in parse(c/e.get('model'))['buffers']for t in triangle_points(b)]
roadboxes=[bounds(t)for t in protected];margins=[]
for t in changedtriangles:
    tb=bounds(t);best=1e9
    for rb,road in zip(roadboxes,protected):
        if boxdistance(tb,rb)<best:best=min(best,triangle_distance(t,road))
    assert best>4.5,best;margins.append(best)
assert max(abs(a-b)for a,b in zip(bounds([v['position']for v in out['vertices']]),old['bounds']))<1e-4
raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*old['bounds'])+struct.pack('<H',len(old['materials'])))
for pair in old['materials']:
    for name in pair:
        value=name.encode();raw+=bytes([len(value)])+value
raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](out,old['materials'])
lib=resources/'library/fluxara_driftlib_volcano_backdrop_terrain_v23';lib.mkdir(exist_ok=True)
model=lib/'vr_v23_rounded_backdrop_terrain.spm';model.write_bytes(raw)
(lib/'node.xml').write_text(f'<scene><object id="RoundedBackdropTerrain" type="animation" model="{model.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
shutil.copy2(oldmodel.parent/'materials.xml',lib/'materials.xml')
placement=scene.getroot().find('library[@id="VRV20_RoundedGreenTerrain_000"]');assert placement.get('name')==oldmodel.parent.name
placement.set('name',lib.name);scene.write(c/'scene.xml',encoding='unicode')
proof={'baseCandidate':'V22','newSharedTerrainLibrary':str(lib),'newSharedTerrainModel':str(model),'sourcePooledModel':str(oldmodel),'sourcePooledModelSha256':hashlib.sha256(oldmodel.read_bytes()).hexdigest(),'sourceAndTargetLocalBounds':list(old['bounds']),'removedSourceTriangleIds':removed,'keptSourceTriangleCount':len(kept)//3,'newTerrainTriangles':len(out['indices'])//3,'newTerrainVertices':len(out['vertices']),'components':records,'protectedDrivingTriangles':len(protected),'minimumChangedFaceRoadTriangleMarginMeters':min(margins),'allOtherV20VerticesAndIndexedAttributesRetained':True,'newMaterialCount':0,'newTextureFiles':0,'newImagePixels':False,'productionIntegrated':False,'referenceAcceptance':False}
(w/'backdrop-changes.json').write_text(json.dumps(proof,indent=2))
print('V23_BACKDROP_FORMS_READY',len(out['indices'])//3,records,min(margins),flush=True)
