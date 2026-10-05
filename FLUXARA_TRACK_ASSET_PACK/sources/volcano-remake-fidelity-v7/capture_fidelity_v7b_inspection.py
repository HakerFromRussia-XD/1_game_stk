from pathlib import Path
import json
import math
import sys
variant=sys.argv[1] if len(sys.argv)>1 else "all"
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as E

r=Path(__file__).resolve().parent
work=r/'fidelity-v7b'
shots=work/'screenshots'
shots.mkdir(exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
bundle='io.fluxara.drift'
app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip())
probe=app/'data/tracks/fluxara-volcano-fidelity-v7b-inspection'
assert not probe.exists()
shutil.copytree(work/'candidate',probe)
if variant=='unlit':
    mt=E.parse(probe/'materials.xml')
    next(e for e in mt.getroot() if e.get('name')=='vr_volcanic_smoke_atlas.png').set('shader','unlit')
    mt.write(probe/'materials.xml',encoding='unicode')
track=E.parse(probe/'track.xml')
track.getroot().set('name','Volcano fidelity inspection')
track.getroot().set('cutscene','Y')
track.getroot().set('internal','Y')
track.write(probe/'track.xml',encoding='unicode')
(probe/'scripting.as').unlink(missing_ok=True)
scene=E.parse(probe/'scene.xml').getroot()
for checks in scene.findall('checks'):scene.remove(checks)
remove={'cards':{'AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm'},'volumes':{'AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm'}}.get(variant,set())
for o in list(scene.findall('object')):
    if o.get('model') in remove:scene.remove(o)
for o in scene.findall('object'):
    o.attrib.pop('if',None)
    o.attrib.pop('on-kart-collision',None)
    o.set('interaction','ghost')
    o.set('type','animation')
pos=(120,130,90)
target=(-42,50,-15)
dx,dz=target[0]-pos[0],target[2]-pos[2]
pitch=math.degrees(math.atan2(pos[1]-target[1],math.hypot(dx,dz)))-90
yaw=math.degrees(math.atan2(dx,dz))
cam=E.SubElement(scene,'object',id='InspectionCamera',type='cutscene_camera',xyz=' '.join(map(str,pos)),hpr=f'{pitch} {yaw} 0',scale='1 1 1',interaction='ghost',model='',**{'skeletal-animation':'false'})
curve=E.SubElement(cam,'curve',channel='LocX',interpolation='linear',extend='const')
for frame in [1,25000]:E.SubElement(curve,'p',c=f'{frame} {pos[0]}')
E.ElementTree(scene).write(probe/'scene.xml',encoding='unicode')
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(work/'probe-stdout.log'),'--stderr='+str(work/'probe-stderr.log'),device,bundle,'--no-sound','--cutscene='+probe.name]
try:
    result=subprocess.check_output(cmd,text=True)
    pid=int(result.strip().split(':')[-1])
    print(result,flush=True)
    time.sleep(18)
    os.kill(pid,0)
    shot=shots/('smoke-diagnostic-'+variant+'.png')
    subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True)
    (work/('smoke-diagnostic-'+variant+'.json')).write_text(json.dumps({'command':cmd,'screenshot':str(shot),'camera':pos,'target':target,'kind':'Candidate static inspection in the game engine; not gameplay validation.'},indent=2))
    print('PROBE_CAPTURED',shot,flush=True)
finally:
    subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
    shutil.rmtree(probe)
