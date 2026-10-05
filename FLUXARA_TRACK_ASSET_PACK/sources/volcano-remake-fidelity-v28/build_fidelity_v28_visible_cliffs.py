from pathlib import Path
import copy,hashlib,json,math,shutil,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v28';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v27/candidate',c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
parts=json.loads((r/'fidelity-v27/column-changes.json').read_text())['parts'];buffers=[parse(q['model'])['buffers'][0]for q in parts]
main=parse(c/'volcano_track.spm');original=parse(r/'fidelity-v24/candidate/volcano_track.spm')['buffers'][3]
def sub(a,b):return tuple(a[k]-b[k]for k in range(3))
def add(a,b):return tuple(a[k]+b[k]for k in range(3))
def mul(a,t):return tuple(q*t for q in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def closest(p,a,b,c):
    ab=sub(b,a);ac=sub(c,a);ap=sub(p,a);d1=dot(ab,ap);d2=dot(ac,ap)
    if d1<=0 and d2<=0:return a
    bp=sub(p,b);d3=dot(ab,bp);d4=dot(ac,bp)
    if d3>=0 and d4<=d3:return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:return add(a,mul(ab,d1/(d1-d3)))
    cp=sub(p,c);d5=dot(ab,cp);d6=dot(ac,cp)
    if d6>=0 and d5<=d6:return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:return add(a,mul(ac,d2/(d2-d6)))
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:return add(b,mul(sub(c,b),(d4-d3)/((d4-d3)+(d5-d6))))
    den=1/(va+vb+vc);return add(a,add(mul(ab,vb*den),mul(ac,vc*den)))
def normal(v):return tuple((q-1024 if q>511 else q)/511 for q in [(v['normal']>>s)&1023 for s in [0,10,20]])
def bounds(pp):return [min(v[k]for v in pp)for k in range(3)]+[max(v[k]for v in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
walls=[]
for j in range(0,len(original['indices']),3):
    vv=[original['vertices'][i]for i in original['indices'][j:j+3]];a,b,d=[v['position']for v in vv];u=sub(b,a);v=sub(d,a)
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);length=math.sqrt(dot(n,n))
    if not length:continue
    n=mul(n,1/length);average=tuple(sum(normal(v)[k]for v in vv)for k in range(3))
    if dot(n,average)<0:n=mul(n,-1)
    horizontal=math.hypot(n[0],n[2])
    if horizontal>.55:walls.append(([a,b,d],(n[0]/horizontal,0,n[2]/horizontal)))
scene=E.parse(c/'scene.xml');root=scene.getroot()
road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in root.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(q[k]*size[k]+pos[k]for k in range(3))for q in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
boxes=[bounds(t)for t in road];changes=[];skipped=[]
def margin(e,buf):
    pos=list(map(float,e.get('xyz').split()));s=list(map(float,e.get('scale').split()));a=math.radians(float(e.get('hpr').split()[1]));co,si=math.cos(a),math.sin(a)
    world=lambda v:(pos[0]+co*v[0]*s[0]+si*v[2]*s[2],pos[1]+v[1]*s[1],pos[2]-si*v[0]*s[0]+co*v[2]*s[2])
    best=1e9
    for tri in triangles(buf):
        pp=[world(v)for v in tri];box=bounds(pp)
        for rb,rt in zip(boxes,road):
            lower=math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))
            if lower<best:best=min(best,triangle_distance(pp,rt))
    return best
for q in json.loads((r/'fidelity-v27/column-changes.json').read_text())['placements']:
    grass=root.find(f'library[@id="{q["grass"]["id"]}"]');stone=root.find(f'library[@id="{q["stone"]["id"]}"]')
    pos=list(map(float,stone.get('xyz').split()));s=list(map(float,stone.get('scale').split()));center=(pos[0],pos[1]+(parts[1]['localBounds'][1]+parts[1]['localBounds'][4])/2*s[1],pos[2])
    distance,point,n=min((math.dist(center,closest(center,*t)),closest(center,*t),n)for t,n in walls)
    radius=max((parts[1]['localBounds'][3]-parts[1]['localBounds'][0])*s[0],(parts[1]['localBounds'][5]-parts[1]['localBounds'][2])*s[2])/2
    new=(point[0]+n[0]*(radius*.45+1),point[2]+n[2]*(radius*.45+1));delta=(new[0]-pos[0],new[1]-pos[2])
    if math.hypot(*delta)>25 or math.hypot(*delta)<2:
        skipped.append({'id':q['source']['id'],'reason':'Move too large or unnecessary','distance':math.hypot(*delta)});continue
    originals=[dict(grass.attrib),dict(stone.attrib)]
    for e in [grass,stone]:
        xyz=list(map(float,e.get('xyz').split()));xyz[0]+=delta[0];xyz[2]+=delta[1];e.set('xyz',' '.join(f'{v:.8f}'for v in xyz))
    clearance=min(margin(grass,buffers[0]),margin(stone,buffers[1]))
    if clearance<1:
        grass.attrib.clear();grass.attrib.update(originals[0]);stone.attrib.clear();stone.attrib.update(originals[1]);skipped.append({'id':q['source']['id'],'reason':'Protected road clearance','candidateClearanceMeters':clearance});continue
    changes.append({'id':q['source']['id'],'before':originals,'after':[dict(grass.attrib),dict(stone.attrib)],'horizontalDisplacementMeters':math.hypot(*delta),'outwardNormal':n,'originalWallClosestPoint':point,'wallCenterDistanceBeforeMeters':distance,'exactAllPartTriangleRoadMarginMeters':clearance})
    print('VISIBLE_CLIFF_MOVED',q['source']['id'],math.hypot(*delta),clearance,flush=True)
assert len(changes)>8,len(changes)
scene.write(c/'scene.xml',encoding='unicode')
(w/'visible-cliff-changes.json').write_text(json.dumps({'baseCandidate':'V27','parts':parts,'changedGroups':changes,'skippedGroups':skipped,'newSharedModels':0,'newTextures':0,'newMaterials':0,'newGeometry':False,'minimumChangedGroupRoadMarginMeters':min(q['exactAllPartTriangleRoadMarginMeters']for q in changes),'sourceLocalGeometryBoundsOriginsAxesUnchanged':True,'changedAddedInstanceXZPositions':True,'sourceSceneObjectsAndGameplayControlsUnchanged':True,'productionIntegrated':False,'referenceAcceptance':False},indent=2))
print('V28_VISIBLE_CLIFF_PLACEMENTS_READY',len(changes),flush=True)
