from pathlib import Path
import sys,json,math,struct,collections,copy,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v21';old=r/'fidelity-v20/candidate';c=w/'candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,check_triangle_distance_geometry
check_triangle_distance_geometry(); proof=json.loads((w/'crest-changes.json').read_text())
d=parse(old/'volcano_track.spm');new=parse(c/'volcano_track.spm');clean=lambda v:{k:x for k,x in v.items()if not k.endswith('offset')}
norm=lambda b:([clean(v)for v in b['vertices']],list(b['indices']),b['material'])
assert d['bounds']==new['bounds'] and d['materials']==new['materials']
assert [norm(b)for i,b in enumerate(d['buffers'])if i!=3]==[norm(b)for b in new['buffers']]
col=parse(c/proof['sourceColliderModel']); original=d['buffers'][3]
assert [clean(v)for v in original['vertices']]==[clean(v)for v in col['buffers'][0]['vertices']]
assert original['indices']==col['buffers'][0]['indices'] and col['materials']==[d['materials'][original['material']]]
scene=E.parse(c/'scene.xml').getroot();physics=scene.find('object[@id="VRV21_OriginalCentralCrestCollision"]');vis=scene.find('library[@id="VRV21_RoundedCentralCrest_000"]')
assert physics.get('interaction')=='physicsonly' and physics.get('shape')=='exact'
for e in [physics,vis]:assert e.get('xyz')=='0 0 0'and e.get('hpr')=='0 0 0'and e.get('scale')=='1 1 1'
scene.remove(physics);scene.remove(vis);assert E.tostring(scene)==E.tostring(E.parse(old/'scene.xml').getroot())
for p in old.iterdir():
    if p.is_file()and p.name not in ['volcano_track.spm','scene.xml']:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
assert {p.name for p in c.iterdir()}=={p.name for p in old.iterdir()}|{proof['sourceColliderModel']}
visual=parse(proof['newSharedCrestModel']); assert len(visual['buffers'])==2
def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
source_box=bounds([v['position']for b in d['buffers'][2:4]for v in b['vertices']])
target_box=bounds([v['position']for b in [d['buffers'][2]]+visual['buffers']for v in b['vertices']])
assert max(abs(a-b)for a,b in zip(source_box,target_box))<1e-4
tris=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
road=[t for b in d['buffers']if d['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in tris(b)]
for e in E.parse(old/'scene.xml').getroot().findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        for b in parse(old/e.get('model'))['buffers']:road +=[[tuple(p[k]*scale[k]+xyz[k]for k in range(3))for p in t]for t in tris(b)]
boxes=[bounds(t)for t in road];dist=lambda a,b:math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
margins=[]
for b in visual['buffers']:
    for t in tris(b):
        bb=bounds(t);margin=1e9
        for rb,rt in zip(boxes,road):
            if dist(bb,rb)<margin:margin=min(margin,triangle_distance(t,rt))
        assert margin>4.5,margin;margins.append(margin)
for pair in visual['materials']:
    for name in pair:
        if name:assert Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/textures',name).is_file()
# Match the complete original central object, including its stone side, to before.
before=parse(r/'before/volcano_track.spm');key=lambda b,t:tuple(b['vertices'][j]['position']for j in b['indices'][3*t:3*t+3])
need=collections.Counter(key(b,t)for b in d['buffers'][2:4]for t in range(len(b['indices'])//3)); parts=[];textures=set()
for b in before['buffers']:
    selected=[]
    for t in range(len(b['indices'])//3):
        k=key(b,t)
        if need[k]:selected.append(t);need[k]-=1
    if not selected:continue
    pair=before['materials'][b['material']];textures.update(n for n in pair if n)
    ids=sorted({i for t in selected for i in b['indices'][t*3:t*3+3]});remap={j:i for i,j in enumerate(ids)}
    parts.append(({'vertices':[copy.deepcopy(b['vertices'][i])for i in ids],'indices':[remap[j]for t in selected for j in b['indices'][t*3:t*3+3]],'material':len(parts)},pair))
assert not any(need.values());assert sum(len(b['indices'])//3 for b,pair in parts)==72
ns={'math':math,'struct':struct};helper=(r/'fidelity_v2.py').read_text();exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*source_box)+struct.pack('<H',len(parts)))
for b,pair in parts:
    for n in pair:v=n.encode();raw+=bytes([len(v)])+v
raw+=struct.pack('<HH',1,len(parts))
for b,pair in parts:raw+=ns['encode_buffer'](b,[p for _,p in parts])
source=w/'original-central-object-before.spm';source.write_bytes(raw)
original_weight=source.stat().st_size+sum((r/'before'/n).stat().st_size for n in textures)
stone_part=d['buffers'][2];stone_names=[d['materials'][stone_part['material']]]
retained_raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*bounds([v['position']for v in stone_part['vertices']]))+struct.pack('<H',1))
for name in stone_names[0]:value=name.encode();retained_raw+=bytes([len(value)])+value
retained_raw+=struct.pack('<HH',1,1)+ns['encode_buffer']({**stone_part,'material':0},stone_names)
retained_path=w/'retained-central-stone-component.spm';retained_path.write_bytes(retained_raw)
adapted_weight=Path(proof['newSharedCrestModel']).stat().st_size+(c/proof['sourceColliderModel']).stat().st_size+retained_path.stat().st_size+sum(Path(p).stat().st_size for p in proof['existingRuntimeTextures'])
assert adapted_weight<=original_weight*1.2
size=lambda p:sum(f.stat().st_size for f in p.rglob('*')if f.is_file())
base=json.loads((r/'fidelity-v20/preservation-verification.json').read_text());shared=base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(proof['newSharedCrestLibrary']));global_bytes=base['newGlobalTextureBytes'];total=size(c)+shared+global_bytes;v1=size(r/'fidelity-v2/baseline');assert total<v1
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
for p in (r/'fidelity-v2/baseline').iterdir():
    if p.is_file():assert p.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/p.name).read_bytes()
result={'baseCandidate':'V20','allRetainedMainIndexedAttributesExact':True,'currentStoneTextureUVNormalsColorsAndGeometryExactV20':True,
        'allSourceCrestCollisionIndexedAttributesExact':True,'originalCrestCollisionTriangles':8,'centralObjectCompositeBoundsOriginAxesRetained':True,
        'sourceSceneObjectsAndGameplayControlsExactV20':True,'allOtherFilesExactV20':True,'existingGreenAndStonePixelsReused':True,
        'protectedDrivingTriangles':len(road),'independentCrestRoadTriangleMarginMeters':min(margins),
        'originalCentralObjectModelWithTextureBytes':original_weight,'adaptedCentralObjectIncludingRetainedStoneAndCollisionWithTexturesBytes':adapted_weight,
        'modelWithTextureUpper20PercentPassed':True,'modelWithTextureChangePercent':(adapted_weight/original_weight-1)*100,
        'sourceWeightBaseline':'Matched all 72 triangles to unmodified before/volcano_track.spm plus actual original referenced textures. Includes retained 64-triangle stone side in adapted weight.',
        'originalSourceTextureNames':sorted(textures),'originalSourceComponentModel':str(source),'retainedStoneComponentForWeightAccounting':str(retained_path),
        'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,'newGlobalTextureBytes':global_bytes,
        'candidateIncludingNewSharedBytes':total,'v1Bytes':v1,'savingBytesVsV1':v1-total,'changeBytesAgainstIntermediateV20':total-base['candidateIncludingNewSharedBytes'],
        'newTextureFiles':0,'newTexturePixels':False,'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(result,indent=2));print('V21_CREST_ROUTE_COLLISIONS_BOUNDS_AND_WEIGHT_VERIFIED',total,min(margins),original_weight,adapted_weight,flush=True)
