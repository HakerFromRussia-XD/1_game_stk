from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import subprocess

r = Path(__file__).resolve().parent
w = r/'fidelity-v23'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
source = repo/'iosApp/FluxaraResources'
device = '3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
app = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', device, 'io.fluxara.drift', 'app'], text=True).strip())
tree = ast.parse((r/'capture_fidelity_v23_drive.py').read_text())
required = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'required' for t in n.targets))
assert not (app/'data/tracks/fluxara-volcano-fidelity-v23-drive-probe').exists()
assert not (app/'data/tracks/fluxara-volcano-fidelity-v23-inspection').exists()
assert not (app/'data/tracks/fluxara-volcano-v22-backdrop-comparison').exists()
assert all(not (app/'data'/folder/name).exists() for folder, name in required)
hill = source/'library/fluxara_driftlib_grassy_hill_v2'
assert all((app/'data/library'/hill.name/p.name).read_bytes() == p.read_bytes() for p in hill.iterdir() if p.is_file())
run = json.loads((w/'drive-capture.json').read_text())
assert [q['seconds'] for q in run['screenshots']] == [40, 80, 140, 190]
assert all(Path(q['screenshot']).is_file() for q in run['screenshots'])
assert not run['forceWinsUsed']
def warnings(path):
    return sorted(set(re.findall(r'Cannot determine texture full path: ([^\r\n]+)', path.read_text())))
current = warnings(w/'drive-stdout.log')
assert current == warnings(r/'fidelity-v22/drive-stdout.log')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
stone = source/'textures/fluxara_volcano_stone_shared_v16.jpg'
assert stone.stat().st_size == 39938
assert sha(stone) == '6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
finish = w/'screenshots/natural-finish.png'
shutil.copy2(w/'screenshots/drive-190s.png', finish)
comparison = json.loads((r/'ai-v1-comparison/comparison.json').read_text())
assert comparison['baselineNaturalFinishObserved'] and not comparison['regressionFullyExcluded']
shutil.copy2(r/'ai-v1-comparison/comparison.json', w/'ai-v1-comparison.json')
run.update({
    'visualInspectionCompleted': True, 'staticOverviewInspected': True,
    'naturalFinishObserved': True, 'result': '#1', 'fullRouteCompleted': True,
    'naturalFinishScreenshot': str(finish),
    'inspectedGameplayFiles': [q['screenshot'] for q in run['screenshots']],
    'originalPhysicsGeometryAndCourseVerified': True,
    'AITraversalWithoutOffRoadVerified': False,
    'preexistingUnsafeRampTraversalObservedInV1': True,
    'allTraversalRegressionsExcluded': False,
    'candidateMainSPMSha256': sha(w/'candidate/volcano_track.spm'),
    'sharedBackdropTerrainModelSha256': sha(source/'library/fluxara_driftlib_volcano_backdrop_terrain_v23/vr_v23_rounded_backdrop_terrain.spm'),
    'currentStoneTextureBytes': stone.stat().st_size,
    'currentStoneTextureSha256': sha(stone),
    'finalProbeTrackCleanupVerified': True,
    'temporaryCopiedResourcesCleanupVerified': True,
    'existingInstalledDonorLibraryUnchanged': True,
    'materialWarningsExactV22': current,
    'productionIntegrated': False, 'referenceAcceptance': False,
    'sameCameraBackdropComparisonInspected': True,
    'backdropComparisonFinding': 'Compared V22 and V23 from camera100,175,-100 looking50,5,-500. Former flat green caps now show a curved silhouette and gradual normal shading. Surrounding stone geometry/texture unchanged. V23 diagnostic has black system/UI overlay at left, left unretouched. Overall composition remains far from reference.',
    'visualFinding': 'Two broad distant green caps have raised rounded interiors. Stone image pixels/UVs, narrow roadside strips, original collision and all other source geometry unchanged. All four drive frames inspected: kart on road at40 and80, road below arch at140, natural #1 result at190. Frame140 has a black system/UI overlay at left, retained unretouched. No claim that AI stayed on road between samples; prior V1 ramp issue remains unresolved. Diagnostic views do not prove reference acceptance. Repeated stone walls, castle proportions and lighting still unlike the reference. No retouched images, new app build, performance, reverse or whole-campaign claim.'
})
before=json.loads((r/'backdrop-v22-comparison/smoke-diagnostic-backdrops.json').read_text())
after=json.loads((w/'smoke-diagnostic-backdrops.json').read_text())
assert before['camera']==after['camera'] and before['target']==after['target']
(w/'runtime-validation.json').write_text(json.dumps(run, indent=2))
print('V23_RUNTIME_RECORDED_AND_PROBES_CLEAN', flush=True)
