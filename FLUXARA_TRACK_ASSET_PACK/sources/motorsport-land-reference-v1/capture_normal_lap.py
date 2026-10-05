from pathlib import Path
import subprocess,time,json
r=Path(__file__).resolve().parent
(r/'screenshots').mkdir(exist_ok=True)
d='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(r/'final-normal-lap-stdout.log'),'--stderr='+str(r/'final-normal-lap-stderr.log'),d,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track=fluxara-user-motorsport-land','--mode=0','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4']
print(subprocess.check_output(cmd,text=True),flush=True);start=time.monotonic();rows=[]
try:
 for t in [8,20,35,50,70,95]:
  time.sleep(max(0,t-(time.monotonic()-start)));p=r/'screenshots'/f'final-normal-lap-{t}s.png';subprocess.run(['xcrun','simctl','io',d,'screenshot',str(p)],capture_output=True,check=True);rows.append({'seconds':t,'path':str(p)});print('CAPTURE',t,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',d,bundle],capture_output=True);(r/'final-normal-lap-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows},indent=2))
