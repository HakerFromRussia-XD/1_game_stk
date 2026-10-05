from pathlib import Path
import subprocess,time,json,os,hashlib
r=Path(__file__).resolve().parent;(r/'screenshots').mkdir(exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(r/'before-stdout.log'),'--stderr='+str(r/'before-stderr.log'),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track=fluxara-user-volcano-remake','--mode=1','--laps=2','--numkarts=1','--kart=fluxara-ace','--fluxara-event=main-time_trial-volcano-remake','--seed=4']
launch=subprocess.check_output(cmd,text=True);print(launch,flush=True)
pid=int(launch.strip().split(':')[-1]);start=time.monotonic();rows=[]
try:
    for t in [12,25,40,60,80,120,150,180]:
        time.sleep(max(0,t-(time.monotonic()-start)));os.kill(pid,0)
        p=r/'screenshots'/f'before-{t}s.png'
        subprocess.run(['xcrun','simctl','io',device,'screenshot',str(p)],capture_output=True,check=True)
        rows.append({'seconds':t,'path':str(p)});print('CAPTURE',t,flush=True)
finally:
    subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
    (r/'baseline-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,'sourceManifest':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'before').iterdir() if p.is_file()}},indent=2))
