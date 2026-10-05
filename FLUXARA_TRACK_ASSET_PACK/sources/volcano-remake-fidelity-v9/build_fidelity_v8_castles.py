from pathlib import Path
import sys,copy,json,struct,math,shutil,xml.etree.ElementTree as E,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v8';w.mkdir(exist_ok=True);c=w/'candidate';shutil.copytree(r/'fidelity-v7b/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'fidelity_v2.py').read_text();ns={'struct':struct,'math':math};exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
d=parse(c/'volcano_track.spm');wall=d['buffers'][6];groups=ns['component_triangles'](wall);roof=d['buffers'][14];roofgroups=ns['component_triangles'](roof)
def points(b,ts):return [b['vertices'][i]['position']for t in ts for i in b['indices'][t*3:t*3+3]]
def bounds(ps):return [[min(p[k]for p in ps)for k in range(3)],[max(p[k]for p in ps)for k in range(3)]]
def subset(buffer,triangles,physics=False):
    indices=[i for t in sorted(triangles)for i in buffer['indices'][t*3:t*3+3]];used=sorted(set(indices));mapping={i:j for j,i in enumerate(used)}
    return {'vertices':[copy.deepcopy(buffer['vertices'][i])for i in used],'indices':[mapping[i]for i in indices],'material':0 if physics else buffer['material']}
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');lib='fluxara_driftlib_castle_tower_v1';model=repo/'iosApp/FluxaraResources/library'/lib/(lib+'_main.spm');source=parse(model);lo,hi=source['bounds'][:3],source['bounds'][3:];changes=[];remove={6:set(),14:set()};scene=E.parse(c/'scene.xml')
for n,body in enumerate([255,417]):
    bodybounds=bounds(points(wall,groups[body]));a,b=bodybounds
    selected=[]
    for j,ts in enumerate(groups):
        q,z=bounds(points(wall,ts))
        if j==body or (len(ts)<=30 and all(q[k]>=a[k]-.35 and z[k]<=b[k]+.35 for k in [0,2])and q[1]>=a[1]+(b[1]-a[1])*.55 and z[1]<=b[1]+2):selected.append(j)
    walltris={t for j in selected for t in groups[j]};rooftris=set()
    for ts in roofgroups:
        q,z=bounds(points(roof,ts));centre=[(x+y)/2 for x,y in zip(q,z)]
        if all(a[k]-.35<=centre[k]<=b[k]+.35 for k in [0,2])and q[1]>=a[1]+(b[1]-a[1])*.5 and z[1]<=b[1]+10:rooftris.update(ts)
    visualbounds=bounds(points(wall,walltris)+points(roof,rooftris));a,b=visualbounds;scale=[(b[k]-a[k])/(hi[k]-lo[k])for k in range(3)];xyz=[a[k]-lo[k]*scale[k]for k in range(3)]
    collider=subset(wall,walltris,True)
    if rooftris:
        extra=subset(roof,rooftris,True);offset=len(collider['vertices']);collider['vertices']+=extra['vertices'];collider['indices']+=[offset+i for i in extra['indices']]
    vertices=collider['vertices'];indices=collider['indices'];allbounds=bounds([v['position']for v in vertices]);raw=bytearray(b'SP'+bytes([10,1])+struct.pack('<6f',*(allbounds[0]+allbounds[1]))+struct.pack('<H',1)+b'\0\0'+struct.pack('<HHIIH',1,1,len(vertices),len(indices),0))
    for v in vertices:raw+=struct.pack('<3fI',*v['position'],v['normal'])
    raw+=struct.pack('<'+str(len(indices))+('H'if len(vertices)>255 else'B'),*indices);collname=f'vr_v8_tower_original_collision_{n}.spm';(c/collname).write_bytes(raw)
    obj=E.SubElement(scene.getroot(),'object',id=f'VRV8_OriginalTowerCollision_{n}',type='animation',model=collname,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',shape='exact',**{'skeletal-animation':'false'})
    instance=E.SubElement(scene.getroot(),'library',name=lib,id=f'VRV8_PooledTower_{n}',xyz=' '.join(f'{v:.9f}'for v in xyz),hpr='0 0 0',scale=' '.join(f'{v:.9f}'for v in scale))
    for i,ts in [(6,walltris),(14,rooftris)]:assert not(remove[i]&ts);remove[i].update(ts)
    changes.append({'id':instance.get('id'),'originalTowerBodyComponent':body,'originalWallComponents':selected,'removedWallTriangleIds':sorted(walltris),'removedRoofTriangleIds':sorted(rooftris),'originalVisualBounds':visualbounds,'pooledSource':str(model),'poolPrototypeId':'lap-v1-f4c4d2b2153a47ef','poolMaterialId':'lap-v1-material-00515707869a','pooledTriangles':429,'sourceLibraryUnchangedSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'xyz':xyz,'scale':scale,'collider':collname,'originalCollisionTriangles':len(indices)//3,'colliderBytes':len(raw),'scope':'Existing pooled tower fitted to original decorative tower bounds; source collision copied exactly, original course unchanged.'})
replacements={i:subset(d['buffers'][i],set(range(len(d['buffers'][i]['indices'])//3))-ts)for i,ts in remove.items()if ts}
(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](d,replacements));scene.write(c/'scene.xml',encoding='unicode');(w/'castle-changes.json').write_text(json.dumps(changes,indent=2));print('V8_POOLED_CASTLES_READY',len(changes),sum(len(v)for v in remove.values()),flush=True)
