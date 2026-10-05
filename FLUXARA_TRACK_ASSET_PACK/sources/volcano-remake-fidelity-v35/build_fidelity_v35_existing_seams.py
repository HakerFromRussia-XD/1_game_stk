from pathlib import Path
import collections,hashlib,json,shutil,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v35';w.mkdir(exist_ok=True);c=w/'candidate';assert not (w/'existing-seam-changes.json').exists();shutil.copytree(r/'fidelity-v34/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
models={role:parse(resources/'library'/lib/file)for role,lib,file in [('Stone','fluxara_driftlib_volcano_stone_column_v32','vr_v32_sealed_stone_column.spm'),('Grass','fluxara_driftlib_volcano_grass_cap_v32','vr_v32_sealed_grass_cap.spm')]}
seams=json.loads((r/'fidelity-v32/seam-verification.json').read_text());source=json.loads((r/'fidelity-v32/seam-changes.json').read_text());print('SEAM_SOURCE_KEYS',list(source),flush=True)
# The planar boundary's actual vertex Y is measured from the accepted runtime models.
def boundary(buf):
 def key(i):return tuple(round(x,6)for x in buf['vertices'][i]['position'])
 ed=collections.Counter(tuple(sorted((key(buf['indices'][j+k]),key(buf['indices'][j+(k+1)%3]))))for j in range(0,len(buf['indices']),3)for k in range(3));pts={v for edge,n in ed.items()if n==1 for v in edge};return list({tuple(v['position'])for v in buf['vertices']if tuple(round(x,6)for x in v['position'])in pts})
sb=models['Stone']['buffers'][0];gb=models['Grass']['buffers'][0];si=boundary(sb);gi=boundary(gb);assert len(si)==len(gi)==16
sy={v[1]for v in si};gy={v[1]for v in gi};assert len(sy)==len(gy)==1;stoneY=next(iter(sy));grassY=next(iter(gy))
tree=E.parse(c/'scene.xml');root=tree.getroot();groups=[]
for i in range(58):
 stone=root.find(f'library[@id="VRV16_RoundedTerrain_{i:03d}_Stone"]');grass=root.find(f'library[@id="VRV16_RoundedTerrain_{i:03d}_Grass"]');assert stone is not None and grass is not None
 old=[dict(stone.attrib),dict(grass.attrib)];sp=list(map(float,stone.get('xyz').split()));ss=list(map(float,stone.get('scale').split()));gp=list(map(float,grass.get('xyz').split()));gs=list(map(float,grass.get('scale').split()));top=sp[1]+stoneY*ss[1]
 stone.set('name','fluxara_driftlib_volcano_stone_column_v32');grass.set('name','fluxara_driftlib_volcano_grass_cap_v32');gs[0]=ss[0]*.95;gs[2]=ss[2]*.95;gp[1]=top-.08-grassY*gs[1]
 grass.set('xyz',' '.join(f'{x:.8f}'for x in gp));grass.set('scale',' '.join(f'{x:.8f}'for x in gs))
 groups.append({'partsBefore':old,'partsAfter':[dict(stone.attrib),dict(grass.attrib)],'preservedStoneTopY':top,'boundaryOverlapMeters':.08})
tree.write(c/'scene.xml',encoding='unicode')
for f in(r/'fidelity-v34/candidate').iterdir():
 if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes()
budget=json.loads((r/'fidelity-v34/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());total=size+budget['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+budget['newGlobalTextureBytes'];assert total<budget['v1Bytes']
proof={'baseCandidate':'V34 isolated valley experiment','lastAcceptedCandidate':'V32','groups':groups,'sourceStoneBoundaryY':stoneY,'sourceGrassBoundaryY':grassY,'newSPMOrTextureFiles':0,'existingAcceptedV32ModelsReusedForOld58Groups':True,'allOtherCandidateFilesExactV34':True,'sourceLocalBoundsOriginsAxesPixelsUnchanged':True,'candidateMapBytes':size,'newSharedLibraryBytesIncludingRetainedHistoricalVariants':budget['newSharedLibraryBytesIncludingRetainedHistoricalVariants'],'newGlobalTextureBytes':budget['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':budget['v1Bytes'],'savingBytesVsV1':budget['v1Bytes']-total,'productionIntegrated':False,'referenceAcceptance':False}
(w/'existing-seam-changes.json').write_text(json.dumps(proof,indent=2));print('V35_EXISTING58_SEAMS_PREPARED',total,flush=True)
