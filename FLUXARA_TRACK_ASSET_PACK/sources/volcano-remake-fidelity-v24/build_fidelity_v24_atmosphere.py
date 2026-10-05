from pathlib import Path
import copy,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v24';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v23/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import point_triangle_distance
helper=(r/'fidelity_v2.py').read_text();ns={'math':math,'struct':struct};exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
scene=E.parse(c/'scene.xml');smoke=[]
for name in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']:
    d=parse(c/name);b=copy.deepcopy(d['buffers'][0]);pose=scene.getroot().find(f'object[@model="{name}"]');scale=list(map(float,pose.get('scale').split()));warm=[]
    for v in b['vertices']:
        n=ns['normal'](v);n=[n[k]/scale[k]for k in range(3)];length=math.sqrt(sum(q*q for q in n));n=[q/length for q in n]
        y=(v['position'][1]-d['bounds'][1])/(d['bounds'][4]-d['bounds'][1])
        heat=min(1,max(0,-n[1])**.65*(.70+.30*(1-y))+.17*(1-y))
        v['color']=tuple(round(a*(1-heat)+b*heat)for a,b in zip((112,108,125),(232,134,70)))
        v.pop('uv',None);warm.append(heat)
    raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*d['bounds'])+struct.pack('<H',1)+b'\0\0'+struct.pack('<HH',1,1));raw+=ns['encode_buffer'](b,[['','']]);(c/name).write_bytes(raw)
    original=r/'fidelity-v2/baseline'/name;palette=c/d['materials'][0][0];oldweight=original.stat().st_size+palette.stat().st_size;assert len(raw)<=oldweight*1.2
    smoke.append({'model':name,'sourceModel':str(r/'fidelity-v23/candidate'/name),'sourcePoolObjectId':'volcano-fidelity-v19-cloud-'+Path(name).stem.lower(),'sourceBounds':list(d['bounds']),'vertices':len(b['vertices']),'triangles':len(b['indices'])//3,'originalModelWithTextureBytes':oldweight,'adaptedModelWithTextureBytes':len(raw),'previousV23ModelWithTextureBytes':(r/'fidelity-v23/candidate'/name).stat().st_size+palette.stat().st_size,'modelWithTextureChangePercent':(len(raw)/oldweight-1)*100,'heatMinimum':min(warm),'heatMaximum':max(warm),'geometryNormalsIndicesAndPlacementRetained':True,'originalPaletteFilesRetained':True,'existingVertexColorMaterialReused':True})

torchlib=resources/'library/fluxara_driftlib_aztekTorch_a';torchpack=pack/'models/shared/fluxara_bronze_wall_torch_v1'
for p in torchlib.iterdir():
    if p.is_file():assert p.read_bytes()==(torchpack/p.name).read_bytes(),p
assert (resources/'gfx/fluxara_torch_warm_sparks.xml').read_bytes()==(torchpack/'fluxara_torch_warm_sparks.xml').read_bytes()
torchmodel=torchlib/'fluxara_driftlib_aztekTorch_a_main.spm';td=parse(torchmodel);placements=[]
main=parse(c/'volcano_track.spm')
triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
protected=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in scene.getroot().findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()))
        protected += [[tuple(p[k]*scale[k]+xyz[k]for k in range(3))for p in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
for i,tower in enumerate(scene.getroot().findall('library[@name="fluxara_driftlib_volcano_castle_battlement_v15"]')):
    xyz=list(map(float,tower.get('xyz').split()));scale=list(map(float,tower.get('scale').split()));rad=.23*scale[0]
    size=max(1.05,min(1.65,rad*.26));p=(xyz[0],xyz[1]+1.152*scale[1]+.15-.42*size,xyz[2]-.32*rad)
    # Whole source model bound contains the copied geometry; yaw180 mirrors XZ.
    center=tuple(p[k]+size*((td['bounds'][k]+td['bounds'][k+3])/2)*(1 if k==1 else -1)for k in range(3))
    radius=size*math.sqrt(sum(((td['bounds'][k+3]-td['bounds'][k])/2)**2 for k in range(3)))
    margin=min(point_triangle_distance(center,t)for t in protected)-radius;assert margin>2.,margin
    ident=f'VRV24_BattlementTorch_{i:02d}'
    E.SubElement(scene.getroot(),'library',id=ident,name=torchlib.name,xyz=' '.join(f'{q:.8f}'for q in p),hpr='0 180 0',scale=' '.join(f'{size:.8f}'for k in range(3)))
    placements.append({'id':ident,'towerId':tower.get('id'),'xyz':p,'hpr':[0,180,0],'scale':[size]*3,'wholeModelProtectedRoadSphereMarginMeters':margin,'sourceLibraryUnmodified':True})
assert len(placements)==6
scene.write(c/'scene.xml',encoding='unicode')
proof={'baseCandidate':'V23','smoke':smoke,'newTorchPlacements':placements,'existingTorchLibrary':str(torchlib),'existingTorchPack':str(torchpack),'torchSourceModelSha256':hashlib.sha256(torchmodel.read_bytes()).hexdigest(),'torchPoolObjectId':'shared-bronze-wall-torch-reference-v1','protectedDrivingTriangles':len(protected),'newTextureFiles':0,'newImagePixels':False,'originalStonePixelsAndUVsUnchanged':True,'sourceCourseAndGameplayControlsUnchanged':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'atmosphere-changes.json').write_text(json.dumps(proof,indent=2));print('V24_WARM_SMOKE_AND_SIX_REUSED_TORCHES_READY',[(q['model'],q['adaptedModelWithTextureBytes'])for q in smoke],min(q['wholeModelProtectedRoadSphereMarginMeters']for q in placements),flush=True)
