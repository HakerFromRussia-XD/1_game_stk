from pathlib import Path
import json,math,shutil,subprocess,time,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';shots=w/'screenshots/candidate';shots.mkdir(parents=True,exist_ok=True);device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());copied=[];rows=[]
try:
 for src in (r/'new-library').iterdir():
  dst=app/'data/library'/src.name;shutil.copytree(src,dst);copied.append(dst)
 for src in (r/'new-textures').iterdir():
  dst=app/'data/textures'/src.name
  if not dst.exists():shutil.copy2(src,dst);copied.append(dst)
 for key,pos,target in [('gardens',(-200,210,-80),(0,125,-220)),('garden-close',(-263,169,-285),(-332,148,-300)),('overview',(500,410,200),(30,90,-240))]:
  if len(sys.argv)>1 and key not in sys.argv[1:]:continue
  probe=app/'data/tracks'/('fluxara-spell-shared-picture-'+key);shutil.copytree(w/'candidate',probe);E.ElementTree(E.Element('track',name='Spell Lab screenshot',version='7',groups='Fluxara',designer='Fluxara',cutscene='Y',internal='Y',**{'is-during-day':'Y','shadows':'Y'})).write(probe/'track.xml',encoding='unicode');(probe/'scripting.as').unlink(missing_ok=True);scene=E.parse(probe/'scene.xml').getroot()
  for checks in scene.findall('checks'):scene.remove(checks)
  for o in scene.findall('object'):
   o.attrib.pop('if',None);o.attrib.pop('on-kart-collision',None);o.set('interaction','ghost');o.set('type','animation')
  dx,dz=target[0]-pos[0],target[2]-pos[2];pitch=math.degrees(math.atan2(pos[1]-target[1],math.hypot(dx,dz)))-90;yaw=math.degrees(math.atan2(dx,dz));cam=E.SubElement(scene,'object',id='ScreenshotCamera',type='cutscene_camera',xyz=' '.join(map(str,pos)),hpr=f'{pitch} {yaw} 0',scale='1 1 1',interaction='ghost',model='',**{'skeletal-animation':'false'});curve=E.SubElement(cam,'curve',channel='LocX',interpolation='linear',extend='const')
  for frame in [1,25000]:E.SubElement(curve,'p',c=f'{frame} {pos[0]}')
  E.ElementTree(scene).write(probe/'scene.xml',encoding='unicode')
  try:
   command=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/(key+'-stdout.log')),'--stderr='+str(w/(key+'-stderr.log')),device,bundle,'--no-sound','--cutscene='+probe.name];print(subprocess.check_output(command,text=True),flush=True);time.sleep(6);shot=shots/(key+'.jpg');subprocess.run(['xcrun','simctl','io',device,'screenshot','--type=jpeg',str(shot)],check=True,capture_output=True);rows.append({'view':key,'screenshot':str(shot),'camera':pos,'target':target,'kind':'Static game-engine photograph, not driving test','command':command});print('SPELL_GARDEN_SCREENSHOT_SAVED',key,flush=True)
  finally:subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);shutil.rmtree(probe)
finally:
 for p in copied:
  if p.is_dir():shutil.rmtree(p)
  else:p.unlink()
 if len(sys.argv)>1 and (w/'screenshots.json').exists():
  old=json.loads((w/'screenshots.json').read_text())['screenshots'];rows=[q for q in old if q['view']not in sys.argv[1:]]+rows
 (w/'screenshots.json').write_text(json.dumps({'screenshots':rows,'newDrivingTestPerformed':False,'temporaryProbeResourcesRemoved':True,'existingProductionResourcesPreserved':True,'newBuildPerformed':False},indent=2))
