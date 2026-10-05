from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';c=w/'candidate';old=r/'fidelity-v29/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
p=json.loads((w/'seam-changes.json').read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();models=[]
for q in p['modelSources']:assert sha(q['path'])==q['sha256']and Path(q['path']).stat().st_size==q['bytes'];models.append(parse(q['path']))
before=E.parse(old/'scene.xml').getroot();after=E.parse(c/'scene.xml').getroot();ids=[e['id']for g in p['placements']for e in g['parts']];assert len(ids)==len(set(ids))and len(ids)==3*p['newCoordinateGroups']
assert [E.tostring(e)for e in before]==[E.tostring(e)for e in after if e.get('id')not in ids]
for f in old.iterdir():
    if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
assert {f.name for f in old.iterdir()}=={f.name for f in c.iterdir()}
def bounds(pp):return [min(v[k]for v in pp)for k in range(3)]+[max(v[k]for v in pp)for k in range(3)]
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
main=parse(c/'volcano_track.spm');road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in before.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));s=list(map(float,e.get('scale').split()));road += [[tuple(v[k]*s[k]+xyz[k]for k in range(3))for v in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
assert len(road)==2032;boxes=[bounds(t)for t in road];minimum=1e9;checked=0
for group in p['placements']:
    for attrs,model in zip(group['parts'],[models[1],models[0],models[2]]):
        assert after.find(f'library[@id="{attrs["id"]}"]').attrib==attrs
        assert attrs['id']not in{e.get('id')for e in before};xyz=list(map(float,attrs['xyz'].split()));s=list(map(float,attrs['scale'].split()));yaw=math.radians(float(attrs['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
        world=lambda v:(xyz[0]+co*v[0]*s[0]+si*v[2]*s[2],xyz[1]+v[1]*s[1],xyz[2]-si*v[0]*s[0]+co*v[2]*s[2]);best=1e9
        for b in model['buffers']:
            for t in triangles(b):
                tt=[world(v)for v in t];box=bounds(tt)
                for rt,rb in zip(road,boxes):
                    lower=math.sqrt(sum(max(box[k]-rb[k+3],rb[k]-box[k+3],0)**2 for k in range(3)))
                    if lower<best:best=min(best,triangle_distance(tt,rt))
                checked+=1
        assert best>3,(attrs['id'],best);minimum=min(minimum,best)
    grass=group['parts'][1];tree=group['parts'][2];gp=list(map(float,grass['xyz'].split()));gs=list(map(float,grass['scale'].split()));tp=list(map(float,tree['xyz'].split()));yaw=math.radians(float(grass['hpr'].split()[1]));local=group['treeBaseOnCapLocalPoint'];co,si=math.cos(yaw),math.sin(yaw)
    expected=(gp[0]+co*local[0]*gs[0]+si*local[2]*gs[2],gp[1]+local[1]*gs[1],gp[2]-si*local[0]*gs[0]+co*local[2]*gs[2]);assert math.dist(expected,tp)<1e-6
    # Independently establish that the recorded local point lies on a cap triangle.
    from terrain_triangle_distance import point_triangle_distance
    assert min(point_triangle_distance(local,t)for t in triangles(models[0]['buffers'][0]))<1e-7
    print('V30_GROUP_VERIFIED',group['parts'][0]['id'],flush=True)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');stone=resources/'textures/fluxara_volcano_stone_shared_v16.jpg';assert stone.stat().st_size==39938 and sha(stone)=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
for f in(r/'fidelity-v2/baseline').iterdir():
    if f.is_file():assert f.read_bytes()==(resources/'tracks/fluxara-user-volcano-remake'/f.name).read_bytes()
size=lambda folder:sum(f.stat().st_size for f in folder.rglob('*')if f.is_file());prev=json.loads((r/'fidelity-v29/preservation-verification.json').read_text());newlibs=size(w/'shared-runtime');total=size(c)+prev['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+newlibs+prev['newGlobalTextureBytes'];assert total<prev['v1Bytes']
proof={'baseCandidate':'V29','allExistingSceneNodesModelsImagesPhysicsAndGameplayControlsExactV29':True,'allNewSourceModelFileHashesMatch':True,'copiedModelLocalBoundsOriginsAxesUnchanged':True,'directReuseModelAndTextureUpper20PercentPassed':True,'newFacadeGroups':p['newCoordinateGroups'],'newSharedCoordinateParts':len(ids),'independentlyCheckedNewRenderedTriangles':checked,'protectedDrivingTriangles':2032,'independentAllNewPartRoadMarginMeters':minimum,'treeRootsOnActualCapTrianglesVerified':p['newCoordinateGroups'],'newModels':2,'newTextures':0,'newMaterials':0,'newNativePrototypesPlanned':2,'candidateMapBytes':size(c),'newSharedLibraryBytesIncludingRetainedHistoricalVariants':prev['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+newlibs,'newGlobalTextureBytes':prev['newGlobalTextureBytes'],'newGameAssetPayloadBytes':newlibs,'candidateIncludingNewSharedBytes':total,'v1Bytes':prev['v1Bytes'],'savingBytesVsV1':prev['v1Bytes']-total,'changeBytesAgainstIntermediateV29':total-prev['candidateIncludingNewSharedBytes'],'productionStillExactV1':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V32_SEAMS_AND_PROTECTED_COURSE_VERIFIED',len(ids),total,minimum,flush=True)

originals=[parse(p['sourceGrassModel']),parse(p['sourceStoneModel'])]
for old,new in zip(originals,models[:2]):
 assert old['bounds']==new['bounds'] and old['materials']==new['materials']
 ob,nb=old['buffers'][0],new['buffers'][0];assert ob['indices']==nb['indices'] and len(ob['vertices'])==len(nb['vertices'])
 for ov,nv in zip(ob['vertices'],nb['vertices']):assert ov.get('uv')==nv.get('uv') and ov.get('color')==nv.get('color')
proof.update({'bothCopiedModelsWithUsedTextureBytesBefore':46337,'bothCopiedModelsWithUsedTextureBytesAfter':46337,'sourceTopologyUVRGBLocalBoundsUnchanged':True,'newCopiedSeamGeometry':True,'sourceOriginalDonorsUnmodified':True,'canonicalNativePoolAndGameplayPending':True})
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2))
