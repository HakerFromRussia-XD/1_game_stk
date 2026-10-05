from pathlib import Path
import sys, math, struct, json, copy, shutil, collections, hashlib, xml.etree.ElementTree as E

r=Path(__file__).resolve().parent; w=r/'fidelity-v20'; w.mkdir(exist_ok=True)
old=r/'fidelity-v19/candidate'; c=w/'candidate'
assert not c.exists(), 'Archive a rejected iteration before rebuilding'
shutil.copytree(old,c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse, rewrite_texture_names
helper=(r/'fidelity_v2.py').read_text(); ns={'math':math,'struct':struct}
exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
d=parse(old/'volcano_track.spm'); source=d['buffers'][5]
assert d['materials'][source['material']][0]=='vr_moss_palette.jpg'
assert len(source['indices'])//3==427

def bounds(points):
    return [min(p[k]for p in points)for k in range(3)]+[max(p[k]for p in points)for k in range(3)]
def distance_boxes(a,b):
    return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
def triangle_points(b):
    return [[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
protected=[t for b in d['buffers']if d['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangle_points(b)]
scene=E.parse(c/'scene.xml')
for e in scene.getroot().findall('object'):
    if e.get('driveable')=='true' and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0', e.attrib
        xyz=list(map(float,e.get('xyz').split())); scale=list(map(float,e.get('scale').split()))
        for b in parse(c/e.get('model'))['buffers']:
            protected += [[tuple(v[k]*scale[k]+xyz[k]for k in range(3))for v in t]for t in triangle_points(b)]
roadboxes=[bounds(t)for t in protected]
def road_box_distance(box):
    return min(distance_boxes(box,q)for q in roadboxes)

# Weld only the decorative visual copy; collision source stays byte-faithful.
positions=[]; colors=[]; mapping={}; coordinate_ids={}
for i,v in enumerate(source['vertices']):
    key=tuple(round(p,5)for p in v['position'])
    if key not in coordinate_ids:
        coordinate_ids[key]=len(positions); positions.append(v['position']); colors.append(v['color'])
    mapping[i]=coordinate_ids[key]
triangles=[tuple(mapping[j]for j in source['indices'][i:i+3])for i in range(0,len(source['indices']),3)]
original_positions=list(positions)
groups=ns['component_triangles'](source)
group_for_triangle={t:j for j,ts in enumerate(groups)for t in ts}
owners=[group_for_triangle[t]for t in range(len(triangles))]
group_bounds=[]
for ts in groups:
    group_bounds.append(bounds([source['vertices'][j]['position']for t in ts for j in source['indices'][3*t:3*t+3]]))
edge_counts=collections.Counter(tuple(sorted((a,b)))for t in triangles for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])])
boundary_edges={e for e,n in edge_counts.items()if n==1}
original_boundaries=collections.defaultdict(list)
for t,g in zip(triangles,owners):
    for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
        if tuple(sorted((a,b)))in boundary_edges: original_boundaries[g].append((positions[a],positions[b]))
source_box=bounds(original_positions)

# Conforming edge subdivision: detail follows the road vicinity rather than
# spending most vertices on the distant low-detail background.
edge_targets={}
for t in triangles:
    near=road_box_distance(bounds([positions[i]for i in t]))
    target=13.0 if near<180 else 65.0
    for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
        e=tuple(sorted((a,b))); edge_targets[e]=min(edge_targets.get(e,1e9),target)
splits=0
while len(triangles)<1800:
    candidates=[]
    for edge,target in edge_targets.items():
        a,b=edge; length=math.dist(positions[a],positions[b])
        if length>target: candidates.append((length/target,edge))
    if not candidates: break
    _,edge=max(candidates); a,b=edge
    incident=[i for i,t in enumerate(triangles)if a in t and b in t]
    assert incident
    if len(triangles)+len(incident)>1800: break
    mid=len(positions); positions.append(tuple((positions[a][k]+positions[b][k])/2 for k in range(3)))
    colors.append(tuple(round((colors[a][k]+colors[b][k])/2)for k in range(3)))
    target=edge_targets.pop(edge)
    if edge in boundary_edges:
        boundary_edges.remove(edge); boundary_edges.update([tuple(sorted((a,mid))),tuple(sorted((mid,b)))])
    next_triangles=[]; next_owners=[]
    for i,(t,g)in enumerate(zip(triangles,owners)):
        if i not in incident: next_triangles.append(t); next_owners.append(g); continue
        for k in range(3):
            u,v,z=t[k],t[(k+1)%3],t[(k+2)%3]
            if {u,v}=={a,b}:
                children=[(u,mid,z),(mid,v,z)]; next_triangles.extend(children); next_owners.extend([g,g])
                for child in children:
                    for x,y in [(child[0],child[1]),(child[1],child[2]),(child[2],child[0])]:
                        e=tuple(sorted((x,y))); edge_targets[e]=min(edge_targets.get(e,1e9),target)
                break
    triangles,owners=next_triangles,next_owners; splits+=1
base_positions=list(positions)

def point_segment_xz(p,a,b):
    dx,dz=b[0]-a[0],b[2]-a[2]; length=dx*dx+dz*dz
    t=0 if length<1e-12 else max(0,min(1,((p[0]-a[0])*dx+(p[2]-a[2])*dz)/length))
    return math.hypot(p[0]-a[0]-t*dx,p[2]-a[2]-t*dz)
def smoothstep(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
allowed=[True]*len(positions); vertex_groups={}
for t,g in zip(triangles,owners):
    points=[positions[i]for i in t]
    u=[points[1][k]-points[0][k]for k in range(3)]; v=[points[2][k]-points[0][k]for k in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]); length=math.sqrt(sum(q*q for q in n))
    safe=length>1e-8 and abs(n[1])/length>.60 and road_box_distance(bounds(points))>18.5
    for i in t:
        vertex_groups[i]=g
        if not safe: allowed[i]=False
anchors=set(i for edge in boundary_edges for i in edge)
anchors.update(i for i,p in enumerate(positions)if any(abs(p[k]-source_box[k+3*a])<1e-5 for k in range(3)for a in [0,1]))
changed=[]
for i,p in enumerate(base_positions):
    if i in anchors or not allowed[i]:continue
    g=vertex_groups[i]; bd=group_bounds[g]; dx,dz=bd[3]-bd[0],bd[5]-bd[2]
    if min(dx,dz)<8: continue
    distance=min(point_segment_xz(p,a,b)for a,b in original_boundaries[g])
    band=min(32,max(6,min(dx,dz)*.30)); rim=smoothstep(distance/band)
    u=(p[0]-(bd[0]+bd[3])/2)/max(dx/2,1); v=(p[2]-(bd[2]+bd[5])/2)/max(dz/2,1)
    amplitude=min(14,max(3,min(dx,dz)*.12))
    raw=amplitude*rim*(.65+.25*math.cos(u*math.pi*.95)+.1*math.cos(v*math.pi*1.4+g*.61))
    available=max(0,source_box[4]-p[1])
    lift=0 if available<1e-5 else available*(1-math.exp(-raw/available))
    if lift>.005:
        positions[i]=(p[0],p[1]+lift,p[2]); changed.append(i)
assert len(changed)>40, ('No meaningful large-form edit',len(changed))
assert max(abs(a-b)for a,b in zip(bounds(positions),source_box))<1e-4
changed_set=set(changed); margins=[]; affected_groups=set()
for t,g in zip(triangles,owners):
    if any(i in changed_set for i in t):
        margin=road_box_distance(bounds([positions[i]for i in t])); assert margin>4.5,margin
        margins.append(margin); affected_groups.add(g)

# Recalculate visual normals; source physics keeps its original vertex data.
normals=[[0.,0.,0.]for p in positions]
for t in triangles:
    a,b,z=[positions[i]for i in t]; u=[b[k]-a[k]for k in range(3)]; v=[z[k]-a[k]for k in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    for i in t:
        for k in range(3): normals[i][k]+=n[k]
buf={'vertices':[],'indices':[i for t in triangles for i in t],'material':0}
for p,col,n in zip(positions,colors,normals):
    length=math.sqrt(sum(q*q for q in n)); assert length>1e-8
    buf['vertices'].append({'position':p,'normal':ns['packed_normal']([q/length for q in n]),'color':col,'uv':(.75,.5)})
alias='fluxara_volcano_moss_shared_v20.jpg'; texture=resources/'textures'/alias
assert not texture.exists() or texture.read_bytes()==(old/'vr_moss_palette.jpg').read_bytes()
texture.write_bytes((old/'vr_moss_palette.jpg').read_bytes())
def standalone(buffer, names, bd):
    raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*bd)+struct.pack('<H',len(names)))
    for pair in names:
        for name in pair:
            value=name.encode(); raw+=bytes([len(value)])+value
    raw+=struct.pack('<HH',1,1); raw+=ns['encode_buffer'](buffer,names); return raw
library=resources/'library/fluxara_driftlib_volcano_rounded_terrain_v20'; library.mkdir(exist_ok=True)
visual=library/'vr_v20_rounded_green_terrain.spm'; visual.write_bytes(standalone(buf,[[alias,'']],source_box))
(library/'node.xml').write_text(f'<scene><object id="RoundedTerrain" type="animation" model="{visual.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
(library/'materials.xml').write_text(f'<materials><material name="{alias}" /></materials>')
collision=copy.deepcopy(source); collision['material']=0
collision_name='vr_v20_original_green_collision.spm'; (c/collision_name).write_bytes(standalone(collision,[[alias,'']],source_box))
names=[[alias if n=='vr_moss_palette.jpg'else n for n in pair]for pair in d['materials']]
main=ns['replace_buffers'](d,{5:[]}); parsed_temp=w/'main-before-alias.spm'; parsed_temp.write_bytes(main)
(c/'volcano_track.spm').write_bytes(rewrite_texture_names(parse(parsed_temp),names))
E.SubElement(scene.getroot(),'object',id='VRV20_OriginalGreenTerrainCollision',type='animation',model=collision_name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',shape='exact',**{'skeletal-animation':'false'})
E.SubElement(scene.getroot(),'library',id='VRV20_RoundedGreenTerrain_000',name=library.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1')
materials=E.parse(c/'materials.xml')
for root in [scene.getroot(),materials.getroot()]:
    for e in root.iter():
        if e.get('name')=='vr_moss_palette.jpg':e.set('name',alias)
scene.write(c/'scene.xml',encoding='unicode'); materials.write(c/'materials.xml',encoding='unicode')
alias_models=[]
for path in c.glob('*.spm'):
    pd=parse(path);names=[['fluxara_volcano_moss_shared_v20.jpg'if n=='vr_moss_palette.jpg'else n for n in pair]for pair in pd['materials']]
    if names!=pd['materials']:path.write_bytes(rewrite_texture_names(pd,names));alias_models.append(path.name)
(c/'vr_moss_palette.jpg').unlink() # Only this draft copy; original and pool images retained.

# Match the edited region to the unmodified original map by indexed positions.
original=parse(r/'before/volcano_track.spm'); rock=next(b for b in original['buffers']if original['materials'][b['material']][0]=='Rock13_col.jpg')
key=lambda b,t:tuple(b['vertices'][j]['position']for j in b['indices'][t*3:t*3+3])
need=collections.Counter(key(source,t)for t in range(427)); selected=[]
for t in range(len(rock['indices'])//3):
    k=key(rock,t)
    if need[k]:selected.append(t);need[k]-=1
assert not any(need.values())
used=sorted({i for t in selected for i in rock['indices'][3*t:3*t+3]}); remap={j:i for i,j in enumerate(used)}
original_part={'vertices':[copy.deepcopy(rock['vertices'][i])for i in used],'indices':[remap[j]for t in selected for j in rock['indices'][3*t:3*t+3]],'material':0}
source_component=w/'original-green-region-before.spm'; source_component.write_bytes(standalone(original_part,[['Rock13_col.jpg','']],source_box))
source_weight=source_component.stat().st_size+(r/'before/Rock13_col.jpg').stat().st_size
adapted_weight=visual.stat().st_size+(c/collision_name).stat().st_size+texture.stat().st_size
assert adapted_weight<=source_weight*1.2
proof={'baseCandidate':'V19','sourceMainBuffer':5,'originalTerrainTriangles':427,'originalMatchedTerrainTriangles':len(selected),
       'sourceGeometryFromBefore':str(r/'before/volcano_track.spm'),'originalComponentWeightModel':str(source_component),
       'originalComponentTexture':str(r/'before/Rock13_col.jpg'),'originalComponentWithTextureBytes':source_weight,
       'adaptedVisibleAndCollisionModelsWithTextureBytes':adapted_weight,'componentWithTextureChangePercent':(adapted_weight/source_weight-1)*100,
       'weightUpper20PercentPassed':True,'visualTriangles':len(triangles),'visualVertices':len(positions),'subdivisionEdgeSplits':splits,
       'modifiedVisualVertices':len(changed),'modifiedTerrainComponentIds':sorted(affected_groups),'originalComponentCount':len(groups),
       'sourceAndTargetLocalBounds':source_box,'minimumChangedFaceRoadBoundingBoxMarginMeters':min(margins),
       'maxVerticalLiftMeters':max(positions[i][1]-base_positions[i][1]for i in changed),
       'newSharedTerrainLibrary':str(library),'newSharedTerrainModel':str(visual),'sourceColliderModel':collision_name,
       'textureAliasOnlyOtherModels':alias_models,'existingGreenPaletteGlobalAlias':str(texture),'existingGreenPaletteSha256':hashlib.sha256(texture.read_bytes()).hexdigest(),
       'stoneTextureAndStoneUVsUnchangedV19':True,'newImagePixels':False,'productionIntegrated':False,'referenceAcceptance':False,
       'originalSceneObjectsRetained':True,'originalSourcePositionsBeforeSubdivision':original_positions,
       'baselineAfterSubdivision':base_positions,'changedVertexIndices':changed,'protectedDrivingTriangles':len(protected)}
(w/'terrain-changes.json').write_text(json.dumps(proof,indent=2))
print('V20_LARGE_GREEN_TERRAIN_READY',len(triangles),len(changed),len(affected_groups),min(margins),source_weight,adapted_weight,flush=True)
