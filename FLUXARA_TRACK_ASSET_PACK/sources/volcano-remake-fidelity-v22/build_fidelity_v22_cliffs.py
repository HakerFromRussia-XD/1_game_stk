from pathlib import Path
import sys,math,struct,json,copy,shutil,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v22';w.mkdir(exist_ok=True);old=r/'fidelity-v21/candidate';c=w/'candidate';assert not c.exists();shutil.copytree(old,c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
source_proof=json.loads((r/'fidelity-v16/terrain-changes.json').read_text());source=Path(source_proof['adaptedSharedModel']);d=parse(source);buffers=copy.deepcopy(d['buffers']);bd=d['bounds'];rx,rz=bd[3],bd[5];peak=bd[4]
ns={'math':math,'struct':struct};helper=(r/'fidelity_v2.py').read_text();exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
for bi,b in enumerate(buffers):
    for v in b['vertices']:
        x,y,z=v['position'];theta=math.atan2(z/rz,x/rx);rad=math.hypot(x/rx,z/rz)
        irregular=math.sin(2*theta)**2*(.07+.025*math.sin(3*theta+.6)+.02*math.sin(5*theta))
        factor=1-irregular*(1 if bi==0 else .65+.35*math.cos(y*2.7))
        surface=peak-.24*rad*rad+.035*math.sin(3*theta+.6)*rad*rad
        if bi==0:
            ny=y if abs(y-peak)<1e-5 else .3*y+.7*surface
        else:ny=surface-.025 if y>.61 else y
        v['position']=(x*factor,ny,z*factor)
    normals=[[0.,0.,0.]for _ in b['vertices']]
    for k in range(0,len(b['indices']),3):
        ids=b['indices'][k:k+3];a,p,q=[b['vertices'][i]['position']for i in ids];u=[p[j]-a[j]for j in range(3)];v=[q[j]-a[j]for j in range(3)];n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);assert sum(x*x for x in n)>1e-12
        for i in ids:
            for j in range(3):normals[i][j]+=n[j]
    for v,n in zip(b['vertices'],normals):
        length=math.sqrt(sum(q*q for q in n));assert length>1e-8;v['normal']=ns['packed_normal']([q/length for q in n])
points=[v['position']for b in buffers for v in b['vertices']];actual=[min(p[k]for p in points)for k in range(3)]+[max(p[k]for p in points)for k in range(3)];assert max(abs(x-y)for x,y in zip(actual,bd))<1e-5
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');lib=resources/'library/fluxara_driftlib_volcano_organic_cliff_v22';lib.mkdir(exist_ok=True);visual=lib/'vr_v22_organic_grass_stone_cliff.spm';visual.write_bytes(ns['replace_buffers'](d,{i:b for i,b in enumerate(buffers)}))
(lib/'node.xml').write_text(f'<scene><object id="OrganicCliff" type="animation" model="{visual.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');(lib/'materials.xml').write_text('<materials><material name="fluxara_volcano_stone_shared_v16.jpg" /></materials>')
main=parse(old/'volcano_track.spm');tris=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in tris(b)]
scene=E.parse(c/'scene.xml')
for e in scene.getroot().findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));sc=list(map(float,e.get('scale').split()))
        for b in parse(c/e.get('model'))['buffers']:road +=[[tuple(p[k]*sc[k]+xyz[k]for k in range(3))for p in t]for t in tris(b)]
center_y=(bd[1]+bd[4])/2;placements=[]
for row in source_proof['placements']:
    e=scene.getroot().find(f"library[@id='{row['id']}']");assert e.get('name')==Path(source_proof['adaptedSharedLibrary']).name
    xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()));hpr=list(map(float,e.get('hpr').split()));assert hpr[0]==hpr[2]==0
    for width,height in [(1.55,.83),(1.35,.88),(1.15,.93),(1.,1.)]:
        nscl=[scale[0]*width,scale[1]*height,scale[2]*width];nxyz=[xyz[0],xyz[1]+peak*(scale[1]-nscl[1]),xyz[2]]
        center=[nxyz[0],nxyz[1]+center_y*nscl[1],nxyz[2]]
        radius=max(math.sqrt((p[0]*nscl[0])**2+((p[1]-center_y)*nscl[1])**2+(p[2]*nscl[2])**2)for p in points)
        distance=min(point_triangle_distance(center,t)for t in road);margin=distance-radius
        if margin>2.5:break
    assert margin>2.5,(row['id'],margin);assert nxyz[1]+bd[1]*nscl[1]<row['groundHeight']-.4
    e.set('name',lib.name);e.set('xyz',' '.join(f'{x:.8f}'for x in nxyz));e.set('scale',' '.join(f'{x:.8f}'for x in nscl))
    placements.append({'id':row['id'],'library':lib.name,'oldXYZ':xyz,'xyz':nxyz,'oldScale':scale,'scale':nscl,'hpr':hpr,'widthMultiplier':width,'heightMultiplier':height,'topHeightUnchanged':True,'sourceGroundHeight':row['groundHeight'],'footingDepthBelowSourceGround':row['groundHeight']-(nxyz[1]+bd[1]*nscl[1]),'boundingSphereCentre':center,'boundingSphereRadius':radius,'minimumProtectedRoadDistance3D':distance,'roadClearanceBeyondBoundingSphere':margin})
scene.write(c/'scene.xml',encoding='unicode');assert len(placements)==58
source_weight=source_proof['sourceModelWithTextureBytes'];stone=Path(source_proof['globalStoneAlias']);new_weight=visual.stat().st_size+stone.stat().st_size;assert new_weight<=source_weight*1.2
proof={'baseCandidate':'V21','sourcePoolObjectIds':['volcano-fidelity-v16-grasslip','volcano-fidelity-v16-stonebody'],'sourcePooledModel':str(source),'sourceModelSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'newSharedCliffLibrary':str(lib),'newSharedCliffModel':str(visual),'sourceAndTargetLocalBounds':list(bd),'vertices':sum(len(b['vertices'])for b in buffers),'triangles':sum(len(b['indices'])//3 for b in buffers),'sourcePoolModelWithTexturesBytes':source_weight,'adaptedModelWithTextureBytes':new_weight,'modelWithTextureChangePercent':(new_weight/source_weight-1)*100,'existingStoneUVsAndPixelsRetained':True,'newTexturePixels':False,'newMaterialCount':0,'placements':placements,'protectedDrivingTriangles':len(road),'minimumRoadSphereMarginMeters':min(q['roadClearanceBeyondBoundingSphere']for q in placements),'productionIntegrated':False,'referenceAcceptance':False}
(w/'cliff-changes.json').write_text(json.dumps(proof,indent=2));print('V22_WIDER_ORGANIC_CLIFFS_READY',len(placements),proof['minimumRoadSphereMarginMeters'],flush=True)
