from pathlib import Path
import json,math,os,re,shutil,subprocess,time,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';proof=json.loads((w/'boundary-verification.json').read_text());device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());shots=w/'screenshots/boundary';shots.mkdir(parents=True,exist_ok=True);copied=[];results=[]
q=proof['closedSegments'];values=lambda getter:','.join(f'{getter(x):.8f}'for x in q)
script='''float[] px={PX}; float[] pz={PZ}; float[] nx={NX}; float[] nz={NZ}; int test=0; int step=0;
void onStart(){ Utils::logInfo("BOUNDARY_PROBE_START"); Utils::setTimeout("void beginTest()",5.0); }
void beginTest(){ step=0; Kart::teleportExact(0, Vec3(px[test]-nx[test]*4,20,pz[test]-nz[test]*4)); Kart::setVelocity(0,Vec3(0,0,0)); Utils::setTimeout("void drive()",0.8); }
void drive(){ Vec3 p=Kart::getLocation(0); float d=(p.getX()-px[test])*nx[test]+(p.getZ()-pz[test])*nz[test]; Utils::logInfo("BOUNDARY_SAMPLE "+test+" "+step+" "+p.getX()+" "+p.getY()+" "+p.getZ()+" "+d); step++; if(step<60){ Vec3 v=Kart::getVelocity(0); Kart::setVelocity(0,Vec3(nx[test]*20,v.getY(),nz[test]*20)); Utils::setTimeout("void drive()",0.05); }else{ Kart::setVelocity(0,Vec3(0,0,0)); test++; if(test<3)Utils::setTimeout("void beginTest()",0.6); else Utils::logInfo("BOUNDARY_PROBE_DONE"); } }
'''
for a,b in [('PX',values(lambda x:x['midpoint'][0])),('PZ',values(lambda x:x['midpoint'][2])),('NX',values(lambda x:x['outwardNormal'][0])),('NZ',values(lambda x:x['outwardNormal'][2]))]:script=script.replace(a,b)
(w/'boundary-probe-script.as').write_text(script)
try:
 for folder,root in [('library',r/'new-library'),('textures',r/'new-textures')]:
  for src in root.iterdir():
   dst=app/'data'/folder/src.name;assert not dst.exists()
   if src.is_dir():shutil.copytree(src,dst)
   else:shutil.copy2(src,dst)
   copied.append(dst)
 for phase,src in [('before',r/'before'),('closed',w/'candidate')]:
  probe=app/'data/tracks'/('fluxara-dust-boundary-'+phase);assert not probe.exists();shutil.copytree(src,probe);(probe/'scripting.as').write_text(script);tree=E.parse(probe/'track.xml');tree.getroot().set('internal','Y');tree.write(probe/'track.xml',encoding='unicode');log=w/('boundary-'+phase+'-stderr.log');stdout=w/('boundary-'+phase+'-stdout.log')
  try:
   command=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(stdout),'--stderr='+str(log),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track='+probe.name,'--mode=2','--numkarts=2','--kart=fluxara-ace','--seed=9'];s=subprocess.check_output(command,text=True);pid=int(s.strip().split(':')[-1]);print(s,flush=True);start=time.monotonic()
   while time.monotonic()-start<45:
    time.sleep(1);os.kill(pid,0)
    if log.exists()and'BOUNDARY_PROBE_DONE'in log.read_text(errors='replace'):break
   text=log.read_text(errors='replace');assert 'BOUNDARY_PROBE_DONE'in text,text[-3500:]
   samples=[{'test':int(a),'step':int(b),'x':float(x),'y':float(y),'z':float(z),'signedDistanceOutward':float(d)}for a,b,x,y,z,d in re.findall(r'BOUNDARY_SAMPLE (\d+) (\d+) ([-\d.eE+]+) ([-\d.eE+]+) ([-\d.eE+]+) ([-\d.eE+]+)',text)];assert len(samples)==180,len(samples)
   summary=[{'segment':q[i]['segment'],'samples':sum(x['test']==i for x in samples),'maximumOutwardDistance':max(x['signedDistanceOutward']for x in samples if x['test']==i),'minimumY':min(x['y']for x in samples if x['test']==i)}for i in range(3)];subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shots/(phase+'.png'))],check=True,capture_output=True);results.append({'phase':phase,'summary':summary,'samples':samples,'command':command,'testMethod':'Temporary isolated AngelScript probe teleports kart inside each gap, preserves gravity, repeatedly applies 20m/s outward velocity. Bullet resolves collisions; production scene/startpoints/scripts unchanged.'});print('BOUNDARY_CONTACT_PROBE',phase,summary,flush=True)
  finally:subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);shutil.rmtree(probe)
finally:
 for x in copied:
  if x.is_dir():shutil.rmtree(x)
  else:x.unlink()
 (w/'boundary-runtime-probe.json').write_text(json.dumps({'results':results,'temporaryResourcesRemoved':all(not x.exists()for x in copied),'productionScriptAdded':False,'newBuildPerformed':False},indent=2))
assert len(results)==2
assert all(x['maximumOutwardDistance']>1 for x in results[0]['summary']),results[0]['summary']
assert all(x['maximumOutwardDistance']<0 for x in results[1]['summary']),results[1]['summary']
proof['runtimeTestPending']=False;proof['threeFormerGapsReproducedBeforeFix']=True;proof['threeFormerGapsPhysicallyStopKartAfterFix']=True;proof['runtimeContactProbe']=str(w/'boundary-runtime-probe.json');(w/'boundary-verification.json').write_text(json.dumps(proof,indent=2));print('BOUNDARY_BEFORE_AFTER_PHYSICAL_COLLISION_VERIFIED',flush=True)
