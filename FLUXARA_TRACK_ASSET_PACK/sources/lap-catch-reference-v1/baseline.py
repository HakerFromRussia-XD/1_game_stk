from pathlib import Path
import shutil,json,hashlib,subprocess,time
r=Path(__file__).resolve().parent
src=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-lap-catch')
assert not (r/'before').exists()
shutil.copytree(src,r/'before')
files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in src.iterdir() if p.is_file()}
(r/'baseline.json').write_text(json.dumps({'trackId':src.name,'source':str(src),'originalBytes':sum(q['bytes'] for q in files.values()),'files':files},indent=2))
(r/'screenshots').mkdir(exist_ok=True)
d='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(r/'before-stdout.log'),'--stderr='+str(r/'before-stderr.log'),d,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track=fluxara-user-lap-catch','--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--fluxara-event=main-ghost_geometry-lap-catch','--seed=9']
print(subprocess.check_output(cmd,text=True),flush=True);start=time.monotonic();rows=[]
try:
 for t in [8,25,45,70,100,140,190,250,320,400]:
  time.sleep(max(0,t-(time.monotonic()-start)));p=r/'screenshots'/f'before-{t}s.png';subprocess.run(['xcrun','simctl','io',d,'screenshot',str(p)],capture_output=True,check=True);rows.append({'seconds':t,'path':str(p)});print('CAPTURE',t,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',d,bundle],capture_output=True);(r/'baseline-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows},indent=2))
