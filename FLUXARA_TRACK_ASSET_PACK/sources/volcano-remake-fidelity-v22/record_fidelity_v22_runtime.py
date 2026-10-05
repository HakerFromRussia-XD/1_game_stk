from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import subprocess

r = Path(__file__).resolve().parent
w = r/'fidelity-v22'
repo = Path('/Users/motoricallc/Downloads/fluxara-drift')
source = repo/'iosApp/FluxaraResources'
device = '3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
app = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container', device, 'io.fluxara.drift', 'app'], text=True).strip())
tree = ast.parse((r/'capture_fidelity_v22_drive.py').read_text())
required = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'required' for t in n.targets))
assert not (app/'data/tracks/fluxara-volcano-fidelity-v22-drive-probe').exists()
assert not (app/'data/tracks/fluxara-volcano-fidelity-v22-inspection').exists()
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
assert current == warnings(r/'fidelity-v21/drive-stdout.log')
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
    'sharedCliffModelSha256': sha(source/'library/fluxara_driftlib_volcano_organic_cliff_v22/vr_v22_organic_grass_stone_cliff.spm'),
    'currentStoneTextureBytes': stone.stat().st_size,
    'currentStoneTextureSha256': sha(stone),
    'finalProbeTrackCleanupVerified': True,
    'temporaryCopiedResourcesCleanupVerified': True,
    'existingInstalledDonorLibraryUnchanged': True,
    'materialWarningsExactV21': current,
    'productionIntegrated': False, 'referenceAcceptance': False,
    'visualFinding': 'Wider and shorter copied cliff instances retain source grass vertex colors and stone image pixels/UVs. All four drive frames inspected. At80 the kart is airborne below the elevated ramp edge; at140 it is on the road beneath the arch; at190 natural #1 result is displayed. Unmodified V1 also has unsafe ramp traversal at80 and finishes by190. Single timed comparisons do not exclude every regression or prove identical causes. Large planar near-road terrain, repeated stone walls, castle proportions and lighting remain visually unlike the reference. No retouched images, new application build, performance, reverse or whole-campaign claim.'
})
(w/'runtime-validation.json').write_text(json.dumps(run, indent=2))
print('V22_RUNTIME_RECORDED_AND_PROBES_CLEAN', flush=True)
