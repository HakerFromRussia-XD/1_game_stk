from pathlib import Path
import subprocess,json,shutil,math,time,os,xml.etree.ElementTree as E,sys
from PIL import Image,ImageStat
r=Path(__file__).resolve().parent;shots=r/'screenshots';device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());data=app/'data';source=data/'tracks/fluxara-user-lap-catch'
views=[('draft-overview',(750,480,-300),(0,20,250)),('draft-hills',(545,62,410),(490,15,465)),('draft-castle',(-128,27,-220),(-180,-5,-280)),('draft-beach',(-230,25,-180),(-195,-15,-275)),('draft-portal',(171,155,286),(176,150,264))]
if len(sys.argv)>1:views=[v for v in views if v[0] in sys.argv[1:]]
rows=[]
for key,pos,target in views:
 probe=data/'tracks'/('fluxara-lap-inspection-'+key);assert not probe.exists();shutil.copytree(source,probe)
 E.ElementTree(E.Element('track',name='Lap Catch inspection',version='7',groups='Fluxara',designer='Fluxara',cutscene='Y',internal='Y',**{'is-during-day':'Y','shadows':'Y'})).write(probe/'track.xml',encoding='unicode')
 (probe/'scripting.as').unlink(missing_ok=True)
 scene=E.parse(probe/'scene.xml').getroot()
 for checks in scene.findall('checks'):scene.remove(checks)
 for o in scene.findall('object'):
  o.attrib.pop('if',None);o.attrib.pop('on-kart-collision',None);o.set('interaction','ghost');o.set('type','animation')
 dx,dz=target[0]-pos[0],target[2]-pos[2];pitch=math.degrees(math.atan2(pos[1]-target[1],math.hypot(dx,dz)))-90;yaw=math.degrees(math.atan2(dx,dz));cam=E.SubElement(scene,'object',id='InspectionCamera',type='cutscene_camera',xyz=' '.join(map(str,pos)),hpr=f'{pitch} {yaw} 0',scale='1 1 1',interaction='ghost',model='',**{'skeletal-animation':'false'});curve=E.SubElement(cam,'curve',channel='LocX',interpolation='linear',extend='const')
 for frame in [1,25000]:E.SubElement(curve,'p',c=f'{frame} {pos[0]}')
 E.ElementTree(scene).write(probe/'scene.xml',encoding='unicode')
 try:
  s=subprocess.check_output(['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(r/(key+'-stdout.log')),'--stderr='+str(r/(key+'-stderr.log')),device,bundle,'--no-sound','--cutscene='+probe.name],text=True);pid=int(s.strip().split(':')[-1]);time.sleep(10);os.kill(pid,0);shot=shots/(key+'.png')
  for attempt in range(16):
   subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],check=True,capture_output=True);im=Image.open(shot).convert('RGB');w,h=im.size;variance=max(ImageStat.Stat(im.crop((w*.15,h*.15,w*.85,h*.85))).stddev)
   if variance>6:break
   time.sleep(2);os.kill(pid,0)
  assert variance>6,('Blank loading frame',key)
  time.sleep(2);subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],check=True,capture_output=True)
  rows.append({'view':key,'camera':pos,'target':target,'screenshot':str(shot),'kind':'in-engine static inspection, production geometry'});print('Captured',key,flush=True)
 finally:subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);shutil.rmtree(probe)
(r/'static-captures.json').write_text(json.dumps(rows,indent=2))
