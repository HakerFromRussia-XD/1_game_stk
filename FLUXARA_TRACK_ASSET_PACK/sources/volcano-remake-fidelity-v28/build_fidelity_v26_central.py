from pathlib import Path
import collections, copy, hashlib, json, math, shutil, struct, sys
import xml.etree.ElementTree as E
r=Path(__file__).resolve().parent; w=r/'fidelity-v26'; w.mkdir(exist_ok=True)
c=w/'candidate'; assert not c.exists(); shutil.copytree(r/'fidelity-v24/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
sys.path.insert(0,str(r.parent/'shared-object-redesign')); from spm_io import parse
from terrain_triangle_distance import triangle_distance
ns={'math':math,'struct':struct}; text=(r/'fidelity_v2.py').read_text()
exec(text[text.index('def encode_buffer'):text.index('new_vertices, new_indices')],ns)
d=parse(c/'volcano_track.spm'); b=d['buffers'][2]; assert len(b['indices'])//3==64
groups=ns['component_triangles'](b); targets=set(groups[0])
def bounds(pp): return [min(q[k] for q in pp) for k in range(3)]+[max(q[k] for q in pp) for k in range(3)]
def boxes_distance(a,z): return math.sqrt(sum(max(a[k]-z[k+3],z[k]-a[k+3],0)**2 for k in range(3)))
def triangles(buf): return [[buf['vertices'][i]['position'] for i in buf['indices'][j:j+3]] for j in range(0,len(buf['indices']),3)]
protected=[t for buf in d['buffers'] if d['materials'][buf['material']][0] in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png'] for t in triangles(buf)]
scene=E.parse(c/'scene.xml')
for e in scene.getroot().findall('object'):
    if e.get('driveable')=='true' and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0'
        xyz=list(map(float,e.get('xyz').split())); scale=list(map(float,e.get('scale').split()))
        protected += [[tuple(p[k]*scale[k]+xyz[k] for k in range(3)) for p in t] for bb in parse(c/e.get('model'))['buffers'] for t in triangles(bb)]
assert len(protected)==2032; roadboxes=[bounds(t) for t in protected]
out=copy.deepcopy(b); out['indices']=[i for t in range(64) if t not in targets for i in b['indices'][3*t:3*t+3]]
certificates=[]; records=[]
for component in [0]:
    faces=[tuple(b['indices'][3*t:3*t+3]) for t in groups[component]]
    sourceids=sorted({i for t in faces for i in t}); verts={i:copy.deepcopy(b['vertices'][i]) for i in sourceids}
    edgeids={}; nextid=len(b['vertices'])
    def edge(a,z):
        global nextid
        key=tuple(sorted((a,z)))
        if key not in edgeids:
            row=copy.deepcopy(verts[a]); row['position']=tuple((verts[a]['position'][k]+verts[z]['position'][k])/2 for k in range(3))
            row['uv']=tuple((verts[a]['uv'][k]+verts[z]['uv'][k])/2 for k in range(2))
            row['color']=tuple(round((verts[a].get('color',(255,255,255))[k]+verts[z].get('color',(255,255,255))[k])/2) for k in range(3))
            edgeids[key]=nextid; verts[nextid]=row; nextid+=1
        return edgeids[key]
    linear=[]
    for a,z,h in faces:
        az,zh,ha=edge(a,z),edge(z,h),edge(h,a)
        linear.extend([(a,az,ha),(az,z,zh),(ha,zh,h),(az,zh,ha)])
    # Weld only geometry. Texture seams keep their distinct UV vertices.
    wid={}; positions=[]; vwid={}
    for i,v in verts.items():
        key=tuple(round(x,4) for x in v['position'])
        if key not in wid: wid[key]=len(positions); positions.append(tuple(v['position']))
        vwid[i]=wid[key]
    edges=collections.defaultdict(list); neighbours=collections.defaultdict(set); incident=collections.defaultdict(list)
    allowed=[]
    for ti,t in enumerate(linear):
        pp=[verts[i]['position'] for i in t]; tb=bounds(pp)
        nearest=30.
        for rb,road in zip(roadboxes,protected):
            if boxes_distance(tb,rb)<nearest: nearest=min(nearest,triangle_distance(pp,road))
        allowed.append(max(0,min(10,nearest-5)))
        ids=[vwid[i] for i in t]
        for i in ids: incident[i].append(ti)
        for a,z,h in [(ids[0],ids[1],ids[2]),(ids[1],ids[2],ids[0]),(ids[2],ids[0],ids[1])]:
            edges[tuple(sorted((a,z)))].append((h,ti)); neighbours[a].add(z); neighbours[z].add(a)
    boundary={i for key,rows in edges.items() if len(rows)!=2 for i in key}
    componentbounds=bounds([b['vertices'][i]['position'] for i in sourceids])
    def constrain(base,p,limit):
        q=tuple(max(componentbounds[k],min(componentbounds[k+3],p[k])) for k in range(3))
        # Keep all original extreme planes and open rims, including the grass interface.
        if any(abs(base[k]-componentbounds[k])<1e-4 or abs(base[k]-componentbounds[k+3])<1e-4 for k in range(3)): return base
        length=math.dist(base,q)
        if length>limit and length: q=tuple(base[k]+(q[k]-base[k])*limit/length for k in range(3))
        return q
    relocated={}
    for i,base in enumerate(positions):
        n=len(neighbours[i]); beta=3/(8*n) if n>3 else 3/16
        p=tuple((1-n*beta)*base[k]+beta*sum(positions[j][k] for j in neighbours[i]) for k in range(3)) if n else base
        relocated[i]=base if i in boundary else constrain(base,p,min(allowed[t] for t in incident[i]))
    finalverts={i:copy.deepcopy(v) for i,v in verts.items()}; bases={i:tuple(v['position']) for i,v in verts.items()}
    for i,row in finalverts.items(): row['position']=relocated[vwid[i]]
    finaledges={}; globaledge={}; nextfinal=max(finalverts)+1
    def finaledge(a,z):
        global nextfinal
        key=tuple(sorted((a,z)))
        if key not in finaledges:
            weldkey=tuple(sorted((vwid[a],vwid[z]))); rows=edges[weldkey]
            base=tuple((bases[a][k]+bases[z][k])/2 for k in range(3))
            if weldkey not in globaledge:
                p=tuple(3/8*(positions[weldkey[0]][k]+positions[weldkey[1]][k])+1/8*sum(positions[q[0]][k] for q in rows) for k in range(3)) if len(rows)==2 else base
                globaledge[weldkey]=constrain(base,p,min(allowed[q[1]] for q in rows))
            row=copy.deepcopy(verts[a]); row['position']=globaledge[weldkey]
            row['uv']=tuple((verts[a]['uv'][k]+verts[z]['uv'][k])/2 for k in range(2))
            row['color']=tuple(round((verts[a].get('color',(255,255,255))[k]+verts[z].get('color',(255,255,255))[k])/2) for k in range(3))
            finaledges[key]=nextfinal; finalverts[nextfinal]=row; bases[nextfinal]=base; nextfinal+=1
        return finaledges[key]
    final=[]; parentids=[]
    for ti,(a,z,h) in enumerate(linear):
        az,zh,ha=finaledge(a,z),finaledge(z,h),finaledge(h,a)
        final.extend([(a,az,ha),(az,z,zh),(ha,zh,h),(az,zh,ha)]); parentids.extend([ti]*4)
    # Area-weighted smooth normals shared across coincident UV seam positions.
    sums=collections.defaultdict(lambda:[0.,0.,0.])
    key=lambda i:tuple(round(q,4) for q in finalverts[i]['position'])
    for t in final:
        a,z,h=[finalverts[i]['position'] for i in t]; u=[z[k]-a[k] for k in range(3)]; v=[h[k]-a[k] for k in range(3)]
        n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        assert sum(x*x for x in n)>1e-10
        for i in t:
            for k in range(3): sums[key(i)][k]+=n[k]
    remap={}; active={i for t in final for i in t}
    for i in sorted(active):
        row=finalverts[i]; n=sums[key(i)]; length=math.sqrt(sum(x*x for x in n)); assert length>1e-9
        row['normal']=ns['packed_normal']([q/length for q in n]); remap[i]=len(out['vertices']); out['vertices'].append(row)
    changed=0; margin=1e9
    for t,ti in zip(final,parentids):
        displacement=max(math.dist(finalverts[i]['position'],bases[i]) for i in t)
        if displacement>1e-5:
            tb=bounds([verts[i]['position'] for i in linear[ti]])
            lower=allowed[ti]+5-displacement
            assert lower>4.999,lower; margin=min(margin,lower); changed+=1
        certificates.append({'indices':[remap[i] for i in t],'parentLinearTriangle':[verts[i]['position'] for i in linear[ti]],'baselineCorners':[bases[i] for i in t]})
        out['indices'].extend(remap[i] for i in t)
    records.append({'component':component,'sourceTriangles':len(faces),'newTriangles':len(final),'changedTriangles':changed,'minimumChangedTriangleCertifiedRoadMarginMeters':margin,'maximumVertexShiftMeters':max(math.dist(finalverts[i]['position'],bases[i]) for i in active),'componentActiveBounds':bounds([finalverts[i]['position'] for i in active]),'originalComponentBounds':componentbounds})
    print('CLIF_COMPONENT_READY',records[-1],flush=True)

def standalone(buf,materials):
    pp=[buf['vertices'][i]['position'] for i in buf['indices']]; raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*bounds(pp))+struct.pack('<H',len(materials)))
    for pair in materials:
        for name in pair:
            v=name.encode();raw+=bytes([len(v)])+v
    return raw+struct.pack('<HH',1,1)+ns['encode_buffer'](buf,materials)
lib=resources/'library/fluxara_driftlib_volcano_central_stone_v26'; assert not lib.exists(); lib.mkdir()
visual=lib/'vr_v26_rounded_central_stone.spm'; out['material']=0
visual.write_bytes(standalone(out,[['fluxara_volcano_stone_shared_v16.jpg','']]))
(lib/'node.xml').write_text(f'<scene><object id="RoundedCentralStone" type="animation" model="{visual.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
(lib/'materials.xml').write_text('<materials><material name="fluxara_volcano_stone_shared_v16.jpg" shader="solid" /></materials>')
collision=copy.deepcopy(b); collision['material']=0
collider=c/'vr_v26_original_stone_walls_collision.spm'; collider.write_bytes(standalone(collision,[['','']]))
(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](d,{2:[]}))
E.SubElement(scene.getroot(),'library',id='VRV26_RoundedCentralStone_000',name=lib.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1')
E.SubElement(scene.getroot(),'object',id='VRV26_OriginalCentralStoneCollision',type='animation',model=collider.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',**{'skeletal-animation':'false'})
scene.write(c/'scene.xml',encoding='unicode')
(w/'road-clearance-certificates.json').write_text(json.dumps(certificates))
proof={'baseCandidate':'V24','sourceModel':str(r/'fidelity-v24/candidate/volcano_track.spm'),'sourceModelSha256':hashlib.sha256((r/'fidelity-v24/candidate/volcano_track.spm').read_bytes()).hexdigest(),'sourceBuffer':2,'newSharedLibrary':str(lib),'newSharedModel':str(visual),'originalCollider':str(collider),'components':records,'retainedSourceTriangles':64-len(targets),'targetTriangles':len(out['indices'])//3,'protectedDrivingTriangles':2032,'newImagePixels':False,'newMaterials':0,'sourceTexturePixelsRetained':True,'sourceUVsRetainedAndNewUVsInterpolated':True,'wholeOriginalStoneModelBoundsRetained':True,'originalStoneCollisionGeometryRetained':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'cliff-changes.json').write_text(json.dumps(proof,indent=2))
print('V26_MAIN_CLIFF_SILHOUETTES_READY',len(out['indices'])//3,visual.stat().st_size,flush=True)
