from pathlib import Path
import json,os,subprocess,time
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';assert json.loads((w/'integration-verification.json').read_text())['installedSimulatorResourceFilesMatchSource'];shots=w/'screenshots/integrated';shots.mkdir(exist_ok=True);device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/'integrated-stdout.log'),'--stderr='+str(w/'integrated-stderr.log'),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track=fluxara-user-volcano-remake','--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4'];rows=[]
try:
 result=subprocess.check_output(cmd,text=True);pid=int(result.strip().split(':')[-1]);start=time.monotonic();print(result,flush=True)
 for second in [40,80]:
  time.sleep(max(0,second-(time.monotonic()-start)));os.kill(pid,0);shot=shots/f'drive-{second}s.png';subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True);rows.append({'seconds':second,'screenshot':str(shot)});print('INTEGRATED_CAPTURED',second,shot,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);(w/'integrated-drive-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,'forceWinsUsed':False,'temporaryTrackUsed':False,'newBuildPerformed':False},indent=2))
