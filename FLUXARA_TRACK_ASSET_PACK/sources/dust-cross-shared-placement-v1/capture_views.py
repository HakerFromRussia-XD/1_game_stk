from pathlib import Path
import json,math,os,shutil,subprocess,time,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';shots=w/'screenshots/views';shots.mkdir(parents=True,exist_ok=True);device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());copied=[];rows=[]
try:
 for folder,root in [('library',r/'new-library'),('textures',r/'new-textures')]:
  for src in root.iterdir():
   dst=app/'data'/folder/src.name;assert not dst.exists()
   if src.is_dir():shutil.copytree(src,dst)
   else:shutil.copy2(src,dst)
   copied.append(dst)
 for key,pos,target in [('overview',(0,90,-135),(0,20,100)),('east-rocks',(50,25,85),(220,50,80))]:
  probe=app/'data/tracks'/('fluxara-dust-shared-view-'+key);assert not probe.exists();shutil.copytree(r/'candidate',probe);shutil.copy2(w/'scene.xml',probe/'scene.xml');E.ElementTree(E.Element('track',name='Dust Cross inspection',version='7',groups='Fluxara',designer='Fluxara',cutscene='Y',internal='Y',**{'is-during-day':'Y','shadows':'Y'})).write(probe/'track.xml',encoding='unicode');scene=E.parse(probe/'scene.xml').getroot();dx,dz=target[0]-pos[0],target[2]-pos[2];pitch=math.degrees(math.atan2(pos[1]-target[1],math.hypot(dx,dz)))-90;yaw=math.degrees(math.atan2(dx,dz));cam=E.SubElement(scene,'object',id='InspectionCamera',type='cutscene_camera',xyz=' '.join(map(str,pos)),hpr=f'{pitch} {yaw} 0',scale='1 1 1',interaction='ghost',model='',**{'skeletal-animation':'false'});curve=E.SubElement(cam,'curve',channel='LocX',interpolation='linear',extend='const')
  for frame in [1,25000]:E.SubElement(curve,'p',c=f'{frame} {pos[0]}')
  E.ElementTree(scene).write(probe/'scene.xml',encoding='unicode')
  try:
   cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/(key+'-stdout.log')),'--stderr='+str(w/(key+'-stderr.log')),device,bundle,'--no-sound','--cutscene='+probe.name];s=subprocess.check_output(cmd,text=True);pid=int(s.strip().split(':')[-1]);print(s,flush=True);time.sleep(10);os.kill(pid,0);shot=shots/(key+'.jpg');subprocess.run(['xcrun','simctl','io',device,'screenshot','--type=jpeg',str(shot)],check=True,capture_output=True);rows.append({'view':key,'camera':pos,'target':target,'screenshot':str(shot),'kind':'Engine inspection, not gameplay'});print('DUST_VIEW_CAPTURED',key,flush=True)
  finally:subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);shutil.rmtree(probe)
finally:
 for f in copied:
  if f.is_dir():shutil.rmtree(f)
  else:f.unlink()
 (w/'view-captures.json').write_text(json.dumps({'views':rows,'temporaryCopiedResourcesRemoved':all(not x.exists()for x in copied)},indent=2))
