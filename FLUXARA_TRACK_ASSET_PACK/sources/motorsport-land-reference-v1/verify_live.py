from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');d='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';app=repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app';installed=Path(subprocess.check_output(['xcrun','simctl','get_app_container',d,'io.fluxara.drift','app'],text=True).strip());src=repo/'iosApp/FluxaraResources/tracks/fluxara-user-motorsport-land';f=r/'candidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
exceptions=[]
assert {p.name for p in src.iterdir() if p.is_file()}=={p.name for p in f.iterdir() if p.is_file()},'Source contains uncounted extra files'
for p in f.iterdir():
 if not p.is_file():continue
 assert sha(p)==sha(src/p.name),p.name
 for root in [app,installed]:
  q=root/'data/tracks'/src.name/p.name
  if not q.exists():
   matches=[x for x in (root/'data').rglob(p.name) if x.is_file() and sha(x)==sha(p)];assert matches,p.name;exceptions.append({'file':p.name,'sharedMatches':[str(x.relative_to(root)) for x in matches]})
  else:assert sha(q)==sha(p),p.name
shared=json.loads((r/'shared-runtime.json').read_text());names=[q['library'] for q in shared['libraries']]
for n in names:
 for p in (repo/'iosApp/FluxaraResources/library'/n).iterdir():
  if p.is_file():
   assert sha(p)==sha(app/'data/library'/n/p.name)==sha(installed/'data/library'/n/p.name)
appbytes=sum(p.stat().st_size for p in app.rglob('*') if p.is_file());(r/'live-verification.json').write_text(json.dumps({'sourceBuildInstalledTrackExact':True,'newSharedLibrariesExact':names,'deduplicatedAssets':exceptions,'appBytes':appbytes,'scope':'Unpacked Debug iOS Simulator app'},indent=2));print('LIVE_VERIFIED',appbytes)
