from pathlib import Path
import subprocess,json,shutil,math,time,os,xml.etree.ElementTree as E,sys
from PIL import Image,ImageStat
r=Path(__file__).resolve().parent;shots=r/'screenshots';device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());data=app/'data';source=data/'tracks/fluxara-user-lap-catch'
views=[('section-22', (-202.916259765625, 21.812999725341797, -361.03375244140625), (-228.916259765625, -23.187000274658203, -325.03375244140625)), ('section-53', (608.3825073242188, 58.15750026702881, 478.19500732421875), (582.3825073242188, 13.157500267028809, 514.1950073242188)), ('section-71', (-40.69499969482422, 54.026000022888184, -11.63425064086914), (-66.69499969482422, 9.026000022888184, 24.36574935913086)), ('section-56', (399.06500244140625, 46.0, 660.2657470703125), (373.06500244140625, 1.0, 696.2657470703125)), ('section-70', (-119.64399719238281, 45.20000000298023, 498.9420166015625), (-145.6439971923828, 0.20000000298023224, 534.9420166015625)), ('section-17', (585.31103515625, 49.34625005722046, 67.62249755859375), (559.31103515625, 4.346250057220459, 103.62249755859375)), ('section-2', (-399.3294982910156, 45.20000000298023, 428.87774658203125), (-425.3294982910156, 0.20000000298023224, 464.87774658203125)), ('section-54', (-461.3280029296875, 40.23799991607666, -6.360498428344727), (-487.3280029296875, -4.76200008392334, 29.639501571655273)), ('section-62', (233.1437530517578, 45.00550000043586, -250.26925659179688), (207.1437530517578, 0.005500000435858965, -214.26925659179688)), ('section-68', (96.23324584960938, 45.150000005960464, 270.25), (70.23324584960938, 0.15000000596046448, 306.25)), ('section-52', (-348.42974853515625, 53.51350021362305, 218.70074462890625), (-374.42974853515625, 8.513500213623047, 254.70074462890625)), ('preview-castle', (-126, 54, -228), (-180, 13, -280)), ('preview-castle-wide', (-242, 66, -196), (-180, 10, -280))]
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
(r/'section-captures.json').write_text(json.dumps(rows,indent=2))
