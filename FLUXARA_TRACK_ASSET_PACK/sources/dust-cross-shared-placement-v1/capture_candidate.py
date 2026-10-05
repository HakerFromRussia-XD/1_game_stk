from pathlib import Path
import json,os,shutil,subprocess,time,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';shots=w/'screenshots/candidate';shots.mkdir(parents=True,exist_ok=True);assert (w/'preflight.json').is_file()
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());probe=app/'data/tracks/fluxara-dust-shared-probe';assert not probe.exists();copied=[];rows=[]
try:
 for folder,srcroot in [('library',r/'new-library'),('textures',r/'new-textures')]:
  for src in srcroot.iterdir():
   dst=app/'data'/folder/src.name
   if dst.exists():
    assert src.is_file()and dst.read_bytes()==src.read_bytes();continue
   if src.is_dir():shutil.copytree(src,dst)
   else:shutil.copy2(src,dst)
   copied.append(dst)
 shutil.copytree(r/'candidate',probe);shutil.copy2(w/'scene.xml',probe/'scene.xml');tree=E.parse(probe/'track.xml');tree.getroot().set('internal','Y');tree.getroot().set('name','Dust Cross shared scenery draft');tree.write(probe/'track.xml',encoding='unicode')
 cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/'candidate-stdout.log'),'--stderr='+str(w/'candidate-stderr.log'),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track='+probe.name,'--mode=2','--time-limit=60','--capture-limit=999','--numkarts=6','--kart=fluxara-ace','--seed=9'];result=subprocess.check_output(cmd,text=True);pid=int(result.strip().split(':')[-1]);start=time.monotonic();print(result,flush=True)
 for second in [20,45,85]:
  time.sleep(max(0,second-(time.monotonic()-start)));os.kill(pid,0);shot=shots/f'game-{second}s.png';subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True);rows.append({'seconds':second,'screenshot':str(shot)});print('DUST_CANDIDATE_CAPTURED',second,flush=True)
finally:
 subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
 if probe.exists():shutil.rmtree(probe)
 for x in copied:
  if x.is_dir():shutil.rmtree(x)
  else:x.unlink()
 (w/'candidate-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,'temporaryProbeRemoved':not probe.exists(),'copiedResourcesRemoved':all(not p.exists()for p in copied),'existingInstalledResourcesPreserved':True,'forceWinsUsed':False,'newBuildPerformed':False},indent=2))
