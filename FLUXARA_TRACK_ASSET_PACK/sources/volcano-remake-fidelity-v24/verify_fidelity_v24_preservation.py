from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v24';c=w/'candidate';old=r/'fidelity-v23/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
p=json.loads((w/'atmosphere-changes.json').read_text());changed={q['model']for q in p['smoke']}|{'scene.xml'}
assert {q.name for q in c.iterdir()}=={q.name for q in old.iterdir()}
for f in old.iterdir():
    if f.is_file()and f.name not in changed:assert f.read_bytes()==(c/f.name).read_bytes(),f.name
for q in p['smoke']:
    a=parse(old/q['model']);b=parse(c/q['model']);av=a['buffers'][0];bv=b['buffers'][0]
    assert a['bounds']==b['bounds']and av['indices']==bv['indices']
    assert len(av['vertices'])==len(bv['vertices'])
    assert all(x['position']==y['position']and x['normal']==y['normal']for x,y in zip(av['vertices'],bv['vertices']))
    assert b['materials']==[['','']]and all('uv'not in v and all(0<=x<=255 for x in v['color'])for v in bv['vertices'])
    assert (c/q['model']).stat().st_size==q['adaptedModelWithTextureBytes']<=1.2*q['originalModelWithTextureBytes']
scene=E.parse(c/'scene.xml').getroot();before=E.parse(old/'scene.xml').getroot();added=[]
for q in p['newTorchPlacements']:
    e=scene.find(f'library[@id="{q["id"]}"]');assert e is not None and e.get('name')==Path(p['existingTorchLibrary']).name
    assert e.get('hpr')=='0 180 0';added.append(e);scene.remove(e)
assert E.tostring(scene)==E.tostring(before)
lib=Path(p['existingTorchLibrary']);pack=Path(p['existingTorchPack'])
for f in lib.iterdir():
    if f.is_file():assert f.read_bytes()==(pack/f.name).read_bytes(),f
model=lib/'fluxara_driftlib_aztekTorch_a_main.spm';assert hashlib.sha256(model.read_bytes()).hexdigest()==p['torchSourceModelSha256']
td=parse(model);main=parse(c/'volcano_track.spm')
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
protected=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        protected += [[tuple(p[k]*scale[k]+xyz[k]for k in range(3))for p in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
margins=[]
for e in added:
    pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()));assert size[0]==size[1]==size[2]
    center=tuple(pos[k]+size[k]*(td['bounds'][k]+td['bounds'][k+3])/2*(1 if k==1 else -1)for k in range(3))
    radius=size[0]*math.sqrt(sum(((td['bounds'][k+3]-td['bounds'][k])/2)**2 for k in range(3)))
    margins.append(min(point_triangle_distance(center,t)for t in protected)-radius)
assert min(margins)>2 and len(protected)==2032
previous=json.loads((r/'fidelity-v23/preservation-verification.json').read_text());size=lambda f:sum(q.stat().st_size for q in f.rglob('*')if q.is_file())
total=size(c)+previous['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+previous['newGlobalTextureBytes'];assert total<previous['v1Bytes']
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
for f in(r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
proof={'baseCandidate':'V23','allOtherCandidateModelsTexturesCollisionsControlsExactV23':True,'allSmokeVertexPositionsNormalsIndicesBoundsAndExistingPlacementsExactV23':True,'smokeChangesOnlyRGBAndUnusedTextureCoordinates':True,'allExistingSceneNodesExactV23':True,'newTorchCoordinatePlacements':6,'existingTorchLibraryPackAndModelUnmodified':True,'torchModelWithTexturesWeightChangePercent':0,'independentTorchProtectedRoadSphereMarginMeters':min(margins),'protectedDrivingTriangles':len(protected),'originalStoneGeometryUVsAndPixelFilesUnchanged':True,'newTextureFiles':0,'newImagePixels':False,'newAuthoredMaterials':0,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':previous['newSharedLibraryBytesIncludingRetainedHistoricalVariants'],'newGlobalTextureBytes':previous['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':previous['v1Bytes'],'savingBytesVsV1':previous['v1Bytes']-total,'changeBytesAgainstIntermediateV23':total-previous['candidateIncludingNewSharedBytes'],'directReusedExistingTorchRuntimeLibraryBytes':size(lib),'directReusedTorchBytesAddedToInstalledApp':0,'smokeObjectModelWithTextureUpper20PercentPassed':True,'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V24_GEOMETRY_AND_WEIGHT_VERIFIED',total,min(margins),flush=True)
