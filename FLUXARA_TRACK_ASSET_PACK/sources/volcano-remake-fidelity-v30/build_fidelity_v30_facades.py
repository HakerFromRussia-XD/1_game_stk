from pathlib import Path
import hashlib,json,math,random,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v30';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v29/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
model_paths=[resources/'library/fluxara_driftlib_volcano_grass_cap_v27/vr_v27_grass_cap.spm',resources/'library/fluxara_driftlib_volcano_stone_column_v29/vr_v29_grounded_stone_column.spm',resources/'library/fluxara_driftlib_round_tree_green_v2/fluxara_driftlib_round_tree_green_v2_main.spm']
models=[parse(p)for p in model_paths];parts=[models[0]['buffers'][0],models[1]['buffers'][0]]
def bounds(pp):return [min(v[k]for v in pp)for k in range(3)]+[max(v[k]for v in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
main=parse(c/'volcano_track.spm');wall_index=next(i for i,b in enumerate(main['buffers'])if len(b['indices'])//3==2210 and main['materials'][b['material']][0]=='fluxara_volcano_stone_shared_v16.jpg');wall=main['buffers'][wall_index]
groups=ns['component_triangles'](wall);assert [len(q)for q in groups]==[44,32,10,39,44,232,231,70,1045,463]
scene=E.parse(c/'scene.xml');root=scene.getroot();road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in root.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';p=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(v[k]*size[k]+p[k]for k in range(3))for v in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
assert len(road)==2032;roadboxes=[bounds(t)for t in road];horizontalroad=[[(v[0],0,v[2])for v in t]for t in road];hboxes=[bounds(t)for t in horizontalroad]
def boxdist(a,b):return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
def nearroad(p):
    pp=(p[0],0,p[2]);best=1e9
    for t,box in zip(horizontalroad,hboxes):
        if boxdist(list(pp)+list(pp),box)<best:best=min(best,point_triangle_distance(pp,t))
    return best
def normal(v):return tuple((q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]])
def world(v,pos,scale,yaw):
    co,si=math.cos(yaw),math.sin(yaw);return (pos[0]+co*v[0]*scale[0]+si*v[2]*scale[2],pos[1]+v[1]*scale[1],pos[2]-si*v[0]*scale[0]+co*v[2]*scale[2])
def margin(buf,pos,scale,yaw):
    best=1e9
    for t in triangles(buf):
        tt=[world(v,pos,scale,yaw)for v in t];box=bounds(tt)
        for rt,rb in zip(road,roadboxes):
            if boxdist(box,rb)<best:best=min(best,triangle_distance(tt,rt))
    return best
rows=[]
for ci in [8,9]:
    for ti in groups[ci]:
        vv=[wall['vertices'][i]for i in wall['indices'][ti*3:ti*3+3]];tt=[v['position']for v in vv];center=tuple(sum(v[k]for v in tt)/3 for k in range(3));n=tuple(sum(normal(v)[k]for v in vv)/3 for k in range(3));length=math.hypot(n[0],n[2]);height=max(v[1]for v in tt)-min(v[1]for v in tt)
        if length<.7 or height<8 or max(v[1]for v in tt)<12:continue
        distance=nearroad(center)
        if not 14<distance<95:continue
        rows.append({'component':ci,'triangle':ti,'center':center,'horizontalNormal':(n[0]/length,n[2]/length),'top':max(v[1]for v in tt),'sourceTriangle':tt,'horizontalRoadDistance':distance})
# Large forms are sampled on existing decorative cliff faces, not gameplay lines.
# Prioritize high near-route faces and maintain space between broad columns.
rows.sort(key=lambda q:(q['horizontalRoadDistance']/2-q['top'],q['triangle']));rng=random.Random(3001);placements=[];skipped=0
for row in rows:
    if len(placements)>=40:break
    x,y,z=row['center'];n=row['horizontalNormal'];sx=rng.uniform(3.7,5.1);sz=rng.uniform(3.7,5.1);radius=max(3.22931*sx,2.238349*sz)
    x-=n[0]*radius*.12;z-=n[1]*radius*.12
    if any(math.hypot(x-q['centerXZ'][0],z-q['centerXZ'][1])<22 for q in placements):continue
    top=row['top']+rng.uniform(1.5,4);bottom=min(-40,y-35);sy=(top-bottom)/(models[1]['bounds'][4]-models[1]['bounds'][1]);pos=[x,top-models[1]['bounds'][4]*sy,z];scale=[sx,sy,sz];yaw=math.atan2(n[0],n[1]);gs=[sx*.95,3.2,sz*.95];gp=[x,top-models[0]['bounds'][1]*gs[1]-.08,z]
    stone_margin=margin(parts[1],pos,scale,yaw);grass_margin=margin(parts[0],gp,gs,yaw)
    if min(stone_margin,grass_margin)<3:skipped+=1;continue
    index=len(placements);attrs=[]
    for role,lib,xyz,size in [('Stone',model_paths[1].parent.name,pos,scale),('Grass',model_paths[0].parent.name,gp,gs)]:
        e=E.SubElement(root,'library',id=f'VRV30_CliffFacade_{index:03d}_{role}',name=lib,xyz=' '.join(f'{v:.8f}'for v in xyz),hpr=f'0 {math.degrees(yaw):.8f} 0',scale=' '.join(f'{v:.8f}'for v in size));attrs.append(dict(e.attrib))
    # Position a directly reused leaf tree on the actual cap mesh, not its origin.
    gx=rng.uniform(-.7,.7);gz=rng.uniform(-.55,.55);gt=[]
    for t in triangles(parts[0]):
        a,b,d=t;den=(b[2]-d[2])*(a[0]-d[0])+(d[0]-b[0])*(a[2]-d[2])
        if abs(den)<1e-10:continue
        u=((b[2]-d[2])*(gx-d[0])+(d[0]-b[0])*(gz-d[2]))/den;v=((d[2]-a[2])*(gx-d[0])+(a[0]-d[0])*(gz-d[2]))/den
        if min(u,v,1-u-v)>=-1e-8:gt.append(u*a[1]+v*b[1]+(1-u-v)*d[1])
    assert gt;treepos=list(world((gx,max(gt),gz),gp,gs,yaw));tree_size=rng.uniform(8,13);tree_scale=[tree_size]*3;tree_margin=min(margin(buf,treepos,tree_scale,yaw)for buf in models[2]['buffers']);assert tree_margin>3
    e=E.SubElement(root,'library',id=f'VRV30_CliffFacade_{index:03d}_Tree',name=model_paths[2].parent.name,xyz=' '.join(f'{v:.8f}'for v in treepos),hpr=f'0 {math.degrees(yaw):.8f} 0',scale=' '.join(f'{v:.8f}'for v in tree_scale));attrs.append(dict(e.attrib))
    placements.append({'sourceFace':row,'centerXZ':[x,z],'stoneFootY':bottom,'stoneTopY':top,'treeBaseOnCapLocalPoint':[gx,max(gt),gz],'parts':attrs,'exactPartRoadMarginsMeters':[stone_margin,grass_margin,tree_margin]});print('V30_FACADE_READY',index,min(stone_margin,grass_margin,tree_margin),flush=True)
assert len(placements)>=12,len(placements)
scene.write(c/'scene.xml',encoding='unicode');p={'baseCandidate':'V29','sourceStoneBuffer':wall_index,'sourceMainSha256':hashlib.sha256((c/'volcano_track.spm').read_bytes()).hexdigest(),'placements':placements,'modelSources':[{'path':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes':q.stat().st_size}for q in model_paths],'newModelFiles':0,'newTextureFiles':0,'newMaterials':0,'newGeometry':False,'originalMainMeshesPhysicsAndNodesRetained':True,'sourceModelLocalBoundsOriginsAxesRetained':True,'newAddedInstanceTransforms':True,'newCoordinateGroups':len(placements),'roadClearanceRejectedCandidates':skipped,'minimumAllNewPartRoadMarginMeters':min(min(q['exactPartRoadMarginsMeters'])for q in placements),'protectedDrivingTriangles':2032,'sourceStonePixelsRetained':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'facade-placements.json').write_text(json.dumps(p,indent=2));print('V30_POOLED_FACADES_READY',len(placements),p['minimumAllNewPartRoadMarginMeters'],flush=True)
