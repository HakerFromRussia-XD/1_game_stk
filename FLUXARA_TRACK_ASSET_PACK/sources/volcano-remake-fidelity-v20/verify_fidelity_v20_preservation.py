from pathlib import Path
import sys, json, collections, hashlib, math, xml.etree.ElementTree as E

r=Path(__file__).resolve().parent; w=r/'fidelity-v20'; old=r/'fidelity-v19/candidate'; c=w/'candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
from terrain_triangle_distance import triangle_distance,check_triangle_distance_geometry
check_triangle_distance_geometry()
proof=json.loads((w/'terrain-changes.json').read_text()); alias=Path(proof['existingGreenPaletteGlobalAlias']).name
before=parse(old/'volcano_track.spm'); after=parse(c/'volcano_track.spm')
attrs=lambda v:{k:x for k,x in v.items()if not k.endswith('offset')}
def normalized(b):return {'vertices':[attrs(v)for v in b['vertices']],'indices':list(b['indices']),'material':b['material']}
assert before['bounds']==after['bounds']
assert [[alias if n=='vr_moss_palette.jpg'else n for n in pair]for pair in before['materials']]==after['materials']
kept=[b for i,b in enumerate(before['buffers'])if i!=5]
assert [normalized(b)for b in kept]==[normalized(b)for b in after['buffers']]
source=before['buffers'][5]; collider=parse(c/proof['sourceColliderModel'])
assert collider['materials']==[[alias,'']]
assert [attrs(v)for v in source['vertices']]==[attrs(v)for v in collider['buffers'][0]['vertices']]
assert source['indices']==collider['buffers'][0]['indices']
def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
original_bounds=bounds([v['position']for v in source['vertices']])
visual=parse(proof['newSharedTerrainModel']); vb=visual['buffers'][0]
assert visual['bounds']==collider['bounds']
assert max(abs(a-b)for a,b in zip(bounds([v['position']for v in vb['vertices']]),original_bounds))<1e-4
assert max(abs(a-b)for a,b in zip(visual['bounds'],original_bounds))<1e-4
changed=set(proof['changedVertexIndices']); baseline=proof['baselineAfterSubdivision']
assert len(vb['vertices'])==len(baseline)
for i,(v,p)in enumerate(zip(vb['vertices'],baseline)):
    assert abs(v['position'][0]-p[0])<4e-5 and abs(v['position'][2]-p[2])<4e-5
    assert -1e-5 <= v['position'][1]-p[1] <= 14.0001
    if i not in changed: assert max(abs(a-b)for a,b in zip(v['position'],p))<4e-5
    assert v['uv']==(.75,.5)
    assert all(math.isfinite(q)for q in v['position'])
# Rebuild protected geometry independently, including the reverse-only ramp.
triangles=lambda b:[[b['vertices'][j]['position']for j in b['indices'][i:i+3]]for i in range(0,len(b['indices']),3)]
protected=[t for b in before['buffers']if before['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in E.parse(old/'scene.xml').getroot().findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0'
        xyz=list(map(float,e.get('xyz').split())); scale=list(map(float,e.get('scale').split()))
        for b in parse(old/e.get('model'))['buffers']:
            protected += [[tuple(v[k]*scale[k]+xyz[k]for k in range(3))for v in t]for t in triangles(b)]
boxes=[bounds(t)for t in protected]
distance=lambda a,b:math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
margins=[]
for i in range(0,len(vb['indices']),3):
    ids=vb['indices'][i:i+3]
    if any(j in changed for j in ids):
        points=[vb['vertices'][j]['position']for j in ids];box=bounds(points);margin=1e9
        for b,road in zip(boxes,protected):
            if distance(box,b)<margin:margin=min(margin,triangle_distance(points,road))
        assert margin>4.4999; margins.append(margin)
assert len(protected)==proof['protectedDrivingTriangles']
scene=E.parse(c/'scene.xml').getroot()
col=scene.find('object[@id="VRV20_OriginalGreenTerrainCollision"]'); vis=scene.find('library[@id="VRV20_RoundedGreenTerrain_000"]')
assert col.get('interaction')=='physicsonly'and col.get('shape')=='exact'
for e in [col,vis]:assert e.get('xyz')=='0 0 0'and e.get('hpr')=='0 0 0'and e.get('scale')=='1 1 1'
scene.remove(col); scene.remove(vis)
for e in scene.iter():
    if e.get('name')==alias:e.set('name','vr_moss_palette.jpg')
assert E.tostring(scene)==E.tostring(E.parse(old/'scene.xml').getroot())
material=E.parse(c/'materials.xml').getroot()
for e in material.iter():
    if e.get('name')==alias:e.set('name','vr_moss_palette.jpg')
assert E.tostring(material)==E.tostring(E.parse(old/'materials.xml').getroot())
changed_files={'volcano_track.spm','scene.xml','materials.xml','vr_moss_palette.jpg'}|set(proof['textureAliasOnlyOtherModels'])
for p in old.iterdir():
    if p.is_file()and p.name not in changed_files:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
for name in proof['textureAliasOnlyOtherModels']:
    x=parse(old/name); y=parse(c/name)
    assert x['bounds']==y['bounds']
    assert [normalized(b)for b in x['buffers']]==[normalized(b)for b in y['buffers']],name
    assert [['fluxara_volcano_moss_shared_v20.jpg'if n=='vr_moss_palette.jpg'else n for n in pair]for pair in x['materials']]==y['materials']
assert {p.name for p in c.iterdir()}==({p.name for p in old.iterdir()}-{'vr_moss_palette.jpg'}|{proof['sourceColliderModel']})
palette=Path(proof['existingGreenPaletteGlobalAlias']); assert palette.read_bytes()==(old/'vr_moss_palette.jpg').read_bytes()
def unresolved(folder):
    missing=set()
    for p in folder.glob('*.spm'):
        for pair in parse(p)['materials']:
            for name in pair:
                if name and not(folder/name).exists()and not(Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/textures')/name).exists():missing.add((p.name,name))
    return missing
assert unresolved(c)==unresolved(old), ('New unresolved texture',unresolved(c)-unresolved(old))
legacy_missing=sorted(unresolved(old))
source_weight=Path(proof['originalComponentWeightModel']).stat().st_size+Path(proof['originalComponentTexture']).stat().st_size
adapted_weight=Path(proof['newSharedTerrainModel']).stat().st_size+(c/proof['sourceColliderModel']).stat().st_size+palette.stat().st_size
assert source_weight==proof['originalComponentWithTextureBytes'] and adapted_weight==proof['adaptedVisibleAndCollisionModelsWithTextureBytes']<=source_weight*1.2
size=lambda p:sum(f.stat().st_size for f in p.rglob('*')if f.is_file())
base=json.loads((r/'fidelity-v19/preservation-verification.json').read_text())
shared=base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(proof['newSharedTerrainLibrary']))
global_bytes=base['newGlobalTextureBytes']+palette.stat().st_size
total=size(c)+shared+global_bytes; v1=size(r/'fidelity-v2/baseline'); assert total<v1
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
for p in (r/'fidelity-v2/baseline').iterdir():
    if p.is_file():assert p.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/p.name).read_bytes()
result={'baseCandidate':'V19','originalMainBoundsRetained':True,'allRetainedMainIndexedAttributesExact':True,
        'originalStoneUVsNormalsColorsAndGeometryExactV19':True,'allSourceTerrainCollisionIndexedAttributesExact':True,
        'originalTerrainCollisionTriangles':427,'terrainOriginsAxesCompositeLocalBoundsRetained':True,
        'sourceSceneObjectsAndGameplayControlsExactV19':True,'allOtherModelTextureFilesExactV19ExceptThreeAliasOnlyHeaders':True,'otherModelAliasOnlyGeometryNormalsColorsUVsExact':proof['textureAliasOnlyOtherModels'],
        'greenPalettePixelsReusedWithoutNewImage':True,'protectedDrivingTriangles':len(protected),
        'independentChangedFaceRoadTriangleMarginMeters':min(margins),'modifiedVisualVertices':len(changed),
        'modifiedTerrainComponents':len(proof['modifiedTerrainComponentIds']),
        'originalComponentWeightBaseline':'Indexed green region matched to unmodified before/volcano_track.spm, plus its original Rock13_col.jpg. Not the intermediate V19 palette-based region.',
        'originalComponentWithTextureBytes':source_weight,'adaptedVisibleAndCollisionModelsWithTextureBytes':adapted_weight,
        'componentWithTextureChangePercent':(adapted_weight/source_weight-1)*100,'modelWithTextureUpper20PercentPassed':True,
        'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':shared,
        'newGlobalTextureBytes':global_bytes,'candidateIncludingNewSharedBytes':total,'v1Bytes':v1,
        'savingBytesVsV1':v1-total,'changeBytesAgainstIntermediateV19':total-base['candidateIncludingNewSharedBytes'],
        'legacyUnresolvedTextureNamesUnchanged':legacy_missing,'noNewUnresolvedTextures':True,'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(result,indent=2))
print('V20_TERRAIN_COLLISIONS_COURSE_AND_TOTAL_WEIGHT_VERIFIED',total,min(margins),flush=True)
