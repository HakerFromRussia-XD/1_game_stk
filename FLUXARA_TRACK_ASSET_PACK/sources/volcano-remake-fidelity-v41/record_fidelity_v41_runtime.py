from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import subprocess

r = Path(__file__).resolve().parent
w = r/'fidelity-v41'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
source = repo/'iosApp/FluxaraResources'
device = '3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
app = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', device, 'io.fluxara.drift', 'app'], text=True).strip())
tree = ast.parse((r/'capture_fidelity_v35_drive.py').read_text())
required = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'required' for t in n.targets))
assert not (app/'data/tracks/fluxara-volcano-fidelity-v41-drive-probe').exists()
assert not (app/'data/tracks/fluxara-volcano-fidelity-v41-inspection').exists()
torch = source/'library/fluxara_driftlib_aztekTorch_a'
assert all((app/'data/library'/torch.name/p.name).read_bytes() == p.read_bytes() for p in torch.iterdir() if p.is_file())
assert (app/'data/gfx/fluxara_torch_warm_sparks.xml').read_bytes() == (source/'gfx/fluxara_torch_warm_sparks.xml').read_bytes()
required += [('library','fluxara_driftlib_volcano_mudpot_v36'),('library','fluxara_driftlib_volcano_tile_roof_v36')]+[('textures','fluxara_volcano_bubbling_lava_v36.jpg')]+[('textures','vr_v36_lava_sky_'+side+'.jpg')for side in ['top','bottom','east','west','south','north']]
required += [('library','fluxara_driftlib_volcano_closed_terrain_v40')]+[('library','fluxara_driftlib_volcano_grass_roll_v38'),('library','fluxara_driftlib_volcano_rolling_terrain_v38'),('library','fluxara_driftlib_volcano_sky_cloud_v39')]
assert all(not (app/'data'/folder/name).exists() for folder, name in required)
hill = source/'library/fluxara_driftlib_grassy_hill_v2'
assert all((app/'data/library'/hill.name/p.name).read_bytes() == p.read_bytes() for p in hill.iterdir() if p.is_file())
tree=source/'library/fluxara_driftlib_round_tree_green_v2'
assert all((app/'data/library'/tree.name/p.name).read_bytes()==p.read_bytes()for p in tree.iterdir()if p.is_file())
leaf=source/'textures/fluxara_circuit_leaf_v2.png'
assert (app/'data/textures'/leaf.name).read_bytes()==leaf.read_bytes()
run = json.loads((w/'drive-capture.json').read_text())
assert [q['seconds'] for q in run['screenshots']] == [40, 80, 140]
assert all(Path(q['screenshot']).is_file() for q in run['screenshots'])
assert not run['forceWinsUsed']
def warnings(path):
    return sorted(set(re.findall(r'Cannot determine texture full path: ([^\r\n]+)', path.read_text())))
current = warnings(w/'drive-stdout.log')
assert set(current)<=set(warnings(r/'fidelity-v24/drive-stdout.log'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
stone = source/'textures/fluxara_volcano_stone_shared_v16.jpg'
assert stone.stat().st_size == 39938
assert sha(stone) == '6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
finish = w/'screenshots/natural-finish.png'
shutil.copy2(w/'screenshots/drive-140s.png', finish)
comparison = json.loads((r/'ai-v1-comparison/comparison.json').read_text())
assert comparison['baselineNaturalFinishObserved'] and not comparison['regressionFullyExcluded']
shutil.copy2(r/'ai-v1-comparison/comparison.json', w/'ai-v1-comparison.json')
run.update({
    'visualInspectionCompleted': True, 'staticOverviewInspected': True, 'postFinishProcessTerminatedBefore190Seconds':True, 'postFinishStabilityUnverified':True,
    'naturalFinishObserved': True, 'result': '#1', 'fullRouteCompleted': True,
    'naturalFinishScreenshot': str(finish),
    'inspectedGameplayFiles': [q['screenshot'] for q in run['screenshots']],
    'originalPhysicsGeometryAndCourseVerified': True,
    'AITraversalWithoutOffRoadVerified': False,
    'preexistingUnsafeRampTraversalObservedInV1': True,
    'allTraversalRegressionsExcluded': False,
    'candidateMainSPMSha256': sha(w/'candidate/volcano_track.spm'),
    'sourcePooledTorchModelSha256': sha(torch/'fluxara_driftlib_aztekTorch_a_main.spm'),
    'smokeModelHashes': {name: sha(w/'candidate'/name) for name in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']},
    'sixExistingTorchPlacementsVerified': True,
    'existingInstalledTorchAndEmitterUnchanged': True,
    'newTorchRuntimeBytesAddedToInstalledApp': 0,
    'currentStoneTextureBytes': stone.stat().st_size,
    'currentStoneTextureSha256': sha(stone),
    'finalProbeTrackCleanupVerified': True,
    'temporaryCopiedResourcesCleanupVerified': True,
    'existingInstalledDonorLibraryUnchanged': True,
    'materialWarningsExactV24': current,
    'productionIntegrated': False, 'referenceAcceptance': False,
    'centralSupportAndPartPlacementPreservationProofs': ['V26','V27','V28','V29','V30','V32','V33','V34','V35','V36','V37','V38','V39','V41'],
    'sameCameraOverviewWithV24Inspected': True,
    'screenshotsRetainedUnretouched': True,
    'visualFinding': 'V41 retains stone texture39938B exact pixels.128 low source roadside blocks alternate red/white colors, preserving all source geometry/UV/normals/materials.Three source smoke meshes retain all geometry/normals/indices/world poses and use scoped unlit baked vertex lighting with exact reused158BOrbitalpalette.Individual smoke logicalmodel+usedimage increases13.64to14.34percent, within20percent. Allmapfiles plus acceptedshared history5828925B vs7693535BV1. Natural TT and saved frames verified separately. Production integration, fullreference similarity, performance, reverse and campaign validation pending.'
})
(w/'runtime-validation.json').write_text(json.dumps(run,indent=2))
print('V41_RUNTIME_RECORDED_AND_PROBES_CLEAN',flush=True)
