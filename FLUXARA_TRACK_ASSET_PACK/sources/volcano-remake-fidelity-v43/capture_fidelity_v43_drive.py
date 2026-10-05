from pathlib import Path
import json,os,shutil,subprocess,time,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';shots=w/'screenshots/drive';shots.mkdir(parents=True,exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip())
probe=app/'data/tracks/fluxara-volcano-fidelity-v43-probe';assert not probe.exists();copied=[];rows=[]
try:
 for src in (w/'shared-runtime').iterdir():
  dst=app/'data/library'/src.name;assert not dst.exists();shutil.copytree(src,dst);copied.append(dst)
 shutil.copytree(w/'candidate',probe);tree=E.parse(probe/'track.xml');tree.getroot().set('name','Volcano Remake landscape V43');tree.getroot().set('internal','Y');tree.write(probe/'track.xml',encoding='unicode')
 cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/'drive-stdout.log'),'--stderr='+str(w/'drive-stderr.log'),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track='+probe.name,'--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4']
 result=subprocess.check_output(cmd,text=True);pid=int(result.strip().split(':')[-1]);start=time.monotonic();print(result,flush=True)
 for second in [40,80,140]:
  time.sleep(max(0,second-(time.monotonic()-start)));os.kill(pid,0);shot=shots/f'drive-{second}s.png';subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True);rows.append({'seconds':second,'screenshot':str(shot)});print('V43_CAPTURED',second,shot,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
 if probe.exists():shutil.rmtree(probe)
 for path in copied:shutil.rmtree(path)
 (w/'drive-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,'forceWinsUsed':False,'temporaryTrackUsed':True,'newBuildPerformed':False,'temporaryProbeRemoved':not probe.exists(),'existingInstalledLibrariesUntouched':True},indent=2))
