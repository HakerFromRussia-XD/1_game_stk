from pathlib import Path
import subprocess,time,json,os
r=Path(__file__).resolve().parent
(r/'screenshots').mkdir(exist_ok=True)
d='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(r/'final-campaign-stdout.log'),'--stderr='+str(r/'final-campaign-stderr.log'),d,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track=fluxara-summit-run','--mode=0','--laps=3','--numkarts=1','--kart=fluxara-ace','--fluxara-event=main-normal-ancient-summits','--seed=9']
launch=subprocess.check_output(cmd,text=True);print(launch,flush=True);pid=int(launch.strip().split(':')[-1]);start=time.monotonic();rows=[]
try:
 for t in [12,25,40,60,80,120,160,200,240,280,320,360,400,440]:
  time.sleep(max(0,t-(time.monotonic()-start)));os.kill(pid,0);p=r/'screenshots'/f'final-campaign-{t}s.png';subprocess.run(['xcrun','simctl','io',d,'screenshot',str(p)],capture_output=True,check=True);rows.append({'seconds':t,'path':str(p)});print('CAPTURE',t,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',d,bundle],capture_output=True);(r/'final-campaign-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows},indent=2))
