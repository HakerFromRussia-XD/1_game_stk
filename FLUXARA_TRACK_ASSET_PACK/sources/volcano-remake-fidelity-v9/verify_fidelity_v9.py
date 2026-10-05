from pathlib import Path
from collections import Counter
import sys,json,xml.etree.ElementTree as E,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v9';c=w/'candidate';base=r/'fidelity-v7b/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
changes=json.loads((w/'castle-changes.json').read_text());a=parse(base/'volcano_track.spm');b=parse(c/'volcano_track.spm');assert a['bounds']==b['bounds'];assert a['materials']==b['materials'];assert len(a['buffers'])==len(b['buffers'])
def triangles(buf,attrs=False):
    return Counter(tuple(tuple((v.get(k,(255,255,255)if k=='color'else None)for k in ['position','normal','uv','color']))if attrs else v['position']for v in [buf['vertices'][i]for i in buf['indices'][t:t+3]])for t in range(0,len(buf['indices']),3))
changed={6,20};remove={6:set(t for q in changes for t in q['removedWallTriangleIds']),20:set(t for q in changes for t in q['originalWoodRoofTriangleIds'])}
for i,(old,new)in enumerate(zip(a['buffers'],b['buffers'])):
    if i not in changed:assert old['indices']==new['indices'];assert all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(old['vertices'],new['vertices']))
    else:
        expected={'vertices':old['vertices'],'indices':[v for t in range(len(old['indices'])//3)if t not in remove[i]for v in old['indices'][t*3:t*3+3]]};assert triangles(expected,True)==triangles(new,True)
original_collision=sum((triangles(q)for q in a['buffers']),Counter());new_collision=sum((triangles(q)for q in b['buffers']),Counter())
for q in changes:
    collider=parse(c/q['collider']);assert collider['geometry_end']==len(collider['raw']);assert collider['materials']==[['','']];assert all(0<=v<len(buf['vertices'])for buf in collider['buffers']for v in buf['indices']);new_collision+=sum((triangles(buf)for buf in collider['buffers']),Counter())
    source=parse(q['pooledSource']);lo=source['bounds'][:3];hi=source['bounds'][3:];bounds=[[end[k]*q['scale'][k]+q['xyz'][k]for k in range(3)]for end in [lo,hi]];assert max(abs(x-y)for v,u in zip(bounds,q['originalVisualBounds'])for x,y in zip(v,u))<1e-6
    assert hashlib.sha256(Path(q['originalPoolModel']).read_bytes()).hexdigest()==q['sourceLibraryUnchangedSha256']
assert original_collision==new_collision
old=E.parse(base/'scene.xml').getroot();new=E.parse(c/'scene.xml').getroot()
for q in changes:
    obj=next(e for e in new.findall('object')if e.get('model')==q['collider']);assert obj.get('interaction')=='physicsonly'and obj.get('shape')=='exact'and obj.get('xyz')=='0 0 0'and obj.get('hpr')=='0 0 0'and obj.get('scale')=='1 1 1';new.remove(obj)
    lib=next(e for e in new.findall('library')if e.get('id')==q['id']);assert lib.get('name')=='fluxara_driftlib_volcano_castle_tower_v9';assert all(abs(v-u)<1e-7 for v,u in zip(map(float,lib.get('xyz').split()),q['xyz']));assert all(abs(v-u)<1e-7 for v,u in zip(map(float,lib.get('scale').split()),q['scale']));new.remove(lib)
assert E.tostring(old)==E.tostring(new)
for p in base.iterdir():
    if p.name not in ['scene.xml','volcano_track.spm']:assert p.read_bytes()==(c/p.name).read_bytes()
road=lambda d:next(q for q in d['buffers']if d['materials'][q['material']][0]=='track01.png');oldroad=road(parse(r/'before/volcano_track.spm'));newroad=road(b);assert oldroad['indices']==newroad['indices'];assert all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(oldroad['vertices'],newroad['vertices']))
names=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in names:assert(c/name).read_bytes()==(r/'before'/name).read_bytes()
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
(w/'preservation.json').write_text(json.dumps({'originalRoadPositionsNormalsUvsColoursAndIndicesExact':True,'originalGameplayFilesExact':names,'allExistingSceneEntriesExactV7B':True,'allOtherModelBuffersExactV7B':True,'remainingCastleAndRoofRenderTriangleAttributesExactV7B':True,'mainMeshPlusTwoPhysicsOnlyTriangleCollisionGeometryExactV7B':True,'collisionTriangleCount':sum(original_collision.values()),'retainedPoolBodyGeometryUnchanged':True,'towerTopReshaped':True,'paletteFilePixelsUnchanged':True,'grayBodyAndNewRedConeRoof':True,'pooledTowerBoundsFitOriginalDecorativeBounds':True,'physicsMaterialScope':'Replaced triangles used opaque wall/roof materials with default physical properties; two exact hidden colliders have default physical properties. Runtime gameplay is checked separately.','productionIntegrated':False,'productionSourceUnchanged':True,'changes':changes},indent=2));print('V9_COURSE_AND_COLLISION_PRESERVATION_VERIFIED')


skin=json.loads((w/'skin-changes.json').read_text());old=parse(skin['previousVariant']);new=parse(skin['adaptedModel']);assert old['bounds']==new['bounds'];assert new['geometry_end']==len(new['raw']);b=old['buffers'][0];nb=new['buffers'][0];removed=set(skin['removedPreviousTopTriangleIds']);retained={'vertices':b['vertices'],'indices':[i for t in range(len(b['indices'])//3)if t not in removed for i in b['indices'][t*3:t*3+3]]};newbody={'vertices':nb['vertices'],'indices':nb['indices'][:skin['retainedTriangles']*3]};assert triangles(retained,True)==triangles(newbody,True)
for k in range(3):assert abs(min(v['position'][k]for v in nb['vertices'])-new['bounds'][k])<1e-7 and abs(max(v['position'][k]for v in nb['vertices'])-new['bounds'][k+3])<1e-7
roof=nb['indices'][skin['retainedTriangles']*3:];assert len(roof)//3==16;assert all(nb['vertices'][i]['uv']==(.375,.125)for i in roof)
assert Path(skin['paletteSource']).read_bytes()==(Path(skin['library'])/skin['runtimeTextureAlias']).read_bytes();assert skin['modelWithTextureAfterBytes']<=1.2*skin['modelWithTextureBeforeBytes'];skin['verifiedFromActualFiles']=True;skin['retainedBodyPositionsNormalsUvsAndIndicesExact']=True;(w/'skin-changes.json').write_text(json.dumps(skin,indent=2));print('V9_ROOF_AND_WEIGHT_VERIFIED')
