from pathlib import Path
import json,hashlib,subprocess
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');track='fluxara-user-ski-dash';source=repo/'iosApp/FluxaraResources';app=repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app';installed=Path(subprocess.check_output(['xcrun','simctl','get_app_container','3B2F19DC-4F76-4F61-9F8D-D5E914A6D123','io.fluxara.drift','app'],text=True).strip());a=json.load(open(r/'ski-extraction.json'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for p in (r/'candidate').iterdir():
 if not p.is_file():continue
 assert sha(p)==sha(source/'tracks'/track/p.name)
 for root in [app,installed]:
  f=root/'data/tracks'/track/p.name
  if not f.is_file():f=next((q for q in [root/'data/textures'/p.name,root/'data/textures'/p.name.replace('stk','fluxara_drift'),root/'data/music'/p.name,root/'data/sfx'/p.name] if q.is_file()),None)
  assert f and sha(p)==sha(f),(p,root)
 rows.append({'name':p.name,'sha256':sha(p)})
for q in a['prototypes']:
 src=r/'new-library'/q['library']
 for f in src.iterdir():
  for root in [source,app/'data',installed/'data']:assert sha(f)==sha(root/'library'/q['library']/f.name),(q['library'],f.name,root)
for q in a['textures']:
 for root in [source,app/'data',installed/'data']:assert sha(Path(q['path']))==sha(root/'textures'/q['alias'])
appbytes=sum(p.stat().st_size for p in app.rglob('*') if p.is_file());result={'track':'fluxara-user-ski-dash','trackSourceBuiltInstalledExact':True,'librarySourceBuiltInstalledExact':len(a['prototypes']),'sharedTexturesBuiltInstalledExact':len(a['textures']),'appBytesBefore':294531218,'appBytesAfter':appbytes,'actualAppByteDelta':appbytes-294531218,'appVersion':'Debug iOS Simulator, uncompressed application; not IPA or store download','manifest':rows};(r/'live-verification.json').write_text(json.dumps(result,indent=2));print('LIVE_VERIFIED',appbytes,result['actualAppByteDelta'])
