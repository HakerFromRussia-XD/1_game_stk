from pathlib import Path
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as E

r=Path(__file__).resolve().parent
work=r/'fidelity-v13'
shots=work/'screenshots'
shots.mkdir(exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
bundle='io.fluxara.drift'
app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip())
probe=app/'data/tracks/fluxara-volcano-fidelity-v13-drive-probe'
shared=app/'data/library/fluxara_driftlib_volcano_castle_tower_v9'
fountain=app/'data/library/fluxara_driftlib_volcano_fountain_v13'
globaltex=app/'data/textures/fluxara_volcano_lava_shared_v13.jpg'
assert not fountain.exists()
assert not globaltex.exists()
assert not shared.exists()
assert not probe.exists()
shutil.copytree(Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_volcano_castle_tower_v9'),shared)
shutil.copytree(Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_volcano_fountain_v13'),fountain)
shutil.copy2(Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/textures/fluxara_volcano_lava_shared_v13.jpg'),globaltex)
shutil.copytree(work/'candidate',probe)
track=E.parse(probe/'track.xml')
track.getroot().set('name','Volcano Remake draft V13')
track.getroot().set('internal','Y')
track.write(probe/'track.xml',encoding='unicode')
cmd=['xcrun','simctl','launch','--terminate-running-process',
     '--stdout='+str(work/'drive-stdout.log'),'--stderr='+str(work/'drive-stderr.log'),
     device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1',
     '--track='+probe.name,'--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4']
rows=[]
try:
    result=subprocess.check_output(cmd,text=True)
    pid=int(result.strip().split(':')[-1])
    start=time.monotonic()
    print(result,flush=True)
    for second in [12,40,80,190,240,360,480]:
        time.sleep(max(0,second-(time.monotonic()-start)))
        os.kill(pid,0)
        shot=shots/f'drive-{second}s.png'
        subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True)
        rows.append({'seconds':second,'screenshot':str(shot)})
        print('DRAFT_CAPTURED',second,shot,flush=True)
except KeyboardInterrupt:
    print('RECORDING_STOPPED_BY_OPERATOR_AFTER_SAVED_EVIDENCE',flush=True)
finally:
    subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
    shutil.rmtree(probe)
    shutil.rmtree(shared)
    shutil.rmtree(fountain)
    globaltex.unlink()
    (work/'drive-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,
        'kind':'Candidate gameplay in a temporary simulator-only track. Production source and final Blender project not yet replaced.',
        'forceWinsUsed':False},indent=2))
