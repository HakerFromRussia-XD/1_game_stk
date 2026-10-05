from pathlib import Path
import shutil,json,subprocess,sys
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');dest=repo/'iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake';check=subprocess.run([sys.executable,str(r/'audit.py')],capture_output=True,text=True,check=True);a=json.loads((r/'preservation-audit.json').read_text());assert a['weightNotIncreased'] and a['triangleBudgetPassed']
f=r/'candidate';before={p.name for p in (r/'before').iterdir() if p.is_file()};expected={p.name for p in f.iterdir() if p.is_file()};archive=r/'source-stale-backup';archive.mkdir(exist_ok=True)
for p in dest.iterdir():
 if p.is_file() and p.name not in expected:
  assert p.name in before or p.name.startswith(('vr_','dp_sky_')),p
  shutil.copy2(p,archive/p.name);p.unlink()
for p in f.iterdir():
 if p.is_file():shutil.copy2(p,dest/p.name)
assert {p.name for p in dest.iterdir() if p.is_file()}==expected
print('DRAFT_INTEGRATED',flush=True)
with (r/'build.log').open('w') as log:subprocess.run(['xcodebuild','-project','build-ios-shared-props-simulator/FluxaraDrift.xcodeproj','-scheme','Fluxara Drift','-configuration','Debug','-sdk','iphonesimulator','-destination','id=3B2F19DC-4F76-4F61-9F8D-D5E914A6D123','-jobs','6','CODE_SIGNING_ALLOWED=NO','build'],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
app=repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app';subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True);subprocess.run(['xcrun','simctl','install','3B2F19DC-4F76-4F61-9F8D-D5E914A6D123',str(app)],check=True);print('SIMULATOR_INSTALLED',flush=True)
